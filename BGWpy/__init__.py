"""BGWpy - A modern Python interface for BerkeleyGW workflows.

BGWpy provides a high-level Python interface for setting up, managing, and
executing BerkeleyGW calculations for many-body perturbation theory (GW-BSE).

Examples
--------
Create a basic workflow:

>>> from BGWpy import Workflow
>>> from BGWpy.QE import QeScfTask
>>> workflow = Workflow(dirname='my_calculation')
>>> scf_task = QeScfTask(dirname='my_calculation/scf', ...)
>>> workflow.add_task(scf_task)
>>> workflow.write()

Quick imports:

>>> from BGWpy import Structure, Workflow, TaskStatus
>>> from BGWpy.BGW import EpsilonTask, SigmaTask, KernelTask
>>> from BGWpy.QE import QeScfTask, QeWfnTask
"""

__version__ = "4.0.0"
__author__ = "Gabriel Antonius"
__license__ = "BSD-3-Clause"

# Core modules
# External dependencies
from pymatgen.core import Structure

from . import BGW, DFT, config, core, scripts

# Submodule imports
from .Abinit import *
from .BGW import *

# Core classes
from .core import TaskStatus, Workflow
from .flows import *
from .QE import *

# Public API
__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    "__license__",
    # Core classes
    "Structure",
    "Workflow",
    "TaskStatus",
    # Submodules
    "BGW",
    "DFT",
    "config",
    "core",
    "scripts",
    # Re-exported from submodules
    *QE.__all__,
    *BGW.__all__,
    *flows.__all__,
    *Abinit.__all__,
]
