from __future__ import annotations

import warnings
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
    _has_kgrid: bool = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ngkpt = kwargs.pop("ngkpt", None)
        kshift = kwargs.pop("kshift", 3 * [0.0])
        qshift = kwargs.pop("qshift", 3 * [0.0])

        super().__init__("input_pw2bgw", *args, **kwargs)

        # Sort the variables so that they look nice in the input file.
        # Use explicit sentinel to avoid dropping boolean False values (e.g.
        # wfng_kgrid=False or rhog_flag=False) which are falsy but valid.
        _sentinel = object()
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
            value = self.pop(key, _sentinel)
            if value is not _sentinel:
                self[key] = value
        for key in list(self.keys()):
            if key not in prefered_order:
                value = self.pop(key)
                self[key] = value

        # Only write grid-related keys when ngkpt is provided (i.e. wfng_kgrid=True).
        # When wfng_kgrid=False, pw2bgw passes through whatever k-points are in the
        # save directory, and wfng_nk*/wfng_dk* are not meaningful.
        if ngkpt is not None:
            self._has_kgrid = True
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
        if not self._has_kgrid:
            msg = "kqshift is not defined when wfng_kgrid is False."
            raise AttributeError(msg)
        return self.kshift + self.qshift * self.ngkpt

    def _set_kqshift(self) -> None:
        if not self._has_kgrid:
            msg = "Cannot set wfng_dk* values when wfng_kgrid is False."
            raise AttributeError(msg)
        self["wfng_dk1"] = self.kqshift[0]
        self["wfng_dk2"] = self.kqshift[1]
        self["wfng_dk3"] = self.kqshift[2]


