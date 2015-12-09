from __future__ import print_function
import os

from .abinittask import AbinitTask
from .constructor import get_kpt_variables, get_wfn_variables

__all__ = ['AbinitWfnTask']

class AbinitWfnTask(AbinitTask):
    """Charge density calculation."""

    _TASK_NAME = 'Wavefunction task'

    _input_fname = 'wfn.in'
    _output_fname = 'wfn.out'

    def __init__(self, dirname, **kwargs):
        """
        Arguments
        ---------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.

        input_variables : dict
            Any other input variables for the Abinit input file.

        """
        # TODO complete documentation.

        kwargs.setdefault('prefix', 'wfn')

        super(AbinitWfnTask, self).__init__(dirname, **kwargs)

        #self.input.set_structure(self.structure)
        #self.input.set_variables(get_kpt_variables(**kwargs))
        self.input.set_variables(get_wfn_variables(**kwargs))
        self.input.set_variables(kwargs.get('input_variables', {}))

        self.charge_density_fname = kwargs['charge_density_fname']

    @property
    def wavefunction_fname(self):
        return self.get_odat('WFK')

    wfn_fname = wavefunction_fname
    wfk_fname = wavefunction_fname

    @property
    def charge_density_fname(self):
        return self.get_odat('DEN')

    @charge_density_fname.setter
    def charge_density_fname(self, value):
        self._charge_density_fname = value
        dest = os.path.relpath(self.get_idat('DEN'), self.dirname)
        self.update_link(value, dest)

    rho_fname = charge_density_fname

    @property
    def exchange_correlation_potential_fname(self):
        #return os.path.join(self.dirname, self.get_odat('VXC'))
        return self.get_odat('VXC')

    vxc_fname = exchange_correlation_potential_fname

