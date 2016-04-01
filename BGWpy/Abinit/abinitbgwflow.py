
from os.path import join as pjoin

from . import AbinitScfTask, AbinitWfnTask, Abi2BgwTask
from ..DFT import WfnBgwFlow

__all__ = ['AbinitBgwFlow']

class AbinitBgwFlow(WfnBgwFlow):

    def __init__(self, **kwargs):
        """
        Keyword Arguments
        -----------------

        dirname : str
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

        super(AbinitBgwFlow, self).__init__(**kwargs)

        kwargs.pop('dirname', None)

        #if kwargs.get('charge_density_fname'):
        #    kwargs.setdefault('with_density', False)

        ## SCF task
        #if self.with_density:
        #    self.scftask = AbinitScfTask(
        #        dirname = kwargs.get('density_dirname',
        #                             pjoin(self.dirname, 'Density')),
        #                             **kwargs)

        #    kwargs.setdefault('charge_density_fname',
        #                      self.scftask.charge_density_fname)

        #    kwargs.setdefault('vxc_fname',
        #                      self.scftask.vxc_fname)

        #    self.add_task(self.scftask, merge=False)

        self.charge_density_fname = kwargs['charge_density_fname']

        vxc_fname = kwargs.pop('vxc_fname', '')

        # Wfn task
        self.wfntask = AbinitWfnTask(dirname=self.dirname, **kwargs)
        self.wfntask.runscript.fname = 'wfn.run.sh'
        self.add_task(self.wfntask, merge=False)

        wfn_fname = kwargs.pop('wfn_fname',None)

        # Wfn 2 BGW
        self.wfnbgwntask = Abi2BgwTask(
            dirname = self.wfntask.dirname,
            wfng_flag = kwargs.pop('wfng_flag', True),
            rhog_flag = kwargs.pop('rhog_flag', True),
            vxcg_flag = kwargs.pop('vxcg_flag', bool(vxc_fname)),
            rho_fname = self.charge_density_fname,
            wfn_fname = self.wfntask.wfn_fname,
            vxc_fname = vxc_fname if vxc_fname else 'dummy',
            **kwargs)

        self.add_task(self.wfnbgwntask, merge=False)


    _charge_density_fname = ''

    @property
    def charge_density_fname(self):
        """The charge density used by Abinit."""
        return self._charge_density_fname

    @charge_density_fname.setter
    def charge_density_fname(self, value):
        self._charge_density_fname = value


    @property
    def rho_fname(self):
        """The charge density file name for BerkeleyGW."""
        return self.wfnbgwntask.rho_fname

    @property
    def wfn_fname(self):
        """The wavefunctions file name for BerkeleyGW."""
        return self.wfnbgwntask.wfn_fname

    @property
    def vxc_fname(self):
        """The xc potential file name for BerkeleyGW."""
        return self.wfnbgwntask.vxc_fname

    @property
    def vxc_dat_fname(self):
        raise NotImplementedError(
            'Please use vxc_fname instead of vxc_dat_fname.')

