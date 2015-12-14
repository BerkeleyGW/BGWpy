from __future__ import print_function
import os

from .abinittask import AbinitTask
from .constructor import get_kpt_variables, get_scf_variables

__all__ = ['AbinitScfTask']

class AbinitScfTask(AbinitTask):
    """Charge density calculation."""

    _TASK_NAME = 'SCF task'

    _input_fname = 'scf.in'
    _output_fname = 'scf.out'

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

        kwargs.setdefault('prefix', 'scf')

        super(AbinitScfTask, self).__init__(dirname, **kwargs)

        #self.input.set_structure(self.structure)
        #self.input.set_variables(get_kpt_variables(**kwargs))
        self.input.set_variables(get_scf_variables(**kwargs))
        self.input.set_variables(kwargs.get('input_variables', {}))

    @property
    def charge_density_fname(self):
        #return os.path.join(self.dirname, self.get_odat('DEN'))
        return self.get_odat('DEN')

    rho_fname = charge_density_fname

    @property
    def xc_potential_fname(self):
        #return os.path.join(self.dirname, self.get_odat('DEN'))
        return self.get_odat('VXC')

    vxc_fname = xc_potential_fname

