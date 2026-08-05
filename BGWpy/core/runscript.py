"""Run script generation and management for BGWpy tasks.

This module provides the RunScript class for creating and managing shell
scripts that execute computational tasks, including variable declarations,
file linking, and command execution.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import warnings
from typing import TYPE_CHECKING, Any

from BGWpy.config import default_runscript

from .writable import Writable

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

__all__ = ["RunScript"]

# A flow runs many tasks, so warn about a repaired affinity mask only once.
_warned_cpu_affinity = False


def _widen_cpu_affinity() -> set[int] | None:
    """Lift a single-CPU affinity mask, returning the previous one to restore.

    A child process inherits the caller's CPU affinity, so a driver pinned to
    one CPU would confine every MPI rank it launches to that CPU. Returns None
    when there is nothing to do.
    """
    if not default_runscript.get("fix_cpu_affinity", True):
        return None
    if not hasattr(os, "sched_getaffinity"):
        return None  # Not Linux; no inheritable affinity mask to repair.

    previous = os.sched_getaffinity(0)
    ncpu = os.cpu_count()
    if len(previous) > 1 or not ncpu or ncpu <= 1:
        return None

    try:
        # The kernel intersects this with the cgroup's allowed set, so it
        # restores the allocation rather than escaping it.
        os.sched_setaffinity(0, range(ncpu))
    except OSError:
        return None

    global _warned_cpu_affinity
    if not _warned_cpu_affinity:
        _warned_cpu_affinity = True
        warnings.warn(
            "This process was pinned to a single CPU, which every launched MPI "
            "rank would have inherited; widening the mask for the job. (The usual "
            "cause is OMP_PROC_BIND being set in the environment, which makes a "
            "threaded BLAS bind the process when numpy is imported. Set "
            "OMP_PROC_BIND=false for the Python process to avoid this.)",
            stacklevel=3,
        )
    return previous


class RunScript(Writable):
    """Shell script for task execution.

    A RunScript represents a bash script with distinct sections:
    - First line (shebang)
    - Header (e.g., job scheduler directives)
    - Variable declarations
    - Symbolic links
    - File copies
    - Main execution commands
    - Footer (cleanup commands)

    Attributes
    ----------
    first_line : str
        Script shebang line (e.g., '#!/bin/bash').
    header : list[str]
        Lines executed before variable declarations.
    variables : dict[str, str]
        Environment variables to declare.
    links : list[list[str]]
        Symbolic links as [target, dest] pairs.
    copies : list[list[str]]
        File copies as [source, dest] pairs.
    main : list[str]
        Main execution commands.
    footer : list[str]
        Lines executed after main commands.

    Examples
    --------
    Create a simple run script:

    >>> script = RunScript(
    ...     variables={'NPROC': '4', 'EXECUTABLE': 'pw.x'},
    ...     main=['$MPIRUN -n $NPROC $EXECUTABLE < input > output']
    ... )
    >>> script.write('run.sh')

    Add commands dynamically:

    >>> script = RunScript()
    >>> script['EXECUTABLE'] = 'epsilon.x'
    >>> script.append('$MPIRUN $EXECUTABLE < eps.inp > eps.out')
    """

    def __init__(
        self,
        variables: Mapping[str, str] | None = None,
        links: Iterable[tuple[str, str] | list[str]] | None = None,
        copies: Iterable[tuple[str, str] | list[str]] | None = None,
        main: str | Iterable[str] | None = None,
        *,
        first_line: str | None = None,
        header: str | Iterable[str] | None = None,
        footer: str | Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a run script.

        Parameters
        ----------
        variables : Mapping[str, str] | None, default=None
            Variables to declare. Keys are variable names, values are
            interpreted as strings with automatic quoting.
        links : Iterable[tuple[str, str] | list[str]] | None, default=None
            Symbolic links as (target, dest) pairs.
            Created with: ln -nfs target dest
        copies : Iterable[tuple[str, str] | list[str]] | None, default=None
            File copies as (source, dest) pairs.
            Created with: cp -f source dest
        main : str | Iterable[str] | None, default=None
            Main execution command(s).
        first_line : str | None, default=None
            Script shebang. If None, uses default from config.
        header : str | Iterable[str] | None, default=None
            Header lines (e.g., scheduler directives).
        footer : str | Iterable[str] | None, default=None
            Footer lines (cleanup commands).
        **kwargs
            Additional arguments passed to Writable.__init__.

        Raises
        ------
        ValueError
            If links or copies contain invalid pairs.
        """
        super().__init__(**kwargs)

        # Initialize all sections
        self.first_line: str = first_line or default_runscript.get("first_line", "#!/bin/bash")
        self.header: list[str] = []
        self.variables: dict[str, str] = {}
        self.links: list[list[str]] = []
        self.copies: list[list[str]] = []
        self.main: list[str] = []
        self.footer: list[str] = []

        # Process variables
        if variables is not None:
            self.variables.update(variables)

        # Process links
        if links is not None:
            for link in links:
                if not self._is_valid_pair(link):
                    msg = f"Invalid link pair: {link}. Expected (target, dest) pair."
                    raise ValueError(msg)
                target, dest = link
                self.add_link(target, dest)

        # Process copies
        if copies is not None:
            for copy in copies:
                if not self._is_valid_pair(copy):
                    msg = f"Invalid copy pair: {copy}. Expected (source, dest) pair."
                    raise ValueError(msg)
                source, dest = copy
                self.add_copy(source, dest)

        # Process main commands
        if isinstance(main, str):
            self.main.append(main)
        elif main is not None:
            self.main.extend(main)

        # Process header
        header_value = header or default_runscript.get("header", [])
        if isinstance(header_value, str):
            self.header.append(header_value)
        elif header_value:
            self.header.extend(header_value)

        # Process footer
        footer_value = footer or default_runscript.get("footer", [])
        if isinstance(footer_value, str):
            self.footer.append(footer_value)
        elif footer_value:
            self.footer.extend(footer_value)

    @staticmethod
    def _is_valid_pair(obj: Any) -> bool:
        """Check if an object is a valid two-element pair.

        Parameters
        ----------
        obj : Any
            Object to check.

        Returns
        -------
        bool
            True if obj is a sequence with exactly 2 elements.
        """
        try:
            return len(obj) == 2 and not isinstance(obj, str)
        except TypeError:
            return False

    def append(self, line: str) -> None:
        """Append a command to the main section.

        Parameters
        ----------
        line : str
            Command line to append.

        Examples
        --------
        >>> script.append('echo "Starting calculation"')
        >>> script.append('$MPIRUN $EXECUTABLE < input > output')
        """
        self.main.append(line)

    def extend(self, lines: Iterable[str]) -> None:
        """Append multiple commands to the main section.

        Parameters
        ----------
        lines : Iterable[str]
            Command lines to append.

        Examples
        --------
        >>> script.extend([
        ...     'echo "Starting"',
        ...     '$MPIRUN $EXECUTABLE',
        ...     'echo "Done"'
        ... ])
        """
        self.main.extend(lines)

    def add_link(self, target: str | Path, dest: str | Path) -> None:
        """Add a symbolic link.

        Parameters
        ----------
        target : str | Path
            Link target path.
        dest : str | Path
            Link destination path.

        Notes
        -----
        Creates link with: ln -nfs target dest
        The -n flag prevents dereferencing if dest is a symlink.
        The -f flag forces creation even if dest exists.

        Examples
        --------
        >>> script.add_link('/path/to/pseudo', 'pseudo_dir')
        >>> script.add_link('../data/structure.in', 'input.in')
        """
        self.links.append([str(target), str(dest)])

    def add_copy(self, source: str | Path, dest: str | Path) -> None:
        """Add a file copy.

        Parameters
        ----------
        source : str | Path
            Source file path.
        dest : str | Path
            Destination path.

        Notes
        -----
        Creates copy with: cp -f source dest
        The -f flag forces overwrite if dest exists.

        Examples
        --------
        >>> script.add_copy('template.in', 'calculation.in')
        >>> script.add_copy('/data/wavefunction.h5', 'WFN')
        """
        self.copies.append([str(source), str(dest)])

    def merge(self, other: RunScript) -> None:
        """Merge another RunScript into this one.

        Combines all sections from the other script, executing commands
        sequentially. Assumes both scripts are in the same directory.

        Parameters
        ----------
        other : RunScript
            The script to merge.

        Notes
        -----
        - Variables are updated (later values override)
        - Links and copies are appended
        - A blank line is added before other's main commands
        - Header and footer are NOT merged (only this script's are kept)

        Examples
        --------
        >>> script1 = RunScript(main=['echo "First"'])
        >>> script2 = RunScript(main=['echo "Second"'])
        >>> script1.merge(script2)
        >>> # script1 now contains both commands
        """
        self.variables.update(other.variables)
        self.links.extend(other.links)
        self.copies.extend(other.copies)
        self.main.extend(["", *other.main])  # Blank line separator

    def __setitem__(self, key: str, value: str) -> None:
        """Declare a variable.

        Parameters
        ----------
        key : str
            Variable name.
        value : str
            Variable value (will be quoted in the script).

        Examples
        --------
        >>> script['NPROC'] = '16'
        >>> script['EXECUTABLE'] = 'pw.x'
        """
        self.variables[key] = str(value)

    def __getitem__(self, key: str) -> str:
        """Get a variable value.

        Parameters
        ----------
        key : str
            Variable name.

        Returns
        -------
        str
            Variable value.

        Raises
        ------
        KeyError
            If variable doesn't exist.
        """
        return self.variables[key]

    def __delitem__(self, key: str) -> None:
        """Delete a variable.

        Parameters
        ----------
        key : str
            Variable name to delete.

        Raises
        ------
        KeyError
            If variable doesn't exist.
        """
        del self.variables[key]

    def _quote_value(self, value: str) -> str:
        """Add appropriate quotes around a variable value.

        Parameters
        ----------
        value : str
            The value to quote.

        Returns
        -------
        str
            The quoted value.

        Raises
        ------
        ValueError
            If value contains both single and double quotes.

        Notes
        -----
        Strategy:
        1. Strip existing quotes (one level)
        2. If no quotes in value, use single quotes
        3. If single quotes in value, use double quotes
        4. If double quotes in value, use single quotes
        5. If both quote types, raise error
        """
        # Strip existing quotes (one level)
        for quote in ("'", '"'):
            if value.startswith(quote) and value.endswith(quote):
                value = value[1:-1]
                break

        # Determine appropriate quote style
        has_single = "'" in value
        has_double = '"' in value

        if not has_single and not has_double:
            return f"'{value}'"
        if has_single and not has_double:
            return f'"{value}"'
        if has_double and not has_single:
            return f"'{value}'"
        msg = (
            f"Cannot quote value containing both single and double quotes: {value}\n"
            f"Consider using escaped quotes or adding this as a raw command in main."
        )
        raise ValueError(msg)

    def __str__(self) -> str:
        """Generate the complete script as a string.

        Returns
        -------
        str
            The complete bash script.

        Notes
        -----
        Script structure:
        1. Shebang (first_line)
        2. Blank line
        3. Header lines
        4. Variable declarations
        5. Symbolic links (if any)
        6. File copies (if any)
        7. Main commands
        8. Footer lines
        """
        lines: list[str] = []

        # Shebang
        lines.append(self.first_line)
        lines.append("")

        # Header
        if self.header:
            lines.append("")
            lines.extend(self.header)

        # Variables
        if self.variables:
            for name, value in self.variables.items():
                quoted_value = self._quote_value(value)
                lines.append(f"{name}={quoted_value}")

        # Symbolic links
        if self.links:
            lines.append("")
            for target, dest in self.links:
                # Skip if target and dest are the same
                if target != dest:
                    lines.append(f"ln -nfs {shlex.quote(target)} {shlex.quote(dest)}")

        # File copies
        if self.copies:
            lines.append("")
            for source, dest in self.copies:
                lines.append(f"cp -f {shlex.quote(source)} {shlex.quote(dest)}")

        # Main commands
        if self.main:
            lines.append("")
            lines.extend(self.main)

        # Footer
        if self.footer:
            lines.append("")
            lines.extend(self.footer)

        return "\n".join(lines) + "\n"

    def run(self) -> int:
        """Execute the script with bash.

        Returns
        -------
        int
            The return code from bash execution.

        Raises
        ------
        FileNotFoundError
            If the script file doesn't exist.

        Examples
        --------
        >>> script.write('run.sh')
        >>> returncode = script.run()
        >>> if returncode == 0:
        ...     print("Script executed successfully")
        """
        if self.fname is None:
            msg = "Cannot run script: no filename set"
            raise ValueError(msg)

        previous_affinity = _widen_cpu_affinity()
        try:
            result = subprocess.run(
                ["bash", str(self.fname)],
                capture_output=False,
                check=False,
            )
        finally:
            if previous_affinity is not None:
                os.sched_setaffinity(0, previous_affinity)
        return result.returncode

    def __repr__(self) -> str:
        """Return a string representation of the RunScript.

        Returns
        -------
        str
            String showing key script properties.
        """
        return (
            f"RunScript("
            f"variables={len(self.variables)}, "
            f"links={len(self.links)}, "
            f"copies={len(self.copies)}, "
            f"commands={len(self.main)})"
        )
