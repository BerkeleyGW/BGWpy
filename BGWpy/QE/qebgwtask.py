from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from numpy import array

from BGWpy.config import flavors
from BGWpy.core import Namelist

from .qetask import QeTask

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import ArrayLike, NDArray

# Public
__all__ = ["Qe2BgwInput", "Qe2BgwTask"]


class Qe2BgwInput(Namelist):
    _ngkpt: NDArray[np.float64] = array([1, 1, 1])
    _kshift: NDArray[np.float64] = array([0.0, 0.0, 0.0])
    _qshift: NDArray[np.float64] = array([0.0, 0.0, 0.0])

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ngkpt = kwargs.pop("ngkpt", 3 * [0.0])
        kshift = kwargs.pop("kshift", 3 * [0.0])
        qshift = kwargs.pop("qshift", 3 * [0.0])

        super().__init__("input_pw2bgw", *args, **kwargs)

        # Sort the variables so that they look nice in the input file.
        prefered_order = [
            "prefix",
            "real_or_complex",
            "wfng_flag",
            "wfng_file",
            "rhog_flag",
            "rhog_file",
            "vxc_flag",
            "vxc_file",
            "vxcg_flag",
            "vxcg_file",
            "vxc_offdiag_nmin",
            "vxc_offdiag_nmax",
            "vxc_diag_nmin",
            "vxc_diag_nmax",
            "wfng_kgrid",
        ]
        for key in prefered_order:
            value = self.pop(key, None)
            if value is not None:
                self[key] = value
        for key in self.keys():
            if key not in prefered_order:
                value = self.pop(key)
                self[key] = value

        # Maybe let these be handled by PW2BGWTask
        self.ngkpt = ngkpt
        self.kshift = kshift
        self.qshift = qshift

    @property
    def ngkpt(self) -> NDArray[np.float64]:
        return self._ngkpt

    @ngkpt.setter
    def ngkpt(self, ngkpt: ArrayLike) -> None:
        self._ngkpt = array(ngkpt)
        self["wfng_nk1"] = self._ngkpt[0]
        self["wfng_nk2"] = self._ngkpt[1]
        self["wfng_nk3"] = self._ngkpt[2]
        self._set_kqshift()

    @property
    def kshift(self) -> NDArray[np.float64]:
        return self._kshift

    @kshift.setter
    def kshift(self, kshift: ArrayLike) -> None:
        self._kshift = array(kshift)
        self._set_kqshift()

    @property
    def qshift(self) -> NDArray[np.float64]:
        return self._qshift

    @qshift.setter
    def qshift(self, qshift: ArrayLike) -> None:
        self._qshift = array(qshift)
        self._set_kqshift()

    @property
    def kqshift(self) -> NDArray[np.float64]:
        return self.kshift + self.qshift * self.ngkpt

    def _set_kqshift(self) -> None:
        self["wfng_dk1"] = self.kqshift[0]
        self["wfng_dk2"] = self.kqshift[1]
        self["wfng_dk3"] = self.kqshift[2]


class Qe2BgwTask(QeTask):
    """Wavefunctions convertion."""

    _TASK_NAME = "PW2BGW"

    _input_fname = "wfn.pp.in"
    _output_fname = "wfn.pp.out"

    def __init__(self, dirname: str, **kwargs: Any) -> None:
        """
        Arguments
        ---------

        dirname : str
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


        Properties
        ----------

        wfn_fname : str
            Path to the wavefunction file produced.
        rho_fname : str
            Path to the density file produced.
        vxc_dat_fname : str
            Path to the vxc.dat file produced.
        """

        kwargs.setdefault("runscript_fname", "pw2bgw.run.sh")

        # Check if user explicitly provided nproc
        user_provided_nproc = "nproc" in kwargs

        super().__init__(dirname, **kwargs)

        # pw2bgw.x doesn't scale well to many processors, so cap at 32.
        # Only apply this limit when using default_mpi settings.
        # If the user explicitly provides nproc, respect their choice (they may know better).
        if not user_provided_nproc:
            if self._nproc is None:
                # If nproc is None (unset in config), set it to 32.
                # This prevents MPI launchers like ibrun from defaulting to all available cores.
                # Use the property setter to trigger runscript update.
                self.nproc = 32
            elif self._nproc > 32:
                # Cap high default values to prevent pw2bgw scaling issues.
                # pw2bgw fails or performs poorly with large processor counts (e.g., 56+ cores).
                # Use the property setter to trigger runscript update.
                self.nproc = 32

        self._ngkpt = array(kwargs.pop("ngkpt"))
        self._kshift = array(kwargs.get("kshift", 3 * [0.0]))
        self._qshift = array(kwargs.get("qshift", 3 * [0.0]))

        # Maybe let the defaults be handled by PW2BGWInput

        # Input file
        defaults = {
            "ngkpt": self.ngkpt,
            "kshift": self.kshift,
            "qshift": self.qshift,
            "wfng_file": kwargs.get("wfn_fname", "wfn.cplx"),
            "real_or_complex": 2 if flavors["flavor_complex"] else 1,
            "wfng_flag": True,
            "wfng_kgrid": True,
        }

        rho_defaults = {
            "rhog_flag": True,
            "rhog_file": "rho.real",
            "vxcg_flag": False,
            "vxcg_file": "vxc.real",
            "vxc_flag": True,
            "vxc_file": "vxc.dat",
            "vxc_diag_nmin": 1,
            "vxc_diag_nmax": kwargs.get("nbnd", 1),
            "vxc_offdiag_nmin": 0,
            "vxc_offdiag_nmax": 0,
        }

        if kwargs.get("rho_fname") or kwargs.get("rhog_flag"):
            defaults.update(rho_defaults)

        variables = {}
        for key, value in defaults.items():
            variables[key] = kwargs.get(key, value)

        self.input = Qe2BgwInput(prefix=self.prefix, **variables)

        # Have to make sure the properties are set correctly.
        if "wfn_fname" in kwargs:
            self.wfn_fname = kwargs["wfn_fname"]
        elif "wfng_file" in kwargs:
            self.wfn_fname = kwargs["wfng_file"]
        if "rho_fname" in kwargs:
            self.rho_fname = kwargs["rho_fname"]
        if "vxc_dat_fname" in kwargs:
            self.vxc_dat_fname = kwargs["vxc_dat_fname"]

        self.input.fname = self._input_fname

        # Run script
        self.runscript["PW2BGW"] = "pw2bgw.x"
        self.runscript.append(
            f"$MPIRUN $PW2BGW $PWFLAGS -in {self._input_fname} &> {self._output_fname}"
        )

    _wfn_fname = "wfn.cplx"

    @property
    def wfn_fname(self) -> str:
        return str(Path(self.dirname) / self._wfn_fname)

    @wfn_fname.setter
    def wfn_fname(self, value: str) -> None:
        self._wfn_fname = value
        self.input["wfng_file"] = value

    _rho_fname = "rho.real"

    @property
    def rho_fname(self) -> str:
        return str(Path(self.dirname) / self._rho_fname)

    @rho_fname.setter
    def rho_fname(self, value: str) -> None:
        self._rho_fname = value
        self.input["rhog_file"] = value

    _vxc_dat_fname = "vxc.dat"

    @property
    def vxc_dat_fname(self) -> str:
        return str(Path(self.dirname) / self._vxc_dat_fname)

    @vxc_dat_fname.setter
    def vxc_dat_fname(self, value: str) -> None:
        self._vxc_dat_fname = value
        self.input["vxc_file"] = value
