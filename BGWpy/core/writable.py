"""Base classes for objects that can be written to files.

This module provides abstract base classes for creating objects that can be
serialized to files, including basic file handling and input file generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


class Writable:
    """Base class for objects that can be written to files.

    This class provides a simple interface for objects that can be converted
    to strings and written to files.

    Attributes
    ----------
    fname : str | None
        The default filename for writing this object.
    """

    def __init__(self, fname: str | Path | None = None) -> None:
        """Initialize a writable object.

        Parameters
        ----------
        fname : str | Path | None
            Optional default filename for writing.
        """
        self.fname = str(Path(fname)) if fname else None

    def write(self, fname: str | Path | None = None) -> None:
        """Write the object to a file.

        Parameters
        ----------
        fname : str | Path | None
            The filename to write to. If None, uses self.fname.

        Raises
        ------
        ValueError
            If no filename is provided and self.fname is None.
        """
        if fname:
            target = Path(fname)
        elif self.fname:
            target = Path(self.fname)
        else:
            msg = "No filename provided for writing"
            raise ValueError(msg)

        target.write_text(str(self), encoding="utf-8")

    def __str__(self) -> str:
        """Return string representation of this object.

        Subclasses should override this method to provide the content
        to be written to file.

        Returns
        -------
        str
            The string representation to write to file.
        """
        return ""


class BasicFile(Writable):
    """A basic file consisting of lines.

    This class represents a simple text file as a list of lines.

    Attributes
    ----------
    lines : list[str]
        The lines of text in this file.
    """

    def __init__(self, fname: str | Path | None = None) -> None:
        """Initialize a basic file.

        Parameters
        ----------
        fname : str | Path | None
            Optional default filename.
        """
        super().__init__(fname)
        self.lines: list[str] = []

    def __str__(self) -> str:
        """Return the file content as a string.

        Returns
        -------
        str
            All lines joined with newlines, with a trailing newline.
        """
        return "\n".join(self.lines) + "\n"


class BasicInputFile(Writable):
    """A basic input file with variables and keywords.

    This class represents an input file with key-value pairs (variables)
    and standalone keywords. Variables are written as "key value" pairs,
    followed by keywords.

    Attributes
    ----------
    variables : dict[str, Any]
        Dictionary of variable names to values.
    keywords : list[str] of keyword lines.
    """

    def __init__(
        self,
        variables: Mapping[str, Any] | None = None,
        keywords: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a basic input file.

        Parameters
        ----------
        variables : Mapping[str, Any] | None
            Initial variables to set. If None, starts empty.
        keywords : Iterable[str] | None
            Initial keywords to add. If None, starts empty.
        **kwargs
            Additional keyword arguments passed to parent Writable class.
            Can include 'fname' for default filename.
        """
        super().__init__(**kwargs)
        self.variables: dict[str, Any] = dict(variables) if variables else {}
        self.keywords: list[str] = list(keywords) if keywords else []

    def __str__(self) -> str:
        """Return the input file content as a string.

        Format is:
        - Each variable as "key value" on a line
        - Each keyword on its own line
        - Trailing newline

        Returns
        -------
        str
            The formatted input file content.
        """
        lines: list[str] = []

        # Add variables
        for key, val in self.variables.items():
            lines.append(f"{key} {val}")

        # Add keywords
        lines.extend(self.keywords)

        return "\n".join(lines) + "\n"

    def append(self, line: str) -> None:
        """Append a keyword line.

        Parameters
        ----------
        line : str
            The keyword line to append.
        """
        self.keywords.append(line)

    def __getitem__(self, key: str) -> Any:
        """Get a variable value by key.

        Parameters
        ----------
        key : str
            The variable name.

        Returns
        -------
        Any
            The value of the variable.

        Raises
        ------
        KeyError
            If the key doesn't exist.
        """
        return self.variables[key]

    def __setitem__(self, key: str, val: Any) -> None:
        """Set a variable value.

        Parameters
        ----------
        key : str
            The variable name.
        val : Any
            The value to set.
        """
        self.variables[key] = val

    def __delitem__(self, key: str) -> None:
        """Delete a variable or keyword.

        First tries to delete from variables, then from keywords.

        Parameters
        ----------
        key : str
            The variable name or keyword to delete.

        Raises
        ------
        KeyError
            If the key is not found in variables or keywords.
        """
        if key in self.variables:
            del self.variables[key]
        elif key in self.keywords:
            self.keywords.remove(key)
        else:
            raise KeyError(key)
