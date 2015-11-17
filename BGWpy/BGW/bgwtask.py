from __future__ import print_function
from ..config import use_hdf5
from ..core import MPITask, IOTask

# Public
__all__ = ['BGWTask']

class BGWTask(MPITask, IOTask):
    """Base class for BerkeleyGW calculations."""
    _TAG_JOB_COMPLETED = 'TOTAL:'
    _use_hdf5 = use_hdf5

