
from os.path import join as pjoin

from . import QeScfTask, QeWfnTask, Qe2BgwTask
from ..DFT import WfnBgwFlow

__all__ = ['QeBgwFlow']

class QeBgwFlow(WfnBgwFlow):

    _charge_density_fname = ''
    _spin_polarization_fname = ''
    _data_file_fname = ''

    def __init__(self, **kwargs):
        """

        Keyword Arguments
        -----------------

        with_density : bool (True)
            Include an SCF task to compute the ground state density.
        charge_density_fname : str
            Density file provided, so that the SCF task is not included.
            Giving a file name will set default value of 'with_density' to False.
        data_file_fname : str
            XML data file produced by a density calculation.
            Giving a file name will set default value of 'with_density' to False.
        spin_polarization_fname : str, optional
            Spin polarization file produced by a density calculation.
            Giving a file name will set default value of 'with_density' to False.

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

        scf_keys = ['charge_density_fname', 'data_file_fname', 'spin_polarization_fname']
        if any([key in kwargs for key in scf_keys]):
            kwargs.setdefault('with_density', False)

        self.with_density = kwargs.get('with_density', True)

        # SCF task
        if self.with_density:
            self.scftask = QeScfTask(
                dirname = kwargs.get('density_dirname',
                                     pjoin(self.dirname, '01-Density')),
                                     **kwargs)

            kwargs.setdefault('charge_density_fname',
                              self.scftask.charge_density_fname)

            kwargs.setdefault('data_file_fname',
                              self.scftask.data_file_fname)

            kwargs.setdefault('spin_polarization_fname',
                              self.scftask.spin_polarization_fname)

            self.add_task(self.scftask, merge=False)

        self.charge_density_fname = kwargs['charge_density_fname']
        self.data_file_fname = kwargs['data_file_fname']
        self.spin_polarization_fname = kwargs.get('spin_polarization_fname', 'dummy')

        # Wfn task
        self.wfntask = QeWfnTask(
            dirname = kwargs.get('wfn_dirname',
                                 pjoin(self.dirname, '02-Wavefunctions')),
                                 **kwargs)

        self.add_task(self.wfntask, merge=False)


        # Wfn 2 BGW
        self.wfbgwntask = Qe2BgwTask(
            dirname = self.wfntask.dirname,
            **kwargs)

        self.add_task(self.wfbgwntask, merge=False)

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
        return self.wfbgwntask.rho_fname

    @property
    def wfn_fname(self):
        """The wavefunctions file name for BerkeleyGW."""
        return self.wfbgwntask.wfn_fname

    @property
    def vxc_fname(self):
        raise NotImplementedError(
            'Please use vxc_dat_fname instead of vxc_fname.')

    @property
    def vxc_dat_fname(self):
        """The xc potential file name for BerkeleyGW."""
        return self.wfbgwntask.vxc_dat_fname

