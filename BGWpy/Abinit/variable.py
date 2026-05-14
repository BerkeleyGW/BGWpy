from __future__ import annotations

from pathlib import Path
import string
import warnings
from typing import Any

import numpy as np

from .utils import flatten, is_iter, is_number

__all__ = ["InputVariable", "SpecialInputVariable"]


_SPECIAL_DATASET_INDICES = (":", "+", "?")
_DATASET_INDICES = "".join(list(string.digits) + list(_SPECIAL_DATASET_INDICES))

_INTERNAL_DATASET_INDICES = ("__s", "__i", "__a")
_SPECIAL_CONVERSION = tuple(zip(_INTERNAL_DATASET_INDICES, _SPECIAL_DATASET_INDICES, strict=False))

_UNITS = {
    "bohr": 1.0,
    "angstrom": 1.8897261328856432,
    "hartree": 1.0,
    "Ha": 1.0,
    "eV": 0.03674932539796232,
}


def convert_number(value: Any) -> int | float:
    """
    Converts some object to a number (int or float).
    If the argument is an integer or a float, returns the same object.
    If the argument is a string, tries to convert to an integer,
    then to a float.
    The string '1.0d-03' will be treated the same as '1.0e-03'
    Raises ValueError if conversion fails.
    """

    if isinstance(value, (float, int)):
        return value

    if isinstance(value, str):
        if is_number(value):
            try:
                val = int(value)
            except ValueError:
                val = float(value)
            return val

        # Handle Fortran-style exponential notation
        val = value.replace("d", "e")
        if is_number(val):
            return float(val)

    msg = f"convert_number failed for value: {value}"
    raise ValueError(msg)


