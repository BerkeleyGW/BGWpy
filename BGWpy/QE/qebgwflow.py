
from os.path import join as pjoin

from . import QeScfTask, QeWfnTask, Qe2BgwTask
from ..DFT import WfnBgwFlow

__all__ = ['QeBgwFlow']

class QeBgwFlow(WfnBgwFlow):
    """
    A Workflow to compute wavefunctions with Quantum Espresso
    and convert them to BGW.
    The charge density can optionally be computed as a first step.
    """

    _charge_density_fname = ''
    _spin_polarization_fname = ''
    _data_file_fname = ''

    def __init__(self, **kwargs):
        """
        Keyword Arguments
        -----------------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.
        charge_density_fname : str
            Charge density file produced by a previous PW task.
        data_file_fname : str
            XML data file produced by a density calculation.
            Giving a file name will set default value of 'with_density' to False.
        spin_polarization_fname : str, optional
            Spin polarization file produced by a density calculation.
            Giving a file name will set default value of 'with_density' to False.
        prefix : str
            Prefix required by QE as a rootname.
        pseudo_dir : str
            Directory in which pseudopotential files are found.
        pseudos : list, str
            Pseudopotential files.
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ecutwfc : float
            Energy cutoff for the wavefunctions
        nbnd : int, optional
            Number of bands to be computed.
        ngkpt : list(3), float, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
            K-points are either specified using ngkpt or using kpts and wtks.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
        symkpt : bool (True), optional
            Use symmetries for the k-point grid generation.
        kpts : 2D list(nkpt,3), float, optional
            List of k-points.
            K-points are either specified using ngkpt or using kpts and wtks.
        wtks : list(nkpt), float, optional
            Weights of each k-point.

        See also:
            BGWpy.QE.QeWfnTask
            BGWpy.QE.Qe2BgwTask


        Properties
        ----------

        charge_density_fname : str
            Path to the charge density file used by QE.

        data_file_fname : str
            Path to the xml data file used by QE.

        spin_polarization_fname : str, optional
            Path to the spin polarization file used by QE.

        wfn_fname : str
            Path to the wavefunction file used by BerkeleyGW.

        rho_fname : str
            Path to the density file used by BerkeleyGW.

        vxc_dat_fname : str
            Path to the vxc.dat file used by BerkeleyGW.
        """

        super(QeBgwFlow, self).__init__(**kwargs)

        kwargs.pop('dirname', None)

        self.charge_density_fname = kwargs['charge_density_fname']
        self.data_file_fname = kwargs['data_file_fname']
        self.spin_polarization_fname = kwargs.get('spin_polarization_fname', 'dummy')

        # Wfn task
        self.wfntask = QeWfnTask(dirname = self.dirname, **kwargs)
        self.wfntask.runscript.fname = 'wfn.run.sh'
        self.add_task(self.wfntask, merge=False)

        # Wfn 2 BGW
        self.wfnbgwntask = Qe2BgwTask(
            dirname = self.wfntask.dirname,
            **kwargs)
        self.wfnbgwntask.runscript.fname = 'pw2bgw.run.sh'

        self.add_task(self.wfnbgwntask, merge=False)

    @property
    def charge_density_fname(self):
        """The charge density file used by QE."""
        return self._charge_density_fname

    @charge_density_fname.setter
    def charge_density_fname(self, value):
        self._charge_density_fname = value

    @property
    def spin_polarization_fname(self):
        """The spin polarization file used by QE."""
        return self._spin_polarization_fname

    @spin_polarization_fname.setter
    def spin_polarization_fname(self, value):
        self._spin_polarization_fname = value

    @property
    def data_file_fname(self):
        """The XML data file used by QE."""
        return self._data_file_fname

    @data_file_fname.setter
    def data_file_fname(self, value):
        self._data_file_fname = value


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
        raise NotImplementedError(
            'Please use vxc_dat_fname instead of vxc_fname.')

    @property
    def vxc_dat_fname(self):
        """The xc potential file name for BerkeleyGW."""
        return self.wfnbgwntask.vxc_dat_fname

