
from collections import OrderedDict
from ..core import BasicInputFile
from .bgwtask import BGWTask

__all__ = ['IneqpInput', 'IneqpTask']

class IneqpInput(BasicInputFile):

    def __init__(self, *keywords, **variables):

        all_variables = OrderedDict([
            ('number_val_bands_coarse', 1),
            ('number_val_bands_fine', 1),
            ('number_cond_bands_coarse', 1),
            ('number_cond_bands_fine', 1),
            ])

        all_variables.update(variables)

        super(IneqpInput, self).__init__(all_variables, keywords)


class IneqpTask(BGWTask):

    _TASK_NAME = 'Inteqp task'
    _input_fname = 'inteqp.inp'
    _output_fname = 'inteqp.log'

    def __init__(self, dirname, **kwargs):

        super(IneqpTask, self).__init__(dirname, **kwargs)

        self.eqp_co_fname = kwargs['eqp_co_fname']
        self.wfn_co_fname = kwargs['wfn_co_fname']
        self.wfn_fi_fname = kwargs['wfn_fi_fname']

        self.input = IneqpInput(
            number_val_bands_coarse = kwargs.pop('number_val_bands_coarse', 1),
            number_val_bands_fine = kwargs.pop('number_val_bands_fine', 1),
            number_cond_bands_coarse = kwargs.pop('number_cond_bands_coarse', 1),
            number_cond_bands_fine = kwargs.pop('number_cond_bands_fine', 1),
            *kwargs.get('extra_lines',[]),
            **kwargs.get('extra_variables',{}))

        self.input.fname = self._input_fname

        ex = 'inteqp.cplx.x' if self._flavor_complex else 'inteqp.real.x'
        self.runscript['INTEQP'] = ex
        self.runscript.append('$MPIRUN $INTEQP &> {}'.format(self._output_fname))


    def write(self):
        super(IneqpTask, self).write()
        with self.exec_from_dirname():
            self.input.write()

    @property
    def eqp_co_fname(self):
        return self._eqp_co_fname

    @eqp_co_fname.setter
    def eqp_co_fname(self, value):
        self._eqp_co_fname = value
        self.update_link(value, 'eqp_co.dat')

    @property
    def wfn_co_fname(self):
        return self._wfn_co_fname

    @wfn_co_fname.setter
    def wfn_co_fname(self, value):
        self._wfn_co_fname = value
        self.update_link(value, 'WFN_co')

    @property
    def wfn_fi_fname(self):
        return self._wfn_fi_fname

    @wfn_fi_fname.setter
    def wfn_fi_fname(self, value):
        self._wfn_fi_fname = value
        self.update_link(value, 'WFN_fi')

