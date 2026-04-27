"""Kernel task for BSE kernel calculation.

This module provides the KernelTask class for computing the BSE kernel
using BerkeleyGW's kernel.x executable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .bgwtask import BGWTask
from .inputs import KernelInput

__all__ = ["KernelTask"]


class KernelTask(BGWTask):
    """Kernel calculation for BSE.

    This task computes the BSE kernel using BerkeleyGW's kernel.x
    executable.

    Attributes
    ----------
    input : KernelInput
        The kernel input file object.

    Properties
    ----------
    bsedmat_fname : str
        Path to the bsedmat file produced.
    bsexmat_fname : str
        Path to the bsexmat file produced.
    bsemat_fname : str
        Path to the bsemat file produced.
    wfn_co_fname : str
        Path to the coarse wavefunction file.
    eps0mat_fname : str
        Path to the eps0mat file.
    epsmat_fname : str
        Path to the epsmat file.
    """

    _TASK_NAME: str = "Kernel"
    _input_fname: str = "kernel.inp"
    _output_fname: str = "kernel.out"

    input: KernelInput
    _wfn_co_fname: str
    _eps0mat_fname: str
    _epsmat_fname: str

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """Initialize a kernel task.

        Parameters
        ----------
        dirname : str | Path
            Directory in which the files are written and the code is executed.
            Will be created if needed.

        Other Parameters
        ----------------
        nbnd_val : int
            Number of valence bands.
        nbnd_cond : int
            Number of conduction bands.
        wfn_co_fname : str
            Path to the wavefunction file produced by pw2bgw.
        eps0mat_fname : str
            Path to the eps0mat file produced by epsilon.
        epsmat_fname : str
            Path to the epsmat file produced by epsilon.
        extra_lines : list[str], optional
            Any other lines that should appear in the input file.
        extra_variables : dict[str, Any], optional
            Any other variables that should be declared in the input file.
        """
        super().__init__(dirname, **kwargs)

        # Input file
        nbnd_val: int = kwargs["nbnd_val"]
        nbnd_cond: int = kwargs["nbnd_cond"]
        extra_lines: list[str] = kwargs.get("extra_lines", [])
        extra_variables: dict[str, Any] = kwargs.get("extra_variables", {})

        self.input = KernelInput(
            nbnd_val,
            nbnd_cond,
            *extra_lines,
            **extra_variables,
        )

        self.input.fname = self._input_fname

        # Set up the run script
        self.wfn_co_fname = kwargs["wfn_co_fname"]
        self.eps0mat_fname = kwargs["eps0mat_fname"]
        self.epsmat_fname = kwargs["epsmat_fname"]

        ex = "kernel.cplx.x" if self._flavor_complex else "kernel.real.x"
        self.runscript["KERNEL"] = ex
        self.runscript.append(f"$MPIRUN $KERNEL &> {self._output_fname}")

    @property
    def wfn_co_fname(self) -> str:
        """Get path to the coarse wavefunction file."""
        return self._wfn_co_fname

    @wfn_co_fname.setter
    def wfn_co_fname(self, value: str | Path) -> None:
        """Set path to the coarse wavefunction file and update symlink."""
        value_str = str(value)
        self._wfn_co_fname = value_str
        self.update_link(value_str, "WFN_co")

    @property
    def eps0mat_fname(self) -> str:
        """Get path to the eps0mat file."""
        return self._eps0mat_fname

    @eps0mat_fname.setter
    def eps0mat_fname(self, value: str | Path) -> None:
        """Set path to the eps0mat file and update symlink."""
        value_str = str(value)
        self._eps0mat_fname = value_str
        dest = "eps0mat.h5" if self._use_hdf5 else "eps0mat"
        self.update_link(value_str, dest)

    @property
    def epsmat_fname(self) -> str:
        """Get path to the epsmat file."""
        return self._epsmat_fname

    @epsmat_fname.setter
    def epsmat_fname(self, value: str | Path) -> None:
        """Set path to the epsmat file and update symlink."""
        value_str = str(value)
        self._epsmat_fname = value_str
        dest = "epsmat.h5" if self._use_hdf5 else "epsmat"
        self.update_link(value_str, dest)

    def write(self) -> None:
        """Write the task files to disk."""
        super().write()
        with self.exec_from_dirname():
            self.input.write()

    @property
    def bsedmat_fname(self) -> str:
        """Get path to the bsedmat file produced.

        Returns the HDF5 or binary filename depending on configuration.
        """
        basename = "bsedmat.h5" if self._use_hdf5 else "bsedmat"
        return str(Path(self.dirname) / basename)

    @property
    def bsexmat_fname(self) -> str:
        """Get path to the bsexmat file produced.

        Returns the HDF5 or binary filename depending on configuration.
        """
        basename = "bsexmat.h5" if self._use_hdf5 else "bsexmat"
        return str(Path(self.dirname) / basename)

    @property
    def bsemat_fname(self) -> str:
        """Get path to the bsemat file produced.

        Returns the HDF5 or binary filename depending on configuration.
        """
        basename = "bsemat.h5" if self._use_hdf5 else "bsemat"
        return str(Path(self.dirname) / basename)
