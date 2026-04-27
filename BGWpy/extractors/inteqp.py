"""Inteqp data extraction from BerkeleyGW output files.

This module provides functions for reading and parsing output files from
the inteqp.x program in BerkeleyGW.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = ["extract_inteqp_bandstructure", "extract_inteqp_eqp"]


class InteqpResult(TypedDict):
    """Result dictionary from inteqp extraction functions."""

    nspin: int
    nkpt: int
    nband: int
    kpts: NDArray[np.float64]
    ib_min: int
    ib_max: int
    eigs_dft_eV: NDArray[np.float64]
    eigs_gw_eV: NDArray[np.float64]
    delta_eigs_eV: NDArray[np.float64]


def extract_inteqp_bandstructure(fname: str | Path) -> InteqpResult:
    """Extract the data in the 'bandstructure.dat' file produced by inteqp.x.

    Parameters
    ----------
    fname : str | Path
        Path to the bandstructure.dat file.

    Returns
    -------
    InteqpResult
        Dictionary containing:
        - nspin : int
            Number of spin components.
        - nkpt : int
            Number of k-points.
        - nband : int
            Number of bands.
        - kpts : NDArray[np.float64], shape (nkpt, 3)
            K-points in cartesian coordinates.
        - ib_min : int
            Index of minimum band (starting at 1 for the first occupied band).
        - ib_max : int
            Index of maximum band.
        - eigs_dft_eV : NDArray[np.float64], shape (nspin, nkpt, nband)
            DFT eigenvalues, in eV.
        - eigs_gw_eV : NDArray[np.float64], shape (nspin, nkpt, nband)
            GW eigenvalues, in eV.
        - delta_eigs_eV : NDArray[np.float64], shape (nspin, nkpt, nband)
            Difference between GW and DFT eigenvalues, in eV.
    """
    data = np.loadtxt(fname, unpack=True)

    spin = np.array(data[0], dtype=np.int64)
    band = np.array(data[1], dtype=np.int64)
    kpt = np.array(data[2:5,], dtype=np.float64).transpose()
    E_DFT = np.array(data[5], dtype=np.float64)
    E_QP = np.array(data[6], dtype=np.float64)
    DE = np.array(data[7], dtype=np.float64)

    # Find the dimensions
    ndata = len(spin)
    nspin = 1 if spin[0] == spin[-1] else 2

    ib_min = int(np.min(band))
    ib_max = int(np.max(band))
    nband = ib_max - ib_min + 1

    nkpt = len(kpt) // (nspin * nband)

    # Construct data arrays
    eigs_dft_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
    eigs_gw_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
    delta_eigs_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)

    for i in range(ndata):
        ispin = int(spin[i]) - 1
        ikpt = i % nkpt
        iband = int(band[i]) - ib_min

        eigs_dft_eV[ispin, ikpt, iband] = E_DFT[i]
        eigs_gw_eV[ispin, ikpt, iband] = E_QP[i]
        delta_eigs_eV[ispin, ikpt, iband] = DE[i]

    return {
        "nspin": nspin,
        "nkpt": nkpt,
        "nband": nband,
        "kpts": kpt[:nkpt],
        "ib_min": ib_min,
        "ib_max": ib_max,
        "eigs_dft_eV": eigs_dft_eV,
        "eigs_gw_eV": eigs_gw_eV,
        "delta_eigs_eV": delta_eigs_eV,
    }


def extract_inteqp_eqp(fname: str | Path) -> InteqpResult:
    """Extract the data in the 'eqp.dat' file produced by inteqp.x.

    Parameters
    ----------
    fname : str | Path
        Path to the eqp.dat file.

    Returns
    -------
    InteqpResult
        Dictionary containing:
        - nspin : int
            Number of spin components.
        - nkpt : int
            Number of k-points.
        - nband : int
            Number of bands.
        - kpts : NDArray[np.float64], shape (nkpt, 3)
            K-points in cartesian coordinates.
        - ib_min : int
            Index of minimum band (starting at 1 for the first occupied band).
        - ib_max : int
            Index of maximum band.
        - eigs_dft_eV : NDArray[np.float64], shape (nspin, nkpt, nband)
            DFT eigenvalues, in eV.
        - eigs_gw_eV : NDArray[np.float64], shape (nspin, nkpt, nband)
            GW eigenvalues, in eV.
        - delta_eigs_eV : NDArray[np.float64], shape (nspin, nkpt, nband)
            Difference between GW and DFT eigenvalues, in eV.
    """
    all_lines = [
        line for line in Path(fname).read_text(encoding="utf-8").splitlines() if line.strip()
    ]

    if not all_lines:
        msg = f"File is empty or contains no data: {fname}"
        raise ValueError(msg)

    # Determine nstates from the first block header line.
    first_parts = all_lines[0].split()
    nstates = int(first_parts[3])

    # Read spin/band metadata from the first block to determine array dimensions.
    spins: list[int] = []
    bands: list[int] = []
    for i in range(1, nstates + 1):
        parts = all_lines[i].split()
        spins.append(int(parts[0]))
        bands.append(int(parts[1]))

    ib_min = min(bands)
    ib_max = max(bands)
    nspin = max(spins)
    nband = ib_max - ib_min + 1

    # Each k-point block is exactly (nstates + 1) non-empty lines.
    block_size = nstates + 1
    if len(all_lines) % block_size != 0:
        msg = (
            f"Unexpected number of lines in {fname}: "
            f"{len(all_lines)} is not divisible by block size {block_size}"
        )
        raise ValueError(msg)
    nkpt = len(all_lines) // block_size

    kpts = np.zeros((nkpt, 3), dtype=np.float64)
    eigs_dft_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
    eigs_gw_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)

    for ikpt in range(nkpt):
        block_start = ikpt * block_size
        header = all_lines[block_start].split()
        kpts[ikpt, :] = list(map(float, header[:3]))

        for i in range(nstates):
            parts = all_lines[block_start + 1 + i].split()
            ispin = spins[i] - 1
            iband = bands[i] - ib_min
            eigs_dft_eV[ispin, ikpt, iband] = float(parts[2])
            eigs_gw_eV[ispin, ikpt, iband] = float(parts[3])

    delta_eigs_eV = eigs_gw_eV - eigs_dft_eV

    return {
        "nspin": nspin,
        "nkpt": nkpt,
        "nband": nband,
        "kpts": kpts,
        "ib_min": ib_min,
        "ib_max": ib_max,
        "eigs_dft_eV": eigs_dft_eV,
        "eigs_gw_eV": eigs_gw_eV,
        "delta_eigs_eV": delta_eigs_eV,
    }
