"""Absorption task for BSE absorption calculation.

This module provides the AbsorptionTask class for computing the optical
absorption spectrum using BerkeleyGW's absorption.x executable.
"""

from __future__ import annotations

from typing import Any

from .bgwtask import BGWTask
from .inputs import AbsorptionInput

__all__ = ["AbsorptionTask"]


class AbsorptionTask(BGWTask):
    """Absorption spectrum calculation.

    This task computes the optical absorption spectrum using BerkeleyGW's
    absorption.x executable, which solves the Bethe-Salpeter equation.

    Attributes
    ----------
    input : AbsorptionInput
        The absorption input file object.

    Properties
    ----------
    wfn_co_fname : str
        Path to the coarse wavefunction file.
    wfn_fi_fname : str
        Path to the fine wavefunction file.
    wfnq_fi_fname : str
        Path to the q-shifted fine wavefunction file.
    eps0mat_fname : str
        Path to the eps0mat file.
    epsmat_fname : str
        Path to the epsmat file.
    bsemat_fname : str
        Path to the bsemat file.
    bsedmat_fname : str
        Path to the bsedmat file.
    bsexmat_fname : str
        Path to the bsexmat file.
    sigma_fname : str
        Path to the sigma_hp.log file.
    eqp_fname : str
        Path to the eqp file.
    """

    _TASK_NAME: str = "Absorption"
    _input_fname: str = "absorption.inp"
    _output_fname: str = "absorption.out"

    input: AbsorptionInput
    _wfn_co_fname: str
    _wfn_fi_fname: str
    _wfnq_fi_fname: str
    _eps0mat_fname: str
    _epsmat_fname: str
    _bsemat_fname: str
    _bsedmat_fname: str
    _bsexmat_fname: str
    _sigma_fname: str
    _eqp_fname: str

    def __init__(self, dirname: str, **kwargs: Any) -> None:
        """Initialize an absorption task.

        Parameters
        ----------
        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.

        Other Parameters
        ----------------
        nbnd_val_co : int
            Number of valence bands on the coarse grid.
        nbnd_cond_co : int
            Number of conduction bands on the coarse grid.
        nbnd_val_fi : int
            Number of valence bands on the fine grid.
        nbnd_cond_fi : int
            Number of conduction bands on the fine grid.
        wfn_co_fname : str
            Path to the wavefunction file (coarse grid) produced by pw2bgw.
        wfn_fi_fname : str
            Path to the wavefunction file (fine grid) produced by pw2bgw.
        wfnq_fi_fname : str
            Path to the q-shifted wavefunction file (fine grid) produced by pw2bgw.
        eps0mat_fname : str
            Path to the eps0mat file produced by epsilon.
        epsmat_fname : str
            Path to the epsmat file produced by epsilon.
        bsemat_fname : str, optional
            Path to the bsemat file produced by kernel. If not provided,
            bsedmat_fname and bsexmat_fname must be provided.
        bsedmat_fname : str, optional
            Path to the bsedmat file produced by kernel.
        bsexmat_fname : str, optional
            Path to the bsexmat file produced by kernel.
        eqp_fname : str
            Path to either eqp0.dat or eqp1.dat file produced by sigma.
        extra_lines : list[str], optional
            Any other lines that should appear in the input file.
        extra_variables : dict[str, Any], optional
            Any other variables that should be declared in the input file.
        """
        super().__init__(dirname, **kwargs)

        # Input file
        nbnd_val_co: int = kwargs["nbnd_val_co"]
        nbnd_cond_co: int = kwargs["nbnd_cond_co"]
        nbnd_val_fi: int = kwargs["nbnd_val_fi"]
        nbnd_cond_fi: int = kwargs["nbnd_cond_fi"]
        extra_lines: list[str] = kwargs.get("extra_lines", [])
        extra_variables: dict[str, Any] = kwargs.get("extra_variables", {})

        self.input = AbsorptionInput(
            nbnd_val_co,
            nbnd_cond_co,
            nbnd_val_fi,
            nbnd_cond_fi,
            *extra_lines,
            **extra_variables,
        )

        self.input.fname = self._input_fname

        # Set up the run script - link files
        self.wfn_co_fname = kwargs["wfn_co_fname"]
        self.wfn_fi_fname = kwargs["wfn_fi_fname"]
        self.wfnq_fi_fname = kwargs["wfnq_fi_fname"]

        self.eps0mat_fname = kwargs["eps0mat_fname"]
        self.epsmat_fname = kwargs["epsmat_fname"]

        if "bsemat_fname" in kwargs:
            self.bsemat_fname = kwargs["bsemat_fname"]
        else:
            self.bsedmat_fname = kwargs["bsedmat_fname"]
            self.bsexmat_fname = kwargs["bsexmat_fname"]

        self.eqp_fname = kwargs["eqp_fname"]

        ex = "absorption.cplx.x" if self._flavor_complex else "absorption.real.x"
        self.runscript["ABSORPTION"] = ex
        self.runscript.append(f"$MPIRUN $ABSORPTION &> {self._output_fname}")

    @property
    def wfn_co_fname(self) -> str:
        """Get path to the coarse wavefunction file."""
        return self._wfn_co_fname

    @wfn_co_fname.setter
    def wfn_co_fname(self, value: str) -> None:
        """Set path to the coarse wavefunction file and update symlink."""
        self._wfn_co_fname = value
        self.update_link(value, "WFN_co")

    @property
    def wfn_fi_fname(self) -> str:
        """Get path to the fine wavefunction file."""
        return self._wfn_fi_fname

    @wfn_fi_fname.setter
    def wfn_fi_fname(self, value: str) -> None:
        """Set path to the fine wavefunction file and update symlink."""
        self._wfn_fi_fname = value
        self.update_link(value, "WFN_fi")

    @property
    def wfnq_fi_fname(self) -> str:
        """Get path to the q-shifted fine wavefunction file."""
        return self._wfnq_fi_fname

    @wfnq_fi_fname.setter
    def wfnq_fi_fname(self, value: str) -> None:
        """Set path to the q-shifted fine wavefunction file and update symlink."""
        self._wfnq_fi_fname = value
        self.update_link(value, "WFNq_fi")

    @property
    def eps0mat_fname(self) -> str:
        """Get path to the eps0mat file."""
        return self._eps0mat_fname

    @eps0mat_fname.setter
    def eps0mat_fname(self, value: str) -> None:
        """Set path to the eps0mat file and update symlink."""
        self._eps0mat_fname = value
        dest = "eps0mat.h5" if self._use_hdf5 else "eps0mat"
        self.update_link(value, dest)

    @property
    def epsmat_fname(self) -> str:
        """Get path to the epsmat file."""
        return self._epsmat_fname

    @epsmat_fname.setter
    def epsmat_fname(self, value: str) -> None:
        """Set path to the epsmat file and update symlink."""
        self._epsmat_fname = value
        dest = "epsmat.h5" if self._use_hdf5 else "epsmat"
        self.update_link(value, dest)

    @property
    def bsemat_fname(self) -> str:
        """Get path to the bsemat file."""
        return self._bsemat_fname

    @bsemat_fname.setter
    def bsemat_fname(self, value: str) -> None:
        """Set path to the bsemat file and update symlink."""
        self._bsemat_fname = value
        dest = "bsemat.h5" if self._use_hdf5 else "bsemat"
        self.update_link(value, dest)

    @property
    def bsedmat_fname(self) -> str:
        """Get path to the bsedmat file."""
        return self._bsedmat_fname

    @bsedmat_fname.setter
    def bsedmat_fname(self, value: str) -> None:
        """Set path to the bsedmat file and update symlink."""
        self._bsedmat_fname = value
        dest = "bsedmat.h5" if self._use_hdf5 else "bsedmat"
        self.update_link(value, dest)

    @property
    def bsexmat_fname(self) -> str:
        """Get path to the bsexmat file."""
        return self._bsexmat_fname

    @bsexmat_fname.setter
    def bsexmat_fname(self, value: str) -> None:
        """Set path to the bsexmat file and update symlink."""
        self._bsexmat_fname = value
        dest = "bsexmat.h5" if self._use_hdf5 else "bsexmat"
        self.update_link(value, dest)

    @property
    def sigma_fname(self) -> str:
        """Get path to the sigma_hp.log file."""
        return self._sigma_fname

    @sigma_fname.setter
    def sigma_fname(self, value: str) -> None:
        """Set path to the sigma_hp.log file and update symlink."""
        self._sigma_fname = value
        self.update_link(value, "sigma_hp.log")

    @property
    def eqp_fname(self) -> str:
        """Get path to the eqp file."""
        return self._eqp_fname

    @eqp_fname.setter
    def eqp_fname(self, value: str) -> None:
        """Set path to the eqp file and update symlink."""
        self._eqp_fname = value
        self.update_link(value, "eqp_co.dat")

    def write(self) -> None:
        """Write the task files to disk."""
        super().write()
        with self.exec_from_dirname():
            self.input.write()
