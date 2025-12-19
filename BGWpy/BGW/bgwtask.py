"""Base task class for BerkeleyGW calculations.

This module provides the base BGWTask class that combines MPI and I/O
task functionality for BerkeleyGW calculations.
"""

from __future__ import annotations

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
