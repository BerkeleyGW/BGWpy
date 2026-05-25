"""Abinit to BGW interface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from BGWpy.core import BasicInputFile, fortran_str

from .abinittask import AbinitTask

__all__ = ["Abi2BgwInput", "Abi2BgwTask"]


# Note
# The implementation of abi2bgw is different from that of pw2bgw.
# Here the kpoint grid is handled by the task rather than the input.


class Abi2BgwInput(BasicInputFile):
    def __init__(self, **kwargs: Any) -> None:
        """
        Keyword arguments
        -----------------
        wfng_file_abi : str
            Name of the wfn file produced by Abinit. (_WFK)
        wfng_flag : bool
            Activate the output of the wavefunction for BGW.
        wfng_file :
            Name of the wfn file for BGW.
        rhog_file_abi : str
            Name of the density file produced by Abinit. (_DEN)
        rhog_flag : bool
            Activate the output of the density for BGW.
        rhog_file : str
            Name of the density file for BGW.
        vxcg_file_abi : str
            Name of the xc potential file produced by Abinit. (_VXC)
        vxcg_flag : bool
            Activate the output of the xc potential for BGW.
        vxcg_file : str
            Name of the xc potential file for BGW.
        wfng_nk1 : int
            Number of k-point division along direction 1.
        wfng_nk2 : int
            Number of k-point division along direction 2.
        wfng_nk3 : int
            Number of k-point division along direction 3.
        wfng_dk1 : float
            k-point shift along direction 1.
        wfng_dk2 : float
            k-point shift along direction 2.
        wfng_dk3 : float
            k-point shift along direction 3.
        cell_symmetry : int
            Cell symmetry. 0 = cubic, 1 = hexagonal.
        symrel_file_flag : bool
            Write symmetry matrices in file.
        """

        super().__init__(fname=kwargs.get("fname", "abi2bgw.in"))

        # Flags and options
        self["wfng_flag"] = kwargs.get("wfng_flag", True)
        self["rhog_flag"] = kwargs.get("rhog_flag", False)
        self["vxcg_flag"] = kwargs.get("vxcg_flag", False)
        self["symrel_file_flag"] = kwargs.get("symrel_file_flag", False)
        self["cell_symmetry"] = kwargs.get("cell_symmetry", 0)

        # Output files
        self._wfn_fname = kwargs.get("wfng_file", "wfn.cplx")
        self["wfng_file"] = self._wfn_fname
        self._rho_fname = kwargs.get("rhog_file", "rho.cplx")
        self["rhog_file"] = self._rho_fname
        self._vxc_fname = kwargs.get("vxcg_file", "vxc.cplx")
        self["vxcg_file"] = self._vxc_fname

        # Input files
        self["wfng_file_abi"] = kwargs.get("wfng_file_abi")
        self["rhog_file_abi"] = kwargs.get("rhog_file_abi")
        self["vxcg_file_abi"] = kwargs.get("vxcg_file_abi")

        # k-points grid
        for key in ("wfng_nk1", "wfng_nk2", "wfng_nk3"):
            self[key] = kwargs.get(key)

        for key in ("wfng_dk1", "wfng_dk2", "wfng_dk3"):
            self[key] = kwargs.get(key, 0.0)

    def __str__(self) -> str:
        # The keyword order is rigid for abi2bgw.
        keys = [
            "wfng_file_abi",
            "wfng_flag",
            "wfng_file",
            "wfng_nk1",
            "wfng_nk2",
            "wfng_nk3",
            "wfng_dk1",
            "wfng_dk2",
            "wfng_dk3",
            "rhog_file_abi",
            "rhog_flag",
            "rhog_file",
            "cell_symmetry",
            "symrel_file_flag",
            "vxcg_file_abi",
            "vxcg_flag",
            "vxcg_file",
        ]

        result_str = ""
        for key in keys:
            result_str += f"{key} {fortran_str(self[key])}\n"
        return result_str


# =========================================================================== #


class Abi2BgwTask(AbinitTask):
    """Wavefunctions convertion."""

    _TASK_NAME = "Abi2BGW"
    _TAG_JOB_COMPLETED = "Calculation completed"

    _input_fname = "abi2bgw.in"
    _output_fname = "abi2bgw.out"

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """
        Arguments
        ---------

        dirname : str | Path
            Directory in which the files are written and the code is executed.
            Will be created if needed.


        Keyword arguments
        -----------------
        (All mandatory unless specified otherwise)

        prefix : str
            Prefix required by QE as a rootname.
        ngkpt : list(3), float
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
        wfn_fname : str ('wfn.cplx'), optional
            Name of the output wavefunction file.
        rhog_flag : bool (False), optional
            If True, will activacte the output of the density and vxc.
        rho_fname : str, optional
            Name of the ouput density file.
            If provided, will activacte the output of the density and vxc.
        nbnd : int, optional
            Number of bands for which vxc should be computed.
            Only if output of the density and vxc is active.

        See also: BGWpy.Abinit.Abi2BgwInput

        Properties
        ----------

        wfn_fname : str
            Path to the wavefunction file produced.
        rho_fname : str
            Path to the density file produced.
        vxc_fname : str
            Path to the vxc file produced.
        """

        kwargs.setdefault("runscript_fname", "abi2bgw.run.sh")

        super().__init__(dirname, **kwargs)

        self.input = Abi2BgwInput(**kwargs)
        self.input.fname = self._input_fname

        # Set the backing attributes directly first to avoid None values when setters call _set_kqshift
        ngkpt_value = kwargs.pop("ngkpt", None)
        if ngkpt_value is None:
            msg = "ngkpt is a required parameter for Abi2BgwTask"
            raise ValueError(msg)

        # Set backing attributes directly without triggering setters yet
        self._ngkpt = np.array(ngkpt_value)
        self._kshift = np.array(kwargs.get("kshift", 3 * [0.0]))
        self._qshift = np.array(kwargs.get("qshift", 3 * [0.0]))

        # Set input variables that the setters would have set
        self.input["wfng_nk1"] = self._ngkpt[0]
        self.input["wfng_nk2"] = self._ngkpt[1]
        self.input["wfng_nk3"] = self._ngkpt[2]

        # Now call _set_kqshift once with all values initialized
        self._set_kqshift()

        if kwargs.get("rhog_fname") or kwargs.get("rhog_file_abi"):
            self.set_rho()

        self.wfn_fname = kwargs.pop("wfn_fname", "")
        self.rho_fname = kwargs.pop("rho_fname", "")
        self.vxc_fname = kwargs.pop("vxc_fname", "")

        # Run script
        self.runscript["ABI2BGW"] = "abi2bgw.x"
        del self.runscript.main[:]
        self.runscript.append(f"$ABI2BGW {self._input_fname} >& {self._output_fname}")

    def write(self) -> None:
        Path(self.dirname).mkdir(parents=True, exist_ok=True)
        with self.exec_from_dirname():
            self.runscript.write()

        with self.exec_from_dirname():
            self.input.write()

    _wfn_fname: str = "wfn.cplx"

    @property
    def wfn_fname(self) -> str:
        return str(Path(self.dirname) / self._wfn_fname)

    @wfn_fname.setter
    def wfn_fname(self, value: str | Path) -> None:
        p = Path(value).absolute().relative_to(Path(self.dirname).absolute(), walk_up=True)
        # self._wfn_fname = p.name
        self.input["wfng_file_abi"] = str(p)

    _rho_fname: str = "rho.cplx"

    @property
    def rho_fname(self) -> str:
        return str(Path(self.dirname) / self._rho_fname)

    @rho_fname.setter
    def rho_fname(self, value: str | Path) -> None:
        p = Path(value).absolute().relative_to(Path(self.dirname).absolute(), walk_up=True)
        # self._rho_fname = p.name
        self.input["rhog_file_abi"] = str(p)

    _vxc_fname: str = "vxc.cplx"

    @property
    def vxc_fname(self) -> str:
        return str(Path(self.dirname) / self._vxc_fname)

    @vxc_fname.setter
    def vxc_fname(self, value: str | Path) -> None:
        p = Path(value).absolute().relative_to(Path(self.dirname).absolute(), walk_up=True)
        # self._vxc_fname = p.name
        self.input["vxcg_file_abi"] = str(p)

    _ngkpt: NDArray[np.float64] = np.array(3 * [1])

    @property
    def ngkpt(self) -> NDArray[np.float64]:
        return self._ngkpt

    @ngkpt.setter
    def ngkpt(self, ngkpt: ArrayLike) -> None:
        self._ngkpt = np.array(ngkpt)
        self.input["wfng_nk1"] = self._ngkpt[0]
        self.input["wfng_nk2"] = self._ngkpt[1]
        self.input["wfng_nk3"] = self._ngkpt[2]
        self._set_kqshift()

    _kshift: NDArray[np.float64] = np.array(3 * [0.0])

    @property
    def kshift(self) -> NDArray[np.float64]:
        return self._kshift

    shiftk = kshift  # Alias

    @kshift.setter
    def kshift(self, kshift: ArrayLike) -> None:
        self._kshift = np.array(kshift)
        self._set_kqshift()

    _qshift: NDArray[np.float64] = np.array(3 * [0.0])

    @property
    def qshift(self) -> NDArray[np.float64]:
        return self._qshift

    @qshift.setter
    def qshift(self, qshift: ArrayLike) -> None:
        self._qshift = np.array(qshift)
        self._set_kqshift()

    shiftq = qshift  # Alias

    @property
    def kqshift(self) -> NDArray[np.float64]:
        return self.kshift + self.qshift * self.ngkpt

    def _set_kqshift(self) -> None:
        self.input["wfng_dk1"] = self.kqshift[0]
        self.input["wfng_dk2"] = self.kqshift[1]
        self.input["wfng_dk3"] = self.kqshift[2]

    def set_rho(self) -> None:
        self.input["rhog_flag"] = True

    @property
    def output_fname(self) -> str:
        return str(Path(self.dirname) / self._output_fname)
