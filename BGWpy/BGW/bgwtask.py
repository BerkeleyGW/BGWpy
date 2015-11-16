from __future__ import print_function
from ..core import MPITask, IOTask

# Public
__all__ = ['BGWTask']

class BGWTask(MPITask, IOTask):
    """Base class for BerkeleyGW calculations."""
    _TAG_JOB_COMPLETED = 'TOTAL:'

