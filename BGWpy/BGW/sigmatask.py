"""Sigma task for self-energy calculation.

This module provides the SigmaTask class for computing the self-energy
using BerkeleyGW's sigma.x executable.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import ArrayLike, NDArray

from .bgwtask import BGWTask
from .inputs import SigmaInput
from .kgrid import KgridTask

__all__ = ["SigmaTask"]


class SigmaTask(BGWTask):
    """Self-energy calculation.

    This task computes the GW self-energy using BerkeleyGW's sigma.x
    executable.

    Attributes
    ----------
    input : SigmaInput
        The sigma input file object.
    kgridtask : KgridTask
        Task for generating k-point grids (if ngkpt is provided).

    Properties
    ----------
    sigma_fname : str
        Path to the sigma_hp.log file produced.
    eqp0_fname : str
        Path to the eqp0.dat file produced.
    eqp1_fname : str
        Path to the eqp1.dat file produced.
    wfn_co_fname : str
        Path to the coarse wavefunction file.
    rho_fname : str
        Path to the density file.
    vxc_dat_fname : str
        Path to the vxc.dat file.
    vxc_fname : str
        Path to the VXC file.
    eps0mat_fname : str
        Path to the eps0mat file.
    epsmat_fname : str
        Path to the epsmat file.
    """

    _TASK_NAME: str = "Sigma"
    _input_fname: str = "sigma.inp"
    _output_fname: str = "sigma.out"

    input: SigmaInput
    kgridtask: KgridTask
    _wfn_co_fname: str
    _rho_fname: str
    _vxc_dat_fname: str
    _vxc_fname: str
    _eps0mat_fname: str | None
    _epsmat_fname: str | None
    _ngkpt: NDArray[np.float64] | None
    _kshift: NDArray[np.float64] | None
    _qshift: NDArray[np.float64] | None

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """Initialize a sigma task.

        Parameters
        ----------
        dirname : str | Path
            Directory in which the files are written and the code is executed.
            Will be created if needed.

        Other Parameters
        ----------------
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ngkpt : list(3), int, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
            K-points are either specified using ngkpt or using kpts.
        kpts : Sequence[ArrayLike], optional
            List of k-points. Alternative to ngkpt.
        ibnd_min : int
            Minimum band index for GW corrections.
        ibnd_max : int
            Maximum band index for GW corrections.
        ngqpt : ArrayLike, optional
            Q-points grid, for HF or hybrid functionals.
        qpts : Sequence[ArrayLike], optional
            List of q-points, for HF or hybrid functionals.
        wfn_co_fname : str
            Path to the wavefunction file produced by pw2bgw.
        rho_fname : str
            Path to the density file produced by pw2bgw.
        vxc_dat_fname : str, optional
            Path to the vxc file produced by pw2bgw.
        vxc_fname : str, optional
            Path to the VXC file (alternative to vxc_dat_fname).
        eps0mat_fname : str, optional
            Path to the eps0mat file produced by epsilon.
        epsmat_fname : str, optional
            Path to the epsmat file produced by epsilon.
        extra_lines : list[str], optional
            Any other lines that should appear in the input file.
        extra_variables : dict[str, Any], optional
            Any other variables that should be declared in the input file.
        symkpt : bool, default=True
            Whether to use symmetries for k-point generation.
        fft : ArrayLike, optional
            FFT grid dimensions.
        use_tr : bool, optional
            Whether to use time-reversal symmetry.
        clean_after : bool, optional
            Whether to clean up after k-grid generation.
        """
        super().__init__(dirname, **kwargs)

        # Store ngkpt, kshift, qshift if provided in kwargs (read-only after init)
        self._ngkpt = np.array(kwargs["ngkpt"]) if "ngkpt" in kwargs else None
        self._kshift = np.array(kwargs["kshift"]) if "kshift" in kwargs else None
        self._qshift = np.array(kwargs["qshift"]) if "qshift" in kwargs else None

        extra_lines: list[str] = list(kwargs.get("extra_lines", []))
        extra_variables: dict[str, Any] = kwargs.get("extra_variables", {})

        # HDF5 WFN input: with an HDF5 WFN_inner, BerkeleyGW reads the hardcoded name
        # WFN_inner.h5 (not WFN_inner) and requires the use_wfn_hdf5 keyword. Detect
        # from the .h5 suffix so callers only pass a filename; the link destination is
        # set to match in the wfn_co_fname setter.
        if (
            str(kwargs["wfn_co_fname"]).endswith(".h5")
            and "use_wfn_hdf5" not in extra_lines
        ):
            extra_lines.append("use_wfn_hdf5")

        # Use specified kpoints or compute them from grid.
        kpt_aliases: tuple[str, ...] = (
            "kpts",
            "kpoints",
            "sigma_kpts",
            "sigma_k_points",
            "sigma_kpoints",
        )
        kpts: Sequence[ArrayLike] | list[list[float]] | NDArray[np.float64] | None = None
        for key in kpt_aliases:
            if key in kwargs:
                kpts = kwargs[key]
                break

        if kpts is None:
            # Compute k-points grids
            kgrid_kwargs: dict[str, Any] = {}
            for key in ("structure", "ngkpt", "fft", "use_tr", "clean_after"):
                if key in kwargs:
                    kgrid_kwargs[key] = kwargs[key]
            self.kgridtask = KgridTask(dirname=dirname, **kgrid_kwargs)

            symkpt: bool = kwargs.get("symkpt", True)
            if symkpt:
                kpts_result, _wtks = self.kgridtask.get_kpoints()
                kpts = kpts_result
            else:
                kpts_result, _wtks = self.kgridtask.get_kpt_grid_nosym()
                kpts = kpts_result.tolist()

        # At this point, kpts must be defined
        if kpts is None:
            msg = "kpts must be provided or computed from grid"
            raise ValueError(msg)

        # Use specified qpoints or compute them from grid (HF).
        qpts: Sequence[ArrayLike]
        if "qpts" in kwargs:
            qpts = kwargs["qpts"]
        elif "ngqpt" in kwargs:
            kgrid_kwargs = {"ngkpt": kwargs["ngqpt"]}
            for key in ("structure", "fft", "use_tr", "clean_after"):
                if key in kwargs:
                    kgrid_kwargs[key] = kwargs[key]
            self.kgridtask = KgridTask(dirname=dirname, **kgrid_kwargs)
            qpts, _wtqs = self.kgridtask.get_kpoints()
        else:
            qpts = []

        if "ngqpt" in kwargs:
            extra_variables["qpts"] = qpts
            extra_variables["ngqpt"] = kwargs["ngqpt"]

        # Input file
        ibnd_min: int = kwargs["ibnd_min"]
        ibnd_max: int = kwargs["ibnd_max"]
        self.input = SigmaInput(
            ibnd_min,
            ibnd_max,
            kpts,
            *extra_lines,
            **extra_variables,
        )

        self.input.fname = self._input_fname

        # Prepare links
        self.wfn_co_fname = kwargs["wfn_co_fname"]
        self.rho_fname = kwargs["rho_fname"]

        if "vxc_dat_fname" in kwargs:
            self.vxc_dat_fname = kwargs["vxc_dat_fname"]
        elif "vxc_fname" in kwargs:
            self.vxc_fname = kwargs["vxc_fname"]
        else:
            msg = "Either 'vxc_dat_fname' or 'vxc_fname' must be provided to SigmaTask."
            raise ValueError(msg)

        # It might be useful to issue a warning if those
        # files are not specified, but one would have to check the value
        # of frequency_dependence...
        self.eps0mat_fname = kwargs.get("eps0mat_fname")
        self.epsmat_fname = kwargs.get("epsmat_fname")

        # Set up the run script
        ex = "sigma.cplx.x" if self._flavor_complex else "sigma.real.x"
        self.runscript["SIGMA"] = ex
        self.runscript.append(f"$MPIRUN $SIGMA $SIGMAFLAGS &> {self._output_fname}")

    @property
    def ngkpt(self) -> NDArray[np.float64] | None:
        """Get the k-point grid dimensions."""
        return self._ngkpt

    @property
    def kshift(self) -> NDArray[np.float64] | None:
        """Get the k-point shift."""
        return self._kshift

    @property
    def qshift(self) -> NDArray[np.float64] | None:
        """Get the q-point shift."""
        return self._qshift

    @property
    def wfn_co_fname(self) -> str:
        """Get path to the coarse wavefunction file."""
        return self._wfn_co_fname

    @wfn_co_fname.setter
    def wfn_co_fname(self, value: str | Path) -> None:
        """Set path to the coarse wavefunction file and update symlink."""
        value_str = str(value)
        self._wfn_co_fname = value_str
        # BerkeleyGW reads WFN_inner.h5 (not WFN_inner) when the WFN is HDF5.
        self.update_link(
            value_str, "WFN_inner.h5" if value_str.endswith(".h5") else "WFN_inner"
        )

    @property
    def rho_fname(self) -> str:
        """Get path to the density file."""
        return self._rho_fname

    @rho_fname.setter
    def rho_fname(self, value: str | Path) -> None:
        """Set path to the density file and update symlink."""
        value_str = str(value)
        self._rho_fname = value_str
        self.update_link(value_str, "RHO")

    @property
    def vxc_dat_fname(self) -> str:
        """Get path to the vxc.dat file."""
        return self._vxc_dat_fname

    @vxc_dat_fname.setter
    def vxc_dat_fname(self, value: str | Path) -> None:
        """Set path to the vxc.dat file and update symlink."""
        value_str = str(value)
        self._vxc_dat_fname = value_str
        self.update_link(value_str, "vxc.dat")

    @property
    def vxc_fname(self) -> str:
        """Get path to the VXC file."""
        return self._vxc_fname

    @vxc_fname.setter
    def vxc_fname(self, value: str | Path) -> None:
        """Set path to the VXC file and update symlink."""
        value_str = str(value)
        self._vxc_fname = value_str
        self.update_link(value_str, "VXC")

    @property
    def eps0mat_fname(self) -> str | None:
        """Get path to the eps0mat file."""
        return self._eps0mat_fname

    @eps0mat_fname.setter
    @BGWTask.h5_wrap
    def eps0mat_fname(self, value: str | Path | None) -> None:
        """Set path to the eps0mat file and update symlink."""
        value_str = None if value is None else str(value)
        self._eps0mat_fname = value_str
        dest = "eps0mat.h5" if self._use_hdf5 else "eps0mat"
        self.update_link(value_str, dest)

    @property
    def epsmat_fname(self) -> str | None:
        """Get path to the epsmat file."""
        return self._epsmat_fname

    @epsmat_fname.setter
    @BGWTask.h5_wrap
    def epsmat_fname(self, value: str | Path | None) -> None:
        """Set path to the epsmat file and update symlink."""
        value_str = None if value is None else str(value)
        self._epsmat_fname = value_str
        dest = "epsmat.h5" if self._use_hdf5 else "epsmat"
        self.update_link(value_str, dest)

    def write(self) -> None:
        """Write the task files to disk."""
        super().write()
        with self.exec_from_dirname():
            self.input.write()

    @property
    def sigma_fname(self) -> str:
        """Get path to the sigma_hp.log file produced."""
        return str(Path(self.dirname) / "sigma_hp.log")

    @property
    def eqp0_fname(self) -> str:
        """Get path to the eqp0.dat file produced."""
        return str(Path(self.dirname) / "eqp0.dat")

    @property
    def eqp1_fname(self) -> str:
        """Get path to the eqp1.dat file produced."""
        return str(Path(self.dirname) / "eqp1.dat")
