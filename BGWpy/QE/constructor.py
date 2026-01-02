from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .pwscfinput import PWscfInput

if TYPE_CHECKING:
    from numpy.typing import ArrayLike
    from pymatgen.core import Structure


def get_scf_input(
    prefix: str,
    pseudo_dir: str,
    pseudos: list[str],
    structure: Structure,
    ecutwfc: float,
    kpts: ArrayLike,
    wtks: ArrayLike,
) -> PWscfInput:
    """Construct a Quantum Espresso scf input.

    Parameters
    ----------
    prefix : str
        Prefix for QE output files.
    pseudo_dir : str
        Directory containing pseudopotential files.
    pseudos : list[str]
        List of pseudopotential filenames.
    structure : Structure
        Pymatgen Structure object.
    ecutwfc : float
        Wavefunction energy cutoff in Ry.
    kpts : ArrayLike
        K-points array, shape (nkpt, 3).
    wtks : ArrayLike
        K-point weights array, shape (nkpt,).

    Returns
    -------
    PWscfInput
        Configured input file object for SCF calculation.
    """
    inp = PWscfInput()

    inp.control.update(
        prefix=prefix,
        pseudo_dir=pseudo_dir,
        calculation="scf",
    )

    inp.electrons.update(
        electron_maxstep=100,
        conv_thr=1.0e-10,
        mixing_mode="plain",
        mixing_beta=0.7,
        mixing_ndim=8,
        diagonalization="david",
        diago_david_ndim=4,
        diago_full_acc=True,
    )

    inp.system["ecutwfc"] = ecutwfc
    # Convert ArrayLike inputs to concrete numpy arrays
    kpts_array = np.asarray(kpts, dtype=np.float64)
    wtks_array = np.asarray(wtks, dtype=np.float64)
    inp.set_kpoints_crystal(kpts_array, wtks_array)
    inp.structure = structure
    inp.pseudos = pseudos

    return inp


def get_bands_input(
    prefix: str,
    pseudo_dir: str,
    pseudos: list[str],
    structure: Structure,
    ecutwfc: float,
    kpts: ArrayLike,
    wtks: ArrayLike,
    nbnd: int | None = None,
) -> PWscfInput:
    """Construct a Quantum Espresso bands input.

    Parameters
    ----------
    prefix : str
        Prefix for QE output files.
    pseudo_dir : str
        Directory containing pseudopotential files.
    pseudos : list[str]
        List of pseudopotential filenames.
    structure : Structure
        Pymatgen Structure object.
    ecutwfc : float
        Wavefunction energy cutoff in Ry.
    kpts : ArrayLike
        K-points array, shape (nkpt, 3).
    wtks : ArrayLike
        K-point weights array, shape (nkpt,).
    nbnd : int | None, optional
        Number of bands to compute. If None, uses QE default.

    Returns
    -------
    PWscfInput
        Configured input file object for bands calculation.
    """
    inp = get_scf_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, kpts, wtks)
    inp.control["calculation"] = "bands"
    if nbnd is not None:
        inp.system["nbnd"] = nbnd
    return inp
