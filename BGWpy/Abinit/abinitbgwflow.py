from __future__ import annotations

from typing import Any

from BGWpy.DFT import WfnBgwFlow

__all__ = ["AbinitBgwFlow"]


class AbinitBgwFlow(WfnBgwFlow):
    def __init__(self, **kwargs: Any) -> None:
        """
        Keyword Arguments
        -----------------

        dirname : str | Path
            Directory in which the files are written and the code is executed.
            Will be created if needed.
        charge_density_fname : str
            Charge density file produced by Abinit in a previous SCF task.
        vxc_fname : str
            The xc potential file produced by Abinit, in a previous SCF task.
            If none is available, the flag for VXC conversion to BGW will be unset.
        ecut : float
            Kinetic energy cut-off, in Hartree.
        nband : int
            Number of bands to be computed.
        tolvrs : float (1e-10)
            Tolerance on residual potential used as a convergence criterion
            for the SCF cycle.
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
        input_variables : dict
            Any other input variables for the Abinit input file.

        See also:
            BGWpy.Abinit.AbinitScfTask
            BGWpy.Abinit.AbinitWfnTask
            BGWpy.Abinit.Abi2BgwTask


        Properties
        ----------

        charge_density_fname : str
            The charge density file used by Abinit.

        rho_fname : str
            The charge density file name used by BerkeleyGW.

        wfn_fname : str
            The wavefunctions file name used by BerkeleyGW.

        vxc_fname : str
            The xc potential file name used by BerkeleyGW.

        """

        super().__init__(**kwargs)

        kwargs.pop("dirname", None)

        self.charge_density_fname = kwargs["charge_density_fname"]

        vxc_fname = kwargs.pop("vxc_fname", "")

        # Wfn task
        from .wfntask import AbinitWfnTask

        self.wfntask = AbinitWfnTask(dirname=self.dirname, **kwargs)
        self.wfntask.runscript.fname = "wfn.run.sh"
        self.add_task(self.wfntask, merge=False)

        kwargs.pop("wfn_fname", None)

        # Wfn 2 BGW
        from .abibgw import Abi2BgwTask

        self.wfnbgwntask = Abi2BgwTask(
            dirname=self.wfntask.dirname,
            wfng_flag=kwargs.pop("wfng_flag", True),
            rhog_flag=kwargs.pop("rhog_flag", True),
            vxcg_flag=kwargs.pop("vxcg_flag", bool(vxc_fname)),
            rho_fname=self.charge_density_fname,
            wfn_fname=self.wfntask.wfn_fname,
            vxc_fname=vxc_fname if vxc_fname else "",
            **kwargs,
        )

        self.add_task(self.wfnbgwntask, merge=False)

    charge_density_fname: str = ""

    @property
    def rho_fname(self) -> str:
        """The charge density file name for BerkeleyGW."""
        return self.wfnbgwntask.rho_fname

    @property
    def den_fname(self) -> str:
        """The charge density file name for BerkeleyGW."""
        return self.rho_fname

    @property
    def wfn_fname(self) -> str:
        """The wavefunctions file name for BerkeleyGW."""
        return self.wfnbgwntask.wfn_fname

    @property
    def vxc_fname(self) -> str:
        """The xc potential file name for BerkeleyGW."""
        return self.wfnbgwntask.vxc_fname

    @property
    def vxc_dat_fname(self) -> str:
        msg = "Please use vxc_fname instead of vxc_dat_fname."
        raise NotImplementedError(msg)
