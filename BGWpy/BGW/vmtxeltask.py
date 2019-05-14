
from .bgwtask import BGWTask

__all__ = ['VmtxelTask']

class VmtxelTask(BGWTask):

    _TASK_NAME = 'Vmtxel'
    _input_fname  = '' #'vmtxel.inp'
    _output_fname = 'vmtxel.out'

    def __init__(self, dirname, **kwargs):
        """
        Dipole operator / velocity operator / momentum operator calculation

        Arguments
        ---------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.

        Mandatory Keyword arguments
        --------------------------

        wfn_fi_fname : str
            Path to the wavefunction file (fine grid) produced by pw2bgw.

        Optional Keyword arguments
        --------------------------

        wfnq_fi_fname : str
            Path to the q-shifted wavefunction file (fine grid) produced by pw2bgw.
        """

        super(VmtxelTask, self).__init__(dirname, **kwargs)

        # Run script
        self.wfn_fi_fname = kwargs['wfn_fi_fname']
        if 'wfnq_fi_fname' in kwargs:
            self.wfnq_fi_fname = kwargs['wfnq_fi_fname']

        ex = 'vmtxel.cplx.x' if self._flavor_complex else 'vmtxel.real.x'  # Gotta get rid of this boilerplate
        self.runscript['VMTXEL'] = ex
        self.runscript.append('$MPIRUN $VMTXEL &> {}'.format(self._output_fname))


    @property
    def wfn_fi_fname(self):
        return self._wfn_fi_fname

    @wfn_fi_fname.setter
    def wfn_fi_fname(self, value):
        self._wfn_fi_fname = value
        self.update_link(value, 'WFN_fi')

    @property
    def wfnq_fi_fname(self):
        return self._wfn_fi_fname

    @wfnq_fi_fname.setter
    def wfnq_fi_fname(self, value):
        self._wfnq_fi_fname = value
        self.update_link(value, 'WFNq_fi')


