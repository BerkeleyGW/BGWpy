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

    ib_min = int(band[0])
    ib_max = int(band[-1])
    nband = ib_max - ib_min + 1

    nkpt: int = 0
    for i, b in enumerate(band):
        if b != ib_min:
            nkpt = i
            break
    else:
        nkpt = len(kpt) // nspin

    # Construct data arrays
    eigs_dft_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
    eigs_gw_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
    delta_eigs_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)

    for i in range(ndata):
        ispin = int(spin[i]) - 1
        ikpt = i % nkpt
        iband = int(band[i]) - 1

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
    with Path(fname).open() as f:
        # Read the first block to compute the dimensions
        line = next(f)
        parts = line.split()
        nstates = int(parts[3])
        spins: list[int] = []
        bands: list[int] = []
        for _ in range(nstates):
            line = next(f)
            parts = line.split()
            spins.append(int(parts[0]))
            bands.append(int(parts[1]))

        ib_min = min(bands)
        ib_max = max(bands)
        nspin = max(spins)
        nband = nstates // nspin

        # Count the remaining lines
        nlines = nstates + 1
        while True:
            try:
                line = next(f)
                nlines += 1
            except StopIteration:
                break

        nkpt = nlines // (nstates + 1)

        kpts = np.zeros((nkpt, 3), dtype=np.float64)
        eigs_dft_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
        eigs_gw_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)

        # Rewind file to start
        f.seek(0)

        for ikpt in range(nkpt):
            line = next(f)
            parts = line.split()

            kpts[ikpt, :] = list(map(float, parts[:3]))

            for i in range(nstates):
                line = next(f)
                parts = line.split()

                ispin = i // nband
                iband = i % nband

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
