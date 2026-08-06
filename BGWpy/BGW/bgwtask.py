"""Base task class for BerkeleyGW calculations.

This module provides the base BGWTask class that combines MPI and I/O
task functionality for BerkeleyGW calculations.
"""

from __future__ import annotations

import warnings
from pathlib import Path

from BGWpy.config import flavors
from BGWpy.core import IOTask, MPITask

__all__ = ["BGWTask"]


class BGWTask(MPITask, IOTask):
    """Base class for BerkeleyGW calculations.

    This class combines MPI execution support with I/O-based task
    management, providing a foundation for all BerkeleyGW task types.

    Attributes
    ----------
    _TAG_JOB_COMPLETED : str
        String tag indicating job completion in output file.
    _use_hdf5 : bool
        Whether to use HDF5 file format for I/O.
    _flavor_complex : bool
        Whether to use complex-valued executables.
    """

    _TAG_JOB_COMPLETED: str = "TOTAL"
    _use_hdf5: bool = flavors["use_hdf5"]
    _flavor_complex: bool = flavors["flavor_complex"]

    def get_fname_with_auto_h5(self, fname: str | Path) -> str:
        """
        Convert a file name to the proper extension.
        Issue a warning in case of mismatch.
        """
        name = str(fname)
        name_no_h5 = name.split(".h5")[0]
        name_h5 = name_no_h5 + ".h5"
        if self._use_hdf5:
            if name == name_no_h5:
                # No warning
                pass
            return name_h5
        if name == name_h5:
            warnings.warn(
                "BGWpy is configured without hdf5, but hdf5 file provided. Edit ~/.BGWpyrc",
                stacklevel=2,
            )
        return name_no_h5

    # GA: This is still not enough, because bsemat.h5 is split in two, when not using hdf5.
    @staticmethod
    def h5_wrap(f):
        def g(self, fname: str | Path | None, *args, **kwargs):
            # A missing name must stay missing: converting it would yield 'None.h5'.
            new_fname = fname if not fname else self.get_fname_with_auto_h5(fname)
            return f(self, new_fname, *args, **kwargs)

        return g
