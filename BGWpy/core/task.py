"""Task management for BGWpy workflows.

This module provides the core task abstraction for BGWpy, including base Task
classes and specialized variants for MPI execution and I/O-based tasks.
"""

from __future__ import annotations

import os
import sys
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

from BGWpy.config import default_mpi

from .runscript import RunScript
from .util import ensure_directory, exec_from_dir, last_lines_contain

__all__ = ["IOTask", "MPITask", "Task", "TaskStatus"]


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""

    COMPLETED = "Completed"
    UNSTARTED = "Unstarted"
    UNFINISHED = "Unfinished"
    UNKNOWN = "Unknown"

    @property
    def color_code(self) -> str:
        """Get ANSI color code for this status."""
        colors = {
            TaskStatus.COMPLETED: "\033[92m",  # Green
            TaskStatus.UNSTARTED: "\033[94m",  # Blue
            TaskStatus.UNFINISHED: "\033[91m",  # Red
            TaskStatus.UNKNOWN: "\033[95m",  # Magenta
        }
        return colors[self]

    def __str__(self) -> str:
        """Return the status value as a string."""
        return self.value


class Task:
    """Base class for tasks executed from a single directory.

    A Task represents a computational task that can be written, executed,
    and monitored. Each task operates within its own directory and uses
    a shell script for execution.

    Attributes
    ----------
    dirname : str
        Main directory from which the task is executed.
    runscript : RunScript
        The execution script for this task.
    """

    _TASK_NAME: str = "Task"

    def __init__(
        self,
        dirname: str | Path = "./",
        runscript_fname: str = "run.sh",
        **kwargs: Any,
    ) -> None:
        """Initialize a task.

        Parameters
        ----------
        dirname : str | Path, default="./"
            Main directory from which the scripts are executed.
        runscript_fname : str, default="run.sh"
            Name of the main execution script.
        **kwargs
            Additional keyword arguments, consumed by subclasses.
        """
        self.dirname = str(dirname)
        self.runscript = RunScript()
        self.runscript.fname = runscript_fname

    @property
    def runscript_fname(self) -> str:
        """Get the full path to the runscript."""
        if self.runscript.fname is None:
            msg = "runscript.fname is not set"
            raise ValueError(msg)
        return str(Path(self.dirname) / self.runscript.fname)

    @runscript_fname.setter
    def runscript_fname(self, value: str) -> None:
        """Set the runscript filename (basename only)."""
        if Path(value).parent != Path():
            msg = f"runscript_fname must be a basename, not a path: {value}"
            raise ValueError(msg)
        self.runscript.fname = value

    @property
    def task_name(self) -> str:
        """Get formatted task name for reporting."""
        return f"{self._TASK_NAME:<10} : {self.dirname}"

    def exec_from_dirname(self) -> AbstractContextManager[None]:
        """Get context manager to execute code from task directory.

        Returns
        -------
        AbstractContextManager[None]
            Context manager that changes to task directory.

        Examples
        --------
        >>> with task.exec_from_dirname():
        ...     # Code here runs in task.dirname
        ...     pass
        """
        return exec_from_dir(self.dirname)

    def run(self) -> None:
        """Execute the task's runscript."""
        with self.exec_from_dirname():
            self.runscript.run()

    def write(self) -> None:
        """Write the task to disk.

        Creates the task directory and writes the runscript.
        """
        ensure_directory(self.dirname)

        with self.exec_from_dirname():
            self.runscript.write()

    def update_link(self, target: str | Path | None, dest: str | Path) -> None:
        """Modify or add a symbolic link.

        Parameters
        ----------
        target : str | Path | None
            Target path for the link. If None or empty, the link is removed.
        dest : str | Path
            Destination path (relative to task dirname).

        Notes
        -----
        If dest is already defined in a link, the target is replaced.
        The target will be expressed relative to the dirname.
        """
        dest_str = str(dest)

        if not target:
            self.remove_link(dest_str)
            return

        dest_parent = Path(self.dirname) / Path(dest_str).parent

        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = Path(os.path.abspath(str(target_path)))

        reltarget = Path(os.path.relpath(str(target_path), os.path.abspath(str(dest_parent))))

        # Update existing link or add new one
        for link in self.runscript.links:
            if link[1] == dest_str:
                link[0] = str(reltarget)
                return

        self.runscript.add_link(str(reltarget), dest_str)

    def remove_link(self, dest: str) -> None:
        """Remove a symbolic link by destination name.

        Parameters
        ----------
        dest : str
            The destination path of the link to remove.
        """
        self.runscript.links = [link for link in self.runscript.links if link[1] != dest]

    def update_copy(self, source: str | Path, dest: str | Path) -> None:
        """Modify or add a file to copy.

        Parameters
        ----------
        source : str | Path
            Source file path.
        dest : str | Path
            Destination path (relative to task dirname).

        Notes
        -----
        The source will be expressed relative to the task dirname.
        If dest is already defined, the source is replaced.
        """
        source_path = Path(source)
        if not source_path.is_absolute():
            source_path = Path(os.path.abspath(str(source_path)))

        dest_str = str(dest)
        relsource = Path(os.path.relpath(str(source_path), os.path.abspath(str(self.dirname))))

        # Update existing copy or add new one
        for copy in self.runscript.copies:
            if copy[1] == dest_str:
                copy[0] = str(relsource)
                return

        self.runscript.add_copy(str(relsource), dest_str)

    def get_status(self, **kwargs: Any) -> TaskStatus:
        """Get the current status of the task.

        The base Task class returns UNKNOWN since it has no way to determine
        completion status from generic shell scripts. Subclasses like IOTask
        override this to provide actual status checking based on output files,
        completion tags, etc.

        Parameters
        ----------
        **kwargs
            Additional keyword arguments (subclass-specific).

        Returns
        -------
        TaskStatus
            Current status of the task. Base implementation always returns UNKNOWN.
        """
        # Base Task has no way to determine status - subclasses should override
        # if they can check completion (e.g., IOTask checks output files)
        return TaskStatus.UNKNOWN

    def is_complete(self) -> bool:
        """Check if the task has completed successfully.

        Returns
        -------
        bool
            True if task status is COMPLETED.
        """
        return self.get_status() == TaskStatus.COMPLETED

    def report(
        self,
        file: TextIO | None = None,
        color: bool = True,
        **kwargs: Any,
    ) -> None:
        """Report the task status.

        Parameters
        ----------
        file : TextIO | None, default=None
            Output file stream. If None, uses sys.stdout.
        color : bool, default=True
            Whether to use ANSI color codes. Ignored if file is not None.
        **kwargs
            Additional arguments passed to get_status().

        Examples
        --------
        >>> task.report()
           Task       : ./calculation  -  Status :  Completed
        """
        status = self.get_status(**kwargs)

        # Format status with color if requested
        if file is None and color:
            status_str = f"{status.color_code}{status}\033[0m"
        else:
            status_str = str(status)

        message = f"   {self.task_name:<50}  -  Status :  {status_str}"

        output = file if file is not None else sys.stdout
        print(message, file=output)


