"""Fortran I/O formatting functions for input files.

This module provides classes and functions for generating Fortran-readable
input files, including namelists and cards.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

import numpy as np
from numpy import array

from .writable import Writable

__all__ = ["Card", "Namelist", "fortran_str"]


class Card(list, Writable):
    """A card used in Fortran input files.

    Cards represent sections in Fortran input files with a name, option,
    and list of values.

    Parameters
    ----------
    name : str
        The card name.
    option : str
        The card option.
    quotes : bool, default=True
        Whether to quote string values.
    """

    def __init__(self, name: str, option: str, quotes: bool = True, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.name = name
        self.option = option
        self.quotes = quotes

    def __str__(self) -> str:
        """Return the card as a Fortran-formatted string."""
        lines = [f"{self.name} {self.option}"]
        lines.extend(f"   {fortran_str(val, self.quotes)}" for val in self)
        return "\n".join(lines) + "\n"


class Namelist(OrderedDict, Writable):
    """A namelist used in Fortran input files.

    Namelists are Fortran's way of structuring input data with key-value pairs.

    Parameters
    ----------
    name : str
        The namelist name.
    quotes : bool, default=True
        Whether to quote string values.
    """

    def __init__(self, name: str, *args: Any, quotes: bool = True, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.name = name
        self.update(kwargs)
        self.quotes = quotes

    def __str__(self) -> str:
        """Return the namelist as a Fortran-formatted string."""
        lines = [f"&{self.name}"]
        for key, val in self.items():
            lines.append(f"   {key} = {fortran_str(val, self.quotes)}")
        lines.append("/")
        return "\n".join(lines) + "\n"


def fortran_str(obj: Any, quotes: bool = True) -> str:
    """Convert an object to a Fortran-readable string.

    Parameters
    ----------
    obj : Any
        The object to convert.
    quotes : bool, default=True
        Whether to quote string values.

    Returns
    -------
    str
        Fortran-formatted string representation.
    """
    if isinstance(obj, str):
        return str_str(obj, quotes)
    if isinstance(obj, bool):
        return bool_str(obj)
    if hasattr(obj, "__iter__") and not isinstance(obj, str):
        try:
            return arr_str(array(obj, dtype=np.double))
        except (ValueError, TypeError):
            return " ".join([fortran_str(o, quotes) for o in obj])
    return str(obj)


def str_str(s: str, quotes: bool = True) -> str:
    """Format a string for Fortran input.

    Parameters
    ----------
    s : str
        The string to format.
    quotes : bool, default=True
        Whether to add quotes.

    Returns
    -------
    str
        Formatted string.
    """
    return f"'{s}'" if quotes else str(s)


def arr_str(arr: np.ndarray) -> str:
    """Format a NumPy array for Fortran input.

    Parameters
    ----------
    arr : np.ndarray
        The array to format.

    Returns
    -------
    str
        Space-separated values without brackets.
    """
    # Format each element individually to avoid numpy's column alignment spacing
    return " ".join(str(x) for x in arr.flat)


def bool_str(b: bool) -> str:
    """Format a boolean for Fortran input.

    Parameters
    ----------
    b : bool
        The boolean value.

    Returns
    -------
    str
        '.true.' or '.false.'
    """
    return ".true." if b else ".false."
