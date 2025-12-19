"""DFT flavor detection utilities for BGWpy.

This module provides functions for detecting and validating DFT code flavors.
"""

from __future__ import annotations

from typing import Literal

__all__ = ["check_dft_flavor", "is_dft_flavor_abinit", "is_dft_flavor_espresso"]

DFTFlavor = Literal["abinit", "espresso"]

_ABINIT_ALIASES: tuple[str, ...] = ("abinit", "abi")
_ESPRESSO_ALIASES: tuple[str, ...] = (
    "espresso",
    "qe",
    "quantumespresso",
    "quantum espresso",
    "pwpwscf",
)


def is_dft_flavor_abinit(dft_flavor: str) -> bool:
    """Check if the given flavor string corresponds to Abinit.

    Parameters
    ----------
    dft_flavor : str
        The DFT flavor string to check.

    Returns
    -------
    bool
        True if the flavor corresponds to Abinit.
    """
    flavor = str(dft_flavor).lower().strip()
    return flavor in _ABINIT_ALIASES


def is_dft_flavor_espresso(dft_flavor: str) -> bool:
    """Check if the given flavor string corresponds to Quantum Espresso.

    Parameters
    ----------
    dft_flavor : str
        The DFT flavor string to check.

    Returns
    -------
    bool
        True if the flavor corresponds to Quantum Espresso.
    """
    flavor = str(dft_flavor).lower().strip()
    return flavor in _ESPRESSO_ALIASES


def check_dft_flavor(dft_flavor: str) -> str:
    """Check that dft_flavor is a valid value.

    Parameters
    ----------
    dft_flavor : str
        The DFT flavor string to validate.

    Returns
    -------
    str
        The validated dft_flavor string (unchanged if valid).

    Raises
    ------
    ValueError
        If dft_flavor is not a recognized value.
    """
    allowed_values: tuple[str, str] = ("abinit", "espresso")
    if is_dft_flavor_abinit(dft_flavor) or is_dft_flavor_espresso(dft_flavor):
        return dft_flavor
    msg = f"Allowed values for dft_flavor are: {allowed_values}. Got '{dft_flavor}'."
    raise ValueError(msg)
