"""Epsilon task for inverse dielectric function calculation.

This module provides the EpsilonTask class for computing the inverse
dielectric function using BerkeleyGW's epsilon.x executable.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

from .bgwtask import BGWTask
from .inputs import EpsilonInput
from .kgrid import KgridTask

__all__ = ["EpsilonTask"]


class EpsilonTask(BGWTask):
    """Inverse dielectric function calculation.

    This task computes the dielectric matrix and its inverse using
    BerkeleyGW's epsilon.x executable.

    Attributes
    ----------
    input : EpsilonInput
        The epsilon input file object.
    kgridtask : KgridTask
        Task for generating k-point grids.

    Properties
    ----------
    eps0mat_fname : str
        Path to the eps0mat file produced.
    epsmat_fname : str
        Path to the epsmat file produced.
    wfn_fname : str
        Path to the wavefunction file.
    wfnq_fname : str
        Path to the q-shifted wavefunction file.
    """

    _TASK_NAME: str = "Epsilon"
    _input_fname: str = "epsilon.inp"
    _output_fname: str = "epsilon.out"

    input: EpsilonInput
    kgridtask: KgridTask
    _wfn_fname: str
    _wfnq_fname: str
    _ngkpt: NDArray[np.float64] | None
    _kshift: NDArray[np.float64] | None
    _qshift: NDArray[np.float64] | None

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """Initialize an epsilon task.

        Parameters
        ----------
        dirname : str | Path
            Directory in which the files are written and the code is executed.
            Will be created if needed.

        Other Parameters
        ----------------
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ngkpt : list(3), int
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice. This is actually a Q-points grid
            in a GW calculation.
        qshift : list(3), float
            Q-point used to treat the Gamma point.
        ecuteps : float
            Energy cutoff for the dielectric function, in Ry.
        wfn_fname : str
            Path to the wavefunction file produced by pw2bgw.
        wfnq_fname : str
            Path to the q-shifted wavefunction file produced by pw2bgw.
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

        # Compute k-points grids
        kgrid_kwargs: dict[str, Any] = {}
        for key in ("structure", "ngkpt", "fft", "use_tr", "clean_after"):
            if key in kwargs:
                kgrid_kwargs[key] = kwargs[key]
        self.kgridtask = KgridTask(dirname=dirname, **kgrid_kwargs)

        symkpt: bool = kwargs.get("symkpt", True)
        if symkpt:
            kpts_ush, _wtks_ush = self.kgridtask.get_kpoints()
        else:
            kpts_ush, _wtks_ush = self.kgridtask.get_kpt_grid_nosym()

        extra_lines: list[str] = list(kwargs.get("extra_lines", []))
        extra_variables: dict[str, Any] = kwargs.get("extra_variables", {})

        # HDF5 WFN input: with an HDF5 WFN, BerkeleyGW reads the hardcoded names
        # WFN.h5 / WFNq.h5 (not WFN / WFNq) and requires the use_wfn_hdf5 keyword.
        # Detect from the .h5 suffix so callers only pass a filename; the link
        # destinations are set to match in the wfn_fname / wfnq_fname setters. The
        # keyword makes BerkeleyGW read *both* WFN and WFNq as HDF5, so a mixed pair
        # would mislink one of them -- reject it rather than fail cryptically at run.
        wfn_is_hdf5 = str(kwargs["wfn_fname"]).endswith(".h5")
        wfnq_is_hdf5 = str(kwargs["wfnq_fname"]).endswith(".h5")
        if wfn_is_hdf5 != wfnq_is_hdf5:
            msg = (
                "wfn_fname and wfnq_fname must have the same format (both HDF5 '.h5' "
                f"or both binary): got wfn_fname={kwargs['wfn_fname']!r}, "
                f"wfnq_fname={kwargs['wfnq_fname']!r}"
            )
            raise ValueError(msg)
        if wfn_is_hdf5 and "use_wfn_hdf5" not in extra_lines:
            extra_lines.append("use_wfn_hdf5")

        # Input file
        qshift: ArrayLike = kwargs["qshift"]
        ecuteps: float = kwargs["ecuteps"]
        # Convert to list to handle both list and ndarray types uniformly
        if isinstance(kpts_ush, list):
            qpts = kpts_ush[1:]
        else:
            qpts = kpts_ush[1:].tolist()
        self.input = EpsilonInput(
            ecuteps,
            qshift,
            qpts,
            *extra_lines,
            **extra_variables,
        )

        self.input.fname = self._input_fname

        # Set up the run script
        self.wfn_fname = kwargs["wfn_fname"]
        self.wfnq_fname = kwargs["wfnq_fname"]

        ex = "epsilon.cplx.x" if self._flavor_complex else "epsilon.real.x"
        self.runscript["EPSILON"] = ex
        self.runscript.append(f"$MPIRUN $EPSILON &> {self._output_fname}")

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
    def wfn_fname(self) -> str:
        """Get path to the wavefunction file."""
        return self._wfn_fname

    @wfn_fname.setter
    def wfn_fname(self, value: str | Path) -> None:
        """Set path to the wavefunction file and update symlink."""
        value_str = str(value)
        self._wfn_fname = value_str
        # BerkeleyGW reads WFN.h5 (not WFN) when the WFN is HDF5; match by suffix.
        self.update_link(value_str, "WFN.h5" if value_str.endswith(".h5") else "WFN")

    @property
    def wfnq_fname(self) -> str:
        """Get path to the q-shifted wavefunction file."""
        return self._wfnq_fname

    @wfnq_fname.setter
    def wfnq_fname(self, value: str | Path) -> None:
        """Set path to the q-shifted wavefunction file and update symlink."""
        value_str = str(value)
        self._wfnq_fname = value_str
        # BerkeleyGW reads WFNq.h5 (not WFNq) when the WFN is HDF5; match by suffix.
        self.update_link(value_str, "WFNq.h5" if value_str.endswith(".h5") else "WFNq")

    def write(self) -> None:
        """Write the task files to disk."""
        super().write()
        with self.exec_from_dirname():
            self.input.write()

    @property
    def eps0mat_fname(self) -> str:
        """Get path to the eps0mat file produced.

        Returns the HDF5 or binary filename depending on configuration.
        """
        basename = "eps0mat.h5" if self._use_hdf5 else "eps0mat"
        return str(Path(self.dirname) / basename)

    @property
    def epsmat_fname(self) -> str:
        """Get path to the epsmat file produced.

        Returns the HDF5 or binary filename depending on configuration.
        """
        basename = "epsmat.h5" if self._use_hdf5 else "epsmat"
        return str(Path(self.dirname) / basename)