class MPITask(Task):
    """Task with MPI execution support.

    This class extends Task to support MPI-based parallel execution,
    managing MPI runner configuration and process distribution.

    Attributes
    ----------
    mpirun : str
        MPI runner command (e.g., 'mpirun', 'mpiexec').
    nproc : int
        Total number of processes.
    nproc_flag : str
        Flag to specify number of processes (e.g., '-n', '-np').
    nproc_per_node : int
        Number of processes per node.
    nproc_per_node_flag : str
        Flag to specify processes per node.
    nodes : int
        Number of compute nodes.
    nodes_flag : str
        Flag to specify number of nodes.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize an MPI task.

        Parameters
        ----------
        *args
            Positional arguments passed to Task.__init__.
        **kwargs
            Keyword arguments. MPI-specific ones are extracted:
            - mpirun : str
            - nproc : int
            - nproc_flag : str
            - nproc_per_node : int
            - nproc_per_node_flag : str
            - nodes : int
            - nodes_flag : str
            - mpirun_n : str (deprecated, for backward compatibility)

            Others are passed to Task.__init__.
        """
        super().__init__(*args, **kwargs)

        # Initialize MPI settings from defaults
        self._mpirun: str = default_mpi.get("mpirun", "mpirun")
        self._nproc: int = default_mpi.get("nproc", 1)
        self._nproc_flag: str = default_mpi.get("nproc_flag", "-n")
        self._nproc_per_node: int = default_mpi.get("nproc_per_node", 1)
        self._nproc_per_node_flag: str = default_mpi.get("nproc_per_node_flag", "--npernode")
        self._nodes: int = default_mpi.get("nodes", 1)
        self._nodes_flag: str = default_mpi.get("nodes_flag", "--nodes")

        # Override with provided values
        mpi_params = {
            "mpirun",
            "nproc",
            "nproc_flag",
            "nproc_per_node",
            "nproc_per_node_flag",
            "nodes",
            "nodes_flag",
        }

        for key in mpi_params:
            if key in kwargs:
                setattr(self, f"_{key}", kwargs[key])

        # Backward compatibility for mpirun_n
        if "mpirun_n" in kwargs:
            self.mpirun_n = kwargs["mpirun_n"]

        # Initialize MPIRUN variable in runscript
        self._declare_mpirun()

    def _declare_mpirun(self) -> None:
        """Update the MPIRUN variable in the runscript."""
        self.runscript["MPIRUN"] = self.mpirun_variable

    @property
    def mpirun_variable(self) -> str:
        """Construct the full MPI run command string.

        Returns
        -------
        str
            Complete MPI command with all flags.

        Examples
        --------
        >>> task.mpirun_variable
        'mpirun -n 4 --npernode 2'
        """
        if not self._mpirun:
            return ""

        parts = [self._mpirun]

        if self._nproc_flag and self._nproc:
            parts.extend([self._nproc_flag, str(self._nproc)])

        if self._nproc_per_node_flag and self._nproc_per_node:
            parts.extend([self._nproc_per_node_flag, str(self._nproc_per_node)])

        if self._nodes_flag and self._nodes:
            parts.extend([self._nodes_flag, str(self._nodes)])

        return " ".join(parts)

    # Properties with setters that update the runscript

    @property
    def mpirun(self) -> str:
        """Get MPI runner command."""
        return self._mpirun

    @mpirun.setter
    def mpirun(self, value: str) -> None:
        """Set MPI runner command and update runscript."""
        self._mpirun = value
        self._declare_mpirun()

    @property
    def nproc(self) -> int:
        """Get number of processes."""
        return self._nproc

    @nproc.setter
    def nproc(self, value: int) -> None:
        """Set number of processes and update runscript."""
        self._nproc = value
        self._declare_mpirun()

    @property
    def nproc_flag(self) -> str:
        """Get process count flag."""
        return self._nproc_flag

    @nproc_flag.setter
    def nproc_flag(self, value: str) -> None:
        """Set process count flag and update runscript."""
        self._nproc_flag = value
        self._declare_mpirun()

    @property
    def nproc_per_node(self) -> int:
        """Get processes per node."""
        return self._nproc_per_node

    @nproc_per_node.setter
    def nproc_per_node(self, value: int) -> None:
        """Set processes per node and update runscript."""
        self._nproc_per_node = value
        self._declare_mpirun()

    @property
    def nproc_per_node_flag(self) -> str:
        """Get processes per node flag."""
        return self._nproc_per_node_flag

    @nproc_per_node_flag.setter
    def nproc_per_node_flag(self, value: str) -> None:
        """Set processes per node flag and update runscript."""
        self._nproc_per_node_flag = value
        self._declare_mpirun()

    @property
    def nodes(self) -> int:
        """Get number of nodes."""
        return self._nodes

    @nodes.setter
    def nodes(self, value: int) -> None:
        """Set number of nodes and update runscript."""
        self._nodes = value
        self._declare_mpirun()

    @property
    def nodes_flag(self) -> str:
        """Get nodes flag."""
        return self._nodes_flag

    @nodes_flag.setter
    def nodes_flag(self, value: str) -> None:
        """Set nodes flag and update runscript."""
        self._nodes_flag = value
        self._declare_mpirun()

    @property
    def mpirun_n(self) -> str:
        """Get deprecated mpirun_n format (for backward compatibility)."""
        return f"{self._mpirun} {self._nproc_flag}"

    @mpirun_n.setter
    def mpirun_n(self, value: str) -> None:
        """Set mpirun and flag from deprecated mpirun_n format."""
        if not value:
            self._nproc_flag = ""
            self._mpirun = ""
            self._declare_mpirun()
            return

        parts = value.split()

        match len(parts):
            case 0:
                self._nproc_flag = ""
                self._mpirun = ""
            case 1:
                self._mpirun = parts[0]
                self._nproc_flag = ""
            case _:
                self._mpirun = parts[0]
                self._nproc_flag = parts[1]

        self._declare_mpirun()