class Qe2BgwTask(QeTask):
    """Wavefunctions conversion."""

    _TASK_NAME = "PW2BGW"

    _input_fname = "wfn.pp.in"
    _output_fname = "wfn.pp.out"

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
        wfng_kgrid : bool, optional (default: True)
            Whether to override the k-point grid description in the output
            WFN file with an explicit uniform grid (wfng_nk1/2/3 and
            wfng_dk1/2/3). Set to False when the wavefunctions were computed
            on a non-uniform k-point set (e.g. a band path for use as WFN_fi
            in inteqp), in which case pw2bgw will pass through whatever
            k-points are present in the QE save directory unchanged.
        ngkpt : list(3), float, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice. Required when wfng_kgrid is True
            (the default). Ignored with a warning when wfng_kgrid is False.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
            Ignored when wfng_kgrid is False.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
            Ignored when wfng_kgrid is False.
        wfn_fname : str ('wfn.cplx'), optional
            Name of the output wavefunction file.
        rhog_flag : bool (False), optional
            If True, will activate the output of the density and vxc.
        rho_fname : str, optional
            Name of the output density file.
            If provided, will activate the output of the density and vxc.
        nbnd : int, optional
            Number of bands for which vxc should be computed.
            Only if output of the density and vxc is active.
        vscg_flag : bool (False), optional
            If True, output the self-consistent potential in G-space (VSC), an
            input required by BerkeleyGW's ParaBands.
        vscg_file : str ('VSC'), optional
            Name of the output VSC file.
        vkbg_flag : bool (False), optional
            If True, output the Kleinman-Bylander projectors in G-space (VKB), an
            input used by BerkeleyGW's ParaBands.
        vkbg_file : str ('VKB'), optional
            Name of the output VKB file.


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

        # Read wfng_kgrid before super().__init__ so we can validate kwargs
        # early and avoid passing ngkpt-related keys down when not needed.
        wfng_kgrid: bool = kwargs.get("wfng_kgrid", True)

        # Validate / normalise grid kwargs relative to wfng_kgrid.
        _grid_keys = ("ngkpt", "kshift", "qshift")
        if wfng_kgrid:
            if "ngkpt" not in kwargs:
                msg = "'ngkpt' is required when wfng_kgrid is True (the default)."
                raise ValueError(msg)
        else:
            # Strip grid keys before passing kwargs to super().__init__() so they
            # don't reach DFTTask (which would set self._ngkpt) or KgridTask (which
            # would construct an unwanted grid task).  Warn if any were present so
            # the caller knows they had no effect.
            ignored = [k for k in _grid_keys if k in kwargs]
            if ignored:
                warnings.warn(
                    f"wfng_kgrid is False: the following grid keyword(s) will be "
                    f"ignored: {', '.join(ignored)}",
                    UserWarning,
                    stacklevel=2,
                )
                for k in ignored:
                    del kwargs[k]

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

        # Build input file defaults.
        defaults: dict[str, Any] = {
            "wfng_file": kwargs.get("wfn_fname", "wfn.cplx"),
            "real_or_complex": 2 if flavors["flavor_complex"] else 1,
            "wfng_flag": True,
            "wfng_kgrid": wfng_kgrid,
        }

        if wfng_kgrid:
            defaults["ngkpt"] = self.ngkpt
            defaults["kshift"] = self.kshift if self.kshift is not None else 3 * [0.0]
            defaults["qshift"] = self.qshift if self.qshift is not None else 3 * [0.0]

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

        # VSC (self-consistent potential) and VKB (Kleinman-Bylander projectors),
        # in G-space -- the extra inputs BerkeleyGW's ParaBands needs. Emitted only
        # when explicitly requested, so ordinary pw2bgw runs are unaffected.
        if kwargs.get("vscg_flag"):
            defaults["vscg_flag"] = True
            defaults["vscg_file"] = kwargs.get("vscg_file", "VSC")
        if kwargs.get("vkbg_flag"):
            defaults["vkbg_flag"] = True
            defaults["vkbg_file"] = kwargs.get("vkbg_file", "VKB")

        # Allow the caller to override any default, but exclude grid keys when
        # wfng_kgrid is False so they are never forwarded to Qe2BgwInput.
        variables: dict[str, Any] = {}
        for key, value in defaults.items():
            if not wfng_kgrid and key in _grid_keys:
                continue
            variables[key] = kwargs.get(key, value)

        self.input = Qe2BgwInput(prefix=self.prefix, **variables)

        # Have to make sure the properties are set correctly.
        if "wfn_fname" in kwargs:
            self.wfn_fname = kwargs["wfn_fname"]
        elif "wfng_file" in kwargs:
            self.wfn_fname = kwargs["wfng_file"]
        # Forward each output-file kwarg to its property (which also updates the
        # corresponding Qe2BgwInput key).
        for _fname_attr in (
            "rho_fname",
            "vxc_dat_fname",
            "vxc_fname",
            "vsc_fname",
            "vkb_fname",
        ):
            if _fname_attr in kwargs:
                setattr(self, _fname_attr, kwargs[_fname_attr])

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
    def wfn_fname(self, value: str | Path) -> None:
        value_str = str(value)
        self._wfn_fname = value_str
        self.input["wfng_file"] = value_str

    _rho_fname = "rho.real"

    @property
    def rho_fname(self) -> str:
        return str(Path(self.dirname) / self._rho_fname)

    @rho_fname.setter
    def rho_fname(self, value: str | Path) -> None:
        value_str = str(value)
        self._rho_fname = value_str
        self.input["rhog_file"] = value_str

    _vxc_dat_fname = "vxc.dat"

    @property
    def vxc_dat_fname(self) -> str:
        return str(Path(self.dirname) / self._vxc_dat_fname)

    @vxc_dat_fname.setter
    def vxc_dat_fname(self, value: str | Path) -> None:
        value_str = str(value)
        self._vxc_dat_fname = value_str
        self.input["vxc_file"] = value_str

    # Default matches the vxcg_file default in the rho_defaults block above; the
    # setter (and the vxc_fname forward in __init__) keep this in sync with the
    # input file's vxcg_file when a caller overrides it.
    _vxc_fname = "vxc.real"

    @property
    def vxc_fname(self) -> str:
        """Path to the G-space VXC file (XC potential; only if vxcg_flag)."""
        return str(Path(self.dirname) / self._vxc_fname)

    @vxc_fname.setter
    def vxc_fname(self, value: str | Path) -> None:
        value_str = str(value)
        self._vxc_fname = value_str
        self.input["vxcg_file"] = value_str

    _vsc_fname = "VSC"

    @property
    def vsc_fname(self) -> str:
        """Path to the VSC file (self-consistent potential; only if vscg_flag)."""
        return str(Path(self.dirname) / self._vsc_fname)

    @vsc_fname.setter
    def vsc_fname(self, value: str | Path) -> None:
        value_str = str(value)
        self._vsc_fname = value_str
        self.input["vscg_file"] = value_str

    _vkb_fname = "VKB"

    @property
    def vkb_fname(self) -> str:
        """Path to the VKB file (Kleinman-Bylander projectors; only if vkbg_flag)."""
        return str(Path(self.dirname) / self._vkb_fname)

    @vkb_fname.setter
    def vkb_fname(self, value: str | Path) -> None:
        value_str = str(value)
        self._vkb_fname = value_str
        self.input["vkbg_file"] = value_str
