"""Utility functions for BGWpy core operations.

This module provides common utility functions used throughout BGWpy,
including directory management and file operations.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def exec_from_dir(dirname: str | Path) -> Generator[None, None, None]:
    """Context manager to execute code from a different directory.

    This temporarily changes the working directory, executes code in that
    context, then returns to the original directory even if an exception occurs.

    Parameters
    ----------
    dirname : str | Path
        Directory to change to.

    Yields
    ------
    None

    Examples
    --------
    >>> with exec_from_dir('/tmp'):
    ...     # Code here runs in /tmp
    ...     pass
    >>> # Back to original directory
    """
    original = Path.cwd()
    os.chdir(dirname)
    try:
        yield
    finally:
        os.chdir(original)


def last_lines_contain(
    fname: str | Path,
    tag: str,
    nlines: int = 60,
    *,
    encoding: str = "utf-8",
) -> bool:
    """Check if the last n lines of a file contain a specific tag.

    This function is useful for checking completion status of jobs by
    searching for completion tags in log files.

    Parameters
    ----------
    fname : str | Path
        File path to check.
    tag : str
        Tag string to search for.
    nlines : int, default=60
        Number of lines from the end to check.
    encoding : str, default='utf-8'
        File encoding to use.

    Returns
    -------
    bool
        True if tag is found in the last nlines, False otherwise.

    Notes
    -----
    Returns False if the file doesn't exist or has fewer than nlines.

    Examples
    --------
    >>> last_lines_contain('output.log', 'JOB DONE')
    True
    >>> last_lines_contain('output.log', 'ERROR', nlines=100)
    False
    """
    path = Path(fname)

    if not path.exists():
        return False

    try:
        # Read entire file - for most computational logs this is acceptable
        # as they're typically not huge and this is simpler than tail
        content = path.read_text(encoding=encoding)
        lines = content.splitlines()

        # Check last nlines
        check_lines = lines[-nlines:] if len(lines) >= nlines else lines

        return any(tag in line for line in check_lines)

    except (OSError, UnicodeDecodeError):
        return False


def ensure_directory(path: str | Path) -> str:
    """Ensure a directory exists, creating it if necessary.

    Parameters
    ----------
    path : str | Path
        The directory path to ensure exists.

    Returns
    -------
    str
        The directory path as a string.

    Examples
    --------
    >>> ensure_directory('calculations/scf')
    'calculations/scf'
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


def relative_path(
    target: str | Path,
    base: str | Path,
) -> str:
    """Get relative path from base to target.

    This is a convenience wrapper around Path.relative_to that handles
    both absolute and relative paths cleanly.

    Parameters
    ----------
    target : str | Path
        The target path.
    base : str | Path
        The base directory to compute relative to.

    Returns
    -------
    str
        Relative path from base to target.

    Examples
    --------
    >>> relative_path('/home/user/calc/output', '/home/user')
    'calc/output'
    """
    target_path = Path(target).resolve()
    base_path = Path(base).resolve()

    try:
        return str(target_path.relative_to(base_path))
    except ValueError:
        # Paths are not relative to each other, compute via os.path.relpath
        return os.path.relpath(target_path, base_path)
