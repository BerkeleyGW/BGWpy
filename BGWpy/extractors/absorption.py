"""Absorption data extraction from BerkeleyGW output files.

This module provides functions for reading and parsing output files from
the absorption.x program in BerkeleyGW.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = [
    "AbsorptionEigenvaluesEHResult",
    "AbsorptionEigenvaluesNoEHResult",
    "AbsorptionSpectrumResult",
    "extract_absorption_eigenvalues_eh",
    "extract_absorption_eigenvalues_noeh",
    "extract_absorption_spectrum",
]


class AbsorptionSpectrumResult(TypedDict):
    """Result from parsing an absorption spectrum file (absorption_{eh,noeh}.dat).

    Attributes
    ----------
    omega : NDArray[np.float64]
        Photon energies, shape (nomega,), in eV.
    eps2 : NDArray[np.float64]
        Imaginary part of the dielectric function, shape (nomega,).
    eps1 : NDArray[np.float64]
        Real part of the dielectric function, shape (nomega,).
    jdos : NDArray[np.float64]
        Joint density of states, shape (nomega,).
    """

    omega: NDArray[np.float64]
    eps2: NDArray[np.float64]
    eps1: NDArray[np.float64]
    jdos: NDArray[np.float64]


class AbsorptionEigenvaluesEHResult(TypedDict):
    """Result from parsing an eigenvalues file with electron-hole interaction (eigenvalues.dat).

    Attributes
    ----------
    neig : int
        Number of eigenvalues.
    vol : float
        Unit cell volume.
    nspin : int
        Number of spin components.
    nspinor : int
        Number of spinor components.
    eig : NDArray[np.float64]
        Excitation eigenvalues, shape (neig,), in eV.
    abs_dipole_sq : NDArray[np.float64]
        Squared dipole matrix elements, shape (neig,).
    re_dipole : NDArray[np.float64]
        Real part of the dipole matrix elements, shape (neig,).
    im_dipole : NDArray[np.float64]
        Imaginary part of the dipole matrix elements, shape (neig,).
    """

    neig: int
    vol: float
    nspin: int
    nspinor: int
    eig: NDArray[np.float64]
    abs_dipole_sq: NDArray[np.float64]
    re_dipole: NDArray[np.float64]
    im_dipole: NDArray[np.float64]


class AbsorptionEigenvaluesNoEHResult(TypedDict):
    """Result from parsing an eigenvalues file without electron-hole interaction (eigenvalues_noeh.dat).

    Attributes
    ----------
    neig : int
        Number of eigenvalues.
    vol : float
        Unit cell volume.
    nspin : int
        Number of spin components.
    nspinor : int
        Number of spinor components.
    nkpt : int
        Number of k-points.
    ncb : int
        Number of conduction bands.
    nvb : int
        Number of valence bands.
    ik : NDArray[np.int64]
        K-point indices, shape (neig,).
    ic : NDArray[np.int64]
        Conduction band indices, shape (neig,).
    iv : NDArray[np.int64]
        Valence band indices, shape (neig,).
    ispin : NDArray[np.int64]
        Spin indices, shape (neig,).
    ec : NDArray[np.float64]
        Conduction band energies, shape (neig,), in eV.
    ev : NDArray[np.float64]
        Valence band energies, shape (neig,), in eV.
    eig : NDArray[np.float64]
        Transition energies (ec - ev), shape (neig,), in eV.
    abs_dipole_sq : NDArray[np.float64]
        Squared dipole matrix elements, shape (neig,).
    re_dipole : NDArray[np.float64]
        Real part of the dipole matrix elements, shape (neig,).
    im_dipole : NDArray[np.float64]
        Imaginary part of the dipole matrix elements, shape (neig,).
    """

    neig: int
    vol: float
    nspin: int
    nspinor: int
    nkpt: int
    ncb: int
    nvb: int
    ik: NDArray[np.int64]
    ic: NDArray[np.int64]
    iv: NDArray[np.int64]
    ispin: NDArray[np.int64]
    ec: NDArray[np.float64]
    ev: NDArray[np.float64]
    eig: NDArray[np.float64]
    abs_dipole_sq: NDArray[np.float64]
    re_dipole: NDArray[np.float64]
    im_dipole: NDArray[np.float64]


def extract_absorption_spectrum(fname: str | Path) -> AbsorptionSpectrumResult:
    """Extract the absorption spectrum from an absorption.x output file.

    Parses both the electron-hole (absorption_eh.dat) and independent-particle
    (absorption_noeh.dat) spectrum files, which share the same format.

    Parameters
    ----------
    fname : str | Path
        Path to the absorption spectrum file.

    Returns
    -------
    AbsorptionSpectrumResult
        Dictionary containing:
        - omega : NDArray[np.float64], shape (nomega,)
            Photon energies in eV.
        - eps2 : NDArray[np.float64], shape (nomega,)
            Imaginary part of the dielectric function.
        - eps1 : NDArray[np.float64], shape (nomega,)
            Real part of the dielectric function.
        - jdos : NDArray[np.float64], shape (nomega,)
            Joint density of states.
    """
    data = np.loadtxt(fname, comments="#", unpack=True)
    return {
        "omega": data[0],
        "eps2": data[1],
        "eps1": data[2],
        "jdos": data[3],
    }


def extract_absorption_eigenvalues_eh(fname: str | Path) -> AbsorptionEigenvaluesEHResult:
    """Extract eigenvalues from an absorption.x output file with electron-hole interaction.

    Parses the eigenvalues.dat file produced by absorption.x when run with
    electron-hole interaction (BSE calculation).

    Parameters
    ----------
    fname : str | Path
        Path to the eigenvalues.dat file.

    Returns
    -------
    AbsorptionEigenvaluesEHResult
        Dictionary containing:
        - neig : int
            Number of eigenvalues.
        - vol : float
            Unit cell volume.
        - nspin : int
            Number of spin components.
        - nspinor : int
            Number of spinor components.
        - eig : NDArray[np.float64], shape (neig,)
            Excitation eigenvalues in eV.
        - abs_dipole_sq : NDArray[np.float64], shape (neig,)
            Squared dipole matrix elements.
        - re_dipole : NDArray[np.float64], shape (neig,)
            Real part of the dipole matrix elements.
        - im_dipole : NDArray[np.float64], shape (neig,)
            Imaginary part of the dipole matrix elements.
    """
    lines = Path(fname).read_text(encoding="utf-8").splitlines()

    neig = int(lines[0].split("=")[1])
    vol = float(lines[1].split("=")[1])
    spin_vals = lines[2].split("=")[1].split()
    nspin, nspinor = int(spin_vals[0]), int(spin_vals[1])

    data = np.loadtxt(fname, comments="#", ndmin=2, unpack=True)
    return {
        "neig": neig,
        "vol": vol,
        "nspin": nspin,
        "nspinor": nspinor,
        "eig": data[0],
        "abs_dipole_sq": data[1],
        "re_dipole": data[2],
        "im_dipole": data[3],
    }


def extract_absorption_eigenvalues_noeh(fname: str | Path) -> AbsorptionEigenvaluesNoEHResult:
    """Extract eigenvalues from an absorption.x output file without electron-hole interaction.

    Parses the eigenvalues_noeh.dat file produced by absorption.x when run in
    the independent-particle approximation.

    Parameters
    ----------
    fname : str | Path
        Path to the eigenvalues_noeh.dat file.

    Returns
    -------
    AbsorptionEigenvaluesNoEHResult
        Dictionary containing:
        - neig : int
            Number of eigenvalues.
        - vol : float
            Unit cell volume.
        - nspin : int
            Number of spin components.
        - nspinor : int
            Number of spinor components.
        - nkpt : int
            Number of k-points.
        - ncb : int
            Number of conduction bands.
        - nvb : int
            Number of valence bands.
        - ik : NDArray[np.int64], shape (neig,)
            K-point indices.
        - ic : NDArray[np.int64], shape (neig,)
            Conduction band indices.
        - iv : NDArray[np.int64], shape (neig,)
            Valence band indices.
        - ispin : NDArray[np.int64], shape (neig,)
            Spin indices.
        - ec : NDArray[np.float64], shape (neig,)
            Conduction band energies in eV.
        - ev : NDArray[np.float64], shape (neig,)
            Valence band energies in eV.
        - eig : NDArray[np.float64], shape (neig,)
            Transition energies (ec - ev) in eV.
        - abs_dipole_sq : NDArray[np.float64], shape (neig,)
            Squared dipole matrix elements.
        - re_dipole : NDArray[np.float64], shape (neig,)
            Real part of the dipole matrix elements.
        - im_dipole : NDArray[np.float64], shape (neig,)
            Imaginary part of the dipole matrix elements.
    """
    lines = Path(fname).read_text(encoding="utf-8").splitlines()

    neig = int(lines[0].split("=")[1])
    vol = float(lines[1].split("=")[1])
    dim_vals = lines[2].split("=")[1].split()
    nspin, nspinor, nkpt, ncb, nvb = (int(v) for v in dim_vals)

    data = np.loadtxt(fname, comments="#", ndmin=2, unpack=True)
    return {
        "neig": neig,
        "vol": vol,
        "nspin": nspin,
        "nspinor": nspinor,
        "nkpt": nkpt,
        "ncb": ncb,
        "nvb": nvb,
        "ik": data[0].astype(np.int64),
        "ic": data[1].astype(np.int64),
        "iv": data[2].astype(np.int64),
        "ispin": data[3].astype(np.int64),
        "ec": data[4],
        "ev": data[5],
        "eig": data[6],
        "abs_dipole_sq": data[7],
        "re_dipole": data[8],
        "im_dipole": data[9],
    }
