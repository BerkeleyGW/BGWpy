"""Abinit integration for BGWpy.

This module provides classes for managing Abinit calculations within BGWpy
workflows, including SCF, band structure, and wavefunction calculations.
"""

from __future__ import annotations

# Core modules
from . import (
    abibgw,
    abidata,
    abinitbgwflow,
    abinitinput,
    abinittask,
    constructor,
    scftask,
    utils,
    variable,
    wfntask,
)
from .abibgw import *
from .abinitbgwflow import *

# Public task classes - import in dependency order
from .scftask import *
from .wfntask import *

__all__ = [
    # Re-export from submodules
    *scftask.__all__,
    *wfntask.__all__,
    *abibgw.__all__,
    *abinitbgwflow.__all__,
    # Core modules
    "abidata",
    "abinitinput",
    "abinittask",
    "constructor",
    "utils",
    "variable",
]