class InputVariable:
    """An Abinit input variable."""

    def __init__(self, name: str, value: Any, units: str | None = "", decimals: int = 0) -> None:
        self._name = name
        self.value = value
        self._units = units if units is not None else ""
        self.decimals = decimals

        if is_iter(self.value) and isinstance(self.value[-1], str) and self.value[-1] in _UNITS:
            self.value = list(self.value)
            self._units = self.value.pop(-1)

    def get_value(self) -> Any:
        """Return the value."""
        if self.units:
            return [*list(self.value), self.units]
        return self.value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def basename(self) -> str:
        """Return the name trimmed of any dataset index."""
        basename = self.name
        return basename.rstrip(_DATASET_INDICES)

    @property
    def dataset(self) -> str:
        """Return the dataset index in string form."""
        return self.name.split(self.basename)[-1]

    @property
    def units(self) -> str:
        """Return the units."""
        return self._units

    def __str__(self) -> str:
        """Declaration of the variable in the input file."""

        # GA TODO: This works but it is badly written.
        #           Should at least use abinit 10.6 variable module.

        value = self.value
        if value is None or not str(value):
            return ""

        line = f" {self.name} "
        var = self.name

        # By default, do not impose a number of decimal points
        floatdecimal = self.decimals

        # For some inputs, impose number of decimal points...
        if any(inp in var for inp in ("xred", "xcart", "qpt", "kpt")):
            # TODO Shouldn't do that
            floatdecimal = max(floatdecimal, 10)

        # ...but not for those
        if any(inp in var for inp in ("ngkpt", "kptrlatt", "ngqpt", "ng2qpt")):
            # TODO Shouldn't do that
            floatdecimal = 0

        if isinstance(value, np.ndarray):
            n = 1
            for i in np.shape(value):
                n *= i
            value = np.reshape(value, n)
            value = list(value)

        # values in lists
        if isinstance(value, (list, tuple)):
            # Reshape a list of lists into a single list
            if all(isinstance(v, (list, tuple)) for v in value):
                line += self.format_list2d(value, floatdecimal)

            else:
                # Maximum number of values per line.
                valperline = 3
                if any(inp in var for inp in ["bdgw"]):
                    # TODO Shouldn't do that
                    valperline = 2

                line += self.format_list(value, valperline, floatdecimal)

        elif isinstance(value, (str, Path)):
            line += self.format_str(value)

        # scalar values
        else:
            line += str(value)

        # Add units
        if self.units:
            line += f" {self.units}"

        return line

    def format_scalar(self, val: Any, floatdecimal: int = 0) -> str:
        """
        Format a single numerical value into a string
        with the appropriate number of decimal.
        """
        sval = str(val)
        if sval.lstrip("-").lstrip("+").isdigit() and floatdecimal == 0:
            return sval

        try:
            fval = float(val)
        except (ValueError, TypeError):
            return sval

        if fval == 0 or (abs(fval) > 1e-3 and abs(fval) < 1e4):
            form = "f"
            addlen = 5
        else:
            form = "e"
            addlen = 8

        # Calculate number of decimal places more robustly
        frac_part = abs(fval - int(fval))
        if frac_part > 0:
            frac_str = str(frac_part)
            # Remove "0." prefix if present
            if "." in frac_str:
                ndec = max(len(frac_str.rsplit(".", maxsplit=1)[-1]), floatdecimal)
            else:
                ndec = floatdecimal
        else:
            ndec = floatdecimal
        ndec = min(ndec, 16)

        sval = "{v:>{l}.{p}{f}}".format(v=fval, l=ndec + addlen, p=ndec, f=form)

        return sval.replace("e", "d")

    def format_list2d(self, values: list[Any] | tuple[Any, ...], floatdecimal: int = 0) -> str:
        """Format a list of lists."""

        lvals = flatten(values)

        # Determine the representation
        if all(isinstance(v, int) for v in lvals):
            type_all = int
        else:
            try:
                for v in lvals:
                    float(v)
                type_all = float
            except (ValueError, TypeError):
                type_all = str

        # Determine the format
        width = max(len(str(s)) for s in lvals)
        if type_all is int:
            formatspec = f">{width}d"
        elif type_all is str:
            formatspec = f">{width}"
        else:
            # Number of decimal - calculate more robustly
            maxdec = 0
            for f in lvals:
                frac_part = abs(f - int(f))
                if frac_part > 0:
                    frac_str = str(frac_part)
                    if "." in frac_str:
                        maxdec = max(maxdec, len(frac_str.rsplit(".", maxsplit=1)[-1]))
            ndec = min(max(maxdec, floatdecimal), 16)

            if all(f == 0 or (abs(f) > 1e-3 and abs(f) < 1e4) for f in lvals):
                formatspec = f">{ndec + 5}.{ndec}f"
            else:
                formatspec = f">{ndec + 8}.{ndec}e"

        line = "\n"
        for L in values:
            for val in L:
                line += " {v:{f}}".format(v=val, f=formatspec)
            line += "\n"

        return line.rstrip("\n")

    def format_list(
        self, values: list[Any] | tuple[Any, ...], valperline: int = 3, floatdecimal: int = 0
    ) -> str:
        """
        Format a list of values into a string.
        The result might be spread among several lines.
        """

        line = ""
        if not values:
            return line

        # List of strings
        if isinstance(values[0], (str, Path)):
            return self.format_str(', '.join(values))

        # Format the line declaring the value
        for i, val in enumerate(values):
            line += " " + self.format_scalar(val, floatdecimal)
            if (i + 1) % valperline == 0:
                line += "\n"

        # Add a carriage return in case of several lines
        if "\n" in line.rstrip("\n"):
            line = "\n" + line

        return line.rstrip("\n")

    def format_str(self, sval: str | Path) -> str:
        """
        Format value for declaration as a string.
        """
        if str(sval).startswith('*'):
            return str(sval)
        else:
            return f'"{sval}"'

    @staticmethod
    def string_to_value(sval: str) -> Any:
        """
        Interpret a string variable and attempt to return a value of the
        appropriate type.  If all else fails, return the initial string.
        """

        value = None

        try:
            for part in sval.split():
                if "*" in part:
                    # cases like istwfk *1
                    if part[0] == "*":
                        value = None
                        break

                    # cases like acell 3*3.52
                    n = int(part.split("*")[0])
                    f = convert_number(part.split("*")[1])
                    if value is None:
                        value = []
                    value += n * [f]
                    continue

                # Fractions
                if "/" in part:
                    # FIXME not very smart, but all excetions will be caught.
                    # Do NOT specify a file name with strings like '1/3'.
                    # (why would you do that?)
                    (num, den) = (float(part.split("/")[i]) for i in range(2))
                    converted_part = num / den
                else:
                    converted_part = part

                # Unit
                if converted_part in _UNITS:
                    if value is None:
                        warnings.warn(f"Could not apply the unit token '{part}'.", stacklevel=2)
                    elif isinstance(value, list):
                        value.append(converted_part)
                    else:
                        value = [value, converted_part]

                    # Convert
                    if False:
                        if isinstance(value, list):
                            for i in range(len(value)):
                                value[i] *= _UNITS[converted_part]
                        elif isinstance(value, str):
                            value = None
                            break
                        else:
                            value *= _UNITS[converted_part]

                    continue

                # Convert
                try:
                    val = convert_number(converted_part)
                except (ValueError, TypeError):
                    val = converted_part

                if value is None:
                    value = val
                elif isinstance(value, list):
                    value.append(val)
                else:
                    value = [value, val]
        except (ValueError, TypeError, AttributeError):
            value = None

        if value is None:
            value = sval

        return value

    @classmethod
    def from_str(cls, bigstring: str) -> InputVariable:
        """Return an instance from a string declaration."""
        parts = bigstring.split()

        # Perform checks on the string
        if len(parts) < 2 or (parts[-1] in _UNITS and len(parts) < 3):
            msg = "\n".join(
                [
                    "Unable to initialize variable from string:",
                    bigstring,
                    "not enough tokens.",
                ]
            )
            raise ValueError(msg)
        if not parts[0].isalpha():
            msg = "\n".join(
                [
                    "Unable to initialize variable from string:",
                    bigstring,
                    "no valid variable name found.",
                ]
            )
            raise ValueError(msg)

        # Make the name
        name = parts.pop(0)

        # Make the units
        units = parts.pop(-1) if parts[-1] in _UNITS else None

        value = cls.string_to_value(" ".join(parts))

        return cls(name, value, units)

    @property
    def sorting_name(self) -> str:
        """Name for sorting purposes."""
        letters = string.ascii_letters

        dataset = self.dataset
        for this, that in zip(_DATASET_INDICES, letters, strict=False):
            dataset = dataset.replace(this, that)

        return self.basename + "_" + dataset

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, InputVariable):
            return NotImplemented
        return self.sorting_name > other.sorting_name

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, InputVariable):
            return NotImplemented
        return self.sorting_name < other.sorting_name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InputVariable):
            return NotImplemented
        return self.sorting_name == other.sorting_name

    def __hash__(self) -> int:
        return hash(self.sorting_name)


class SpecialInputVariable(InputVariable):
    """
    An Abinit input variable which can be set by replacing
    the special dataset indices according to
        : --> __s
        + --> __i
        ? --> __a
    hence allowing for pythonic names.
    """

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        name = self.internal_to_declared(name)
        self._name = name

    @property
    def internal_name(self) -> str:
        return self.declared_to_internal(self.name)

    @staticmethod
    def internal_to_declared(name: str) -> str:
        """
        Make the conversion
            __s --> :
            __i --> +
            __a --> ?
        """
        for old, new in _SPECIAL_CONVERSION:
            name = name.replace(old, new)
        return name

    @staticmethod
    def declared_to_internal(name: str) -> str:
        """
        Make the conversion
             : --> __s
             + --> __i
             ? --> __a
        """
        for new, old in _SPECIAL_CONVERSION:
            name = name.replace(old, new)
        return name
