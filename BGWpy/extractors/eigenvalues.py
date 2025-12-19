"""Eigenvalue extraction from DFT output files.

This module provides functions for reading eigenvalues and k-points from
Quantum Espresso save directories.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import xmltodict

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = ["get_eigs_unpol"]


def get_eigs_unpol(savedir: str) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Read the band structure from a QE save directory.

    This function reads the band structure from a Quantum Espresso save
    directory, relying on the data-file.xml. This is for the non
    spin-polarized case.

    Parameters
    ----------
    savedir : str
        Path to the QE .save directory containing data-file.xml.

    Returns
    -------
    kpoints : NDArray[np.float64]
        Array of shape (nkpt, 3) containing k-point coordinates.
    eigenvalues_Ha : NDArray[np.float64]
        Array of shape (nkpt, nbnd) containing eigenvalues in Hartree.

    Raises
    ------
    FileNotFoundError
        If data-file.xml is not found in the save directory.
    KeyError
        If the XML file doesn't have the expected structure.
    """
    savedir_path = Path(savedir)

    with (savedir_path / "data-file.xml").open("rb") as f:
        datafile: dict = xmltodict.parse(f)

    kpoints: list[NDArray[np.float64]] = []
    eigs: list[NDArray[np.float64]] = []

    eigenvalues_dict: dict = datafile["Root"]["EIGENVALUES"]
    for kdict in eigenvalues_dict.values():
        kpt_text: str = kdict["K-POINT_COORDS"]["#text"]
        kpt = np.array(list(map(float, kpt_text.split())), dtype=np.float64)

        eigfname = savedir_path / kdict["DATAFILE"]["@iotk_link"]
        with eigfname.open("rb") as f:
            edict: dict = xmltodict.parse(f)

        eigs_text: str = edict["Root"]["EIGENVALUES"]["#text"]
        eigs_Ha = np.array(list(map(float, eigs_text.split())), dtype=np.float64)

        kpoints.append(kpt)
        eigs.append(eigs_Ha)

    return np.array(kpoints, dtype=np.float64), np.array(eigs, dtype=np.float64)
