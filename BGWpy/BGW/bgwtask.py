from BGWpy.config import flavors
from BGWpy.core import IOTask, MPITask

# Public
__all__ = ["BGWTask"]


class BGWTask(MPITask, IOTask):
    """Base class for BerkeleyGW calculations."""

    _TAG_JOB_COMPLETED = "TOTAL"
    _use_hdf5 = flavors["use_hdf5"]
    _flavor_complex = flavors["flavor_complex"]