class IOTask(Task):
    """Task with input/output file management.

    This class extends Task to handle tasks that depend on input files
    and produce output files, with completion checking based on output
    file content.

    It does not modify Task's init function because it is designed for multiple-inheritance use.

    Attributes
    ----------
    _input_fname : str
        Name of the input file (basename).
    _output_fname : str
        Name of the output file (basename).
    _TAG_JOB_COMPLETED : str
        String tag indicating job completion in output file.
    """

    _input_fname: str = ""
    _output_fname: str = ""
    _TAG_JOB_COMPLETED: str = "JOB COMPLETED"

    def get_status(self, check_time: bool = False, **kwargs: Any) -> TaskStatus:
        """Get task status by checking input/output files.

        Parameters
        ----------
        check_time : bool, default=False
            If True, consider task unstarted if output is older than input.

        Returns
        -------
        TaskStatus
            Current status based on file existence and content.

        Notes
        -----
        Status logic:
        - UNSTARTED: Input or output file missing
        - UNSTARTED: Output older than input (if check_time=True)
        - COMPLETED: Completion tag found in output
        - UNFINISHED: Output exists but no completion tag
        - UNKNOWN: No completion tag defined
        """
        # Check input file exists
        if self._input_fname and not Path(self.input_fname).exists():
            return TaskStatus.UNSTARTED

        # Check output file exists
        if self._output_fname and not Path(self.output_fname).exists():
            return TaskStatus.UNSTARTED

        # Check file modification times
        if check_time and self._input_fname and self._output_fname:
            input_time = Path(self.input_fname).stat().st_mtime
            output_time = Path(self.output_fname).stat().st_mtime

            if input_time > output_time:
                return TaskStatus.UNSTARTED

        # Check for completion tag
        if not self._TAG_JOB_COMPLETED:
            return TaskStatus.UNKNOWN

        if last_lines_contain(self.output_fname, self._TAG_JOB_COMPLETED):
            return TaskStatus.COMPLETED

        return TaskStatus.UNFINISHED

    @property
    def input_fname(self) -> str:
        """Get full path to input file.

        Returns
        -------
        str
            Full path to the input file.

        """
        basename: str | Path = self._input_fname

        input_obj = getattr(self, "input", None)
        if input_obj is not None and hasattr(input_obj, "fname"):
            basename = input_obj.fname  # type: ignore[assignment]

        if not isinstance(basename, (str, Path)):
            msg = f"basename must be a string or Path, not {type(basename)}"
            raise TypeError(msg)

        # We allow relative paths like "inputs/eps.inp" but forbid absolute paths.
        basename_path = Path(basename)
        if basename_path.is_absolute():
            msg = f"input_fname must be relative, not absolute: {basename}"
            raise ValueError(msg)

        return str(Path(self.dirname) / str(basename_path))

    @input_fname.setter
    def input_fname(self, value: str | Path) -> None:
        """Set input filename (must be basename only).

        Parameters
        ----------
        value : str | Path
            Input filename (basename only, not a full path).

        Raises
        ------
        ValueError
            If value contains path separators.
        """
        path = Path(value)

        # Allow relative paths but forbid absolute paths.
        if path.is_absolute():
            msg = f"input_fname must be relative, not absolute: {value}"
            raise ValueError(msg)

        self._input_fname = str(path)

        input_obj = getattr(self, "input", None)
        if input_obj is not None and hasattr(input_obj, "fname"):
            input_obj.fname = str(path)  # type: ignore[misc]

    @property
    def output_fname(self) -> str:
        """Get full path to output file.

        Returns
        -------
        str
            Full path to the output file.
        """
        return str(Path(self.dirname) / self._output_fname)

    @output_fname.setter
    def output_fname(self, value: str | Path) -> None:
        """Set output filename (must be basename only).

        Parameters
        ----------
        value : str | Path
            Output filename (basename only, not a full path).

        Raises
        ------
        ValueError
            If value contains path separators.
        """
        path = Path(value)

        # Allow relative paths but forbid absolute paths.
        if path.is_absolute():
            msg = f"output_fname must be relative, not absolute: {value}"
            raise ValueError(msg)

        self._output_fname = str(path)
