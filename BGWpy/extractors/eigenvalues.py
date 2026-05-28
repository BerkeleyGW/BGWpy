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

__all__ = ["get_eigs_unpol", "get_eigs_unpol_from_file"]


def get_eigs_unpol_from_file(
    data_file_fname: str | Path,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Read the band structure from a QE XML data file.

    This function reads the band structure using the modern `data-file-schema.xml`
    format for the non spin-polarized case. Legacy IOTK format is not supported.

    Parameters
    ----------
    data_file_fname : str | Path
        Path to the QE XML data file.

    Returns
    -------
    kpoints : NDArray[np.float64]
        Array of shape (nkpt, 3) containing k-point coordinates.
    eigenvalues_Ha : NDArray[np.float64]
        Array of shape (nkpt, nbnd) containing eigenvalues in Hartree.

    Raises
    ------
    KeyError
        If the XML file doesn't have the expected modern qes:espresso structure.
    """
    with Path(data_file_fname).open("rb") as f:
        datafile: dict = xmltodict.parse(f)

    if "qes:espresso" not in datafile:
        msg = f"Legacy IOTK or unrecognized XML format in {data_file_fname}. Only the modern qes:espresso schema is supported."
        raise KeyError(msg)

    kpoints: list[NDArray[np.float64]] = []
    eigs: list[NDArray[np.float64]] = []

    band_structure = datafile["qes:espresso"]["output"]["band_structure"]
    ks_energies = band_structure["ks_energies"]

    # In case there is only one k-point, xmltodict might not put it in a list
    if not isinstance(ks_energies, list):
        ks_energies = [ks_energies]

    for ks in ks_energies:
        kpt_text = ks["k_point"]["#text"] if isinstance(ks["k_point"], dict) else ks["k_point"]
        eigs_text = (
            ks["eigenvalues"]["#text"] if isinstance(ks["eigenvalues"], dict) else ks["eigenvalues"]
        )

        kpt = np.array(list(map(float, kpt_text.split())), dtype=np.float64)
        eigs_Ha = np.array(list(map(float, eigs_text.split())), dtype=np.float64)

        kpoints.append(kpt)
        eigs.append(eigs_Ha)

    return np.array(kpoints, dtype=np.float64), np.array(eigs, dtype=np.float64)


def get_eigs_unpol(savedir: str | Path) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Read the band structure from a QE save directory.

    This function reads the band structure from a Quantum Espresso save
    directory using the modern `data-file-schema.xml` format. This is for the non
    spin-polarized case. Legacy IOTK format is not supported.

    Parameters
    ----------
    savedir : str | Path
        Path to the QE .save directory containing the XML data file.

    Returns
    -------
    kpoints : NDArray[np.float64]
        Array of shape (nkpt, 3) containing k-point coordinates.
    eigenvalues_Ha : NDArray[np.float64]
        Array of shape (nkpt, nbnd) containing eigenvalues in Hartree.

    Raises
    ------
    FileNotFoundError
        If neither data-file-schema.xml nor data-file.xml is found.
    """
    savedir_path = Path(savedir)

    schema_path = savedir_path / "data-file-schema.xml"
    fallback_path = savedir_path / "data-file.xml"

    if schema_path.exists():
        xml_path = schema_path
    elif fallback_path.exists():
        xml_path = fallback_path
    else:
        msg = f"Could not find data-file-schema.xml or data-file.xml in {savedir_path}"
        raise FileNotFoundError(msg)

    return get_eigs_unpol_from_file(str(xml_path))
