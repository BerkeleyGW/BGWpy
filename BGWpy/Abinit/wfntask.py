from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .abinittask import AbinitTask

__all__ = ["AbinitWfnTask"]


class AbinitWfnTask(AbinitTask):
    """Charge density calculation."""

    _TASK_NAME = "Wfn"

    _input_fname = "wfn.in"
    _output_fname = "wfn.out"

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """
        Arguments
        ---------

        dirname : str | Path
            Directory in which the files are written and the code is executed.
            Will be created if needed.


        Keyword Arguments
        -----------------

        charge_density_fname : str
            Name of the density file produced by a previous SCF run (_DEN).
        ecut : float
            Kinetic energy cut-off, in Hartree.
        nband : int
            Number of bands to be computed.
        nbdbuf : int
            Number of bands in the buffer, useful for NSCF calculations in lots of bands.
        tolwfr : float (1e-16)
            Tolerance on wavefunctions residual used as a convergence criterion
            for the NSCF cycle.
        prefix : str
            Prefix used as a rootname for abinit calculations.
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ngkpt : list(3), int, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
        input_wavefunction_fname: str, optional
            Name of previously compute wavefunction file, in case you want
            to restart from there.
        input_variables : dict
            Any other input variables for the Abinit input file.

        See also:
            BGWpy.Abinit.abinittask.AbinitTask

        """

        kwargs.setdefault("prefix", "wfn")

        super().__init__(dirname, **kwargs)

        self.charge_density_fname = kwargs["charge_density_fname"]

        if "input_wavefunction_fname" in kwargs:
            self.input_wavefunction_fname = kwargs["input_wavefunction_fname"]

        self.input.set_variables(self.get_wfn_variables(**kwargs))

    def get_wfn_variables(self, **kwargs: Any) -> dict[str, Any]:
        """Return a dict of variables required for an SCF calculation."""

        nband = kwargs.get("nband")
        if nband is None:
            nband = kwargs.get("nbnd")

        ecut = kwargs.get("ecut")
        if ecut is None:
            ecut = kwargs.get("ecutwfc")
            if ecut is None:
                msg = "Please specify 'ecut' for Abinit."
                raise ValueError(msg)
            # Maybe warn the user that ecut is in Hartree?

        return {
            "ecut": ecut,
            "nband": nband,
            "irdden": 1,
            "nbdbuf": kwargs.get("nbdbuf", 0),
            "irdwfk": 1 if self.input_wavefunction_fname else 0,
            "tolwfr": kwargs.get("tolwfr", 1e-16),
            "iscf": kwargs.get("iscf", -3),
            "istwfk": kwargs.get("istwfk", "*1"),
        }

    @property
    def wavefunction_fname(self) -> str:
        return self.get_odat("WFK")

    wfn_fname = wavefunction_fname
    wfk_fname = wavefunction_fname

    _charge_density_fname: str | None = None

    @property
    def charge_density_fname(self) -> str:
        if self._charge_density_fname is not None:
            return self._charge_density_fname
        return self.get_odat("DEN")

    @charge_density_fname.setter
    def charge_density_fname(self, value: str | Path) -> None:
        value_str = str(value)
        self._charge_density_fname = value_str
        dest = os.path.relpath(self.get_idat("DEN"), self.dirname)
        if value_str.endswith(".nc"):
            dest += ".nc"
        self.update_link(value_str, dest)

    rho_fname = charge_density_fname

    _input_wavefunction_fname: str = ""

    @property
    def input_wavefunction_fname(self) -> str:
        return self._input_wavefunction_fname

    @input_wavefunction_fname.setter
    def input_wavefunction_fname(self, value: str | Path) -> None:
        value_str = str(value)
        self._input_wavefunction_fname = value_str
        dest = os.path.relpath(self.get_idat("WFK"), self.dirname)
        self.update_link(value_str, dest)

    @property
    def exchange_correlation_potential_fname(self) -> str:
        return self.get_odat("VXC")

    vxc_fname = exchange_correlation_potential_fname
