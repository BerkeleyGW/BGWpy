from __future__ import print_function

from .bgwtask import BGWTask
from .kgrid   import get_kpt_grid
from .inputs  import AbsorptionInput

# Public
__all__ = ['AbsorptionTask']


class AbsorptionTask(BGWTask):
    """Absorption spectrum calculation."""

    _TASK_NAME = 'Absorption'
    _input_fname  = 'absorption.inp'
    _output_fname = 'absorption.out'

    def __init__(self, dirname, **kwargs):
        """
        Arguments
        ---------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.


        Keyword arguments
        -----------------
        (All mandatory unless specified otherwise)

        nbnd_val_co : int
            Number of valence bands on the coarse grid.
        nbnd_cond_co : int
            Number of conduction bands on the coarse grid.
        nbnd_val_fi : int
            Number of valence bands on the fine grid.
        nbnd_cond_fi : int
            Number of conduction bands on the fine grid.
        wfn_co_fname : str
            Path to the wavefunction file (coarse grid) produced by pw2bgw.
        wfn_fi_fname : str
            Path to the wavefunction file (fine grid) produced by pw2bgw.
        wfnq_fi_fname : str
            Path to the q-shifted wavefunction file (fine grid) produced by pw2bgw.
        eps0mat_fname : str
            Path to the eps0mat file produced by epsilon.
        epsmat_fname : str
            Path to the epsmat file produced by epsilon.
        bsemat_fname : str
            Path to the bsemat file produced by kernel.
        bsedmat_fname : str
            Path to the bsedmat file produced by kernel.
        bsexmat_fname : str
            Path to the bsexmat file produced by kernel.
        eqp_fname : str
            Path to either eqp0.dat or eqp1.dat file produced by sigma.
        extra_lines : list, optional
            Any other lines that should appear in the input file.
        extra_variables : dict, optional
            Any other variables that should be declared in the input file.

        """

        super(AbsorptionTask, self).__init__(dirname, **kwargs)

        # Input file
        self.input = AbsorptionInput(
            kwargs['nbnd_val_co'],
            kwargs['nbnd_cond_co'],
            kwargs['nbnd_val_fi'],
            kwargs['nbnd_cond_fi'],
            *kwargs.get('extra_lines',[]),
            **kwargs.get('extra_variables',{}))

        self.input.fname = self._input_fname

        # Run script
        self.wfn_co_fname = kwargs['wfn_co_fname']
        self.wfn_fi_fname = kwargs['wfn_fi_fname']
        self.wfnq_fi_fname = kwargs['wfnq_fi_fname']

        self.eps0mat_fname = kwargs['eps0mat_fname']
        self.epsmat_fname = kwargs['epsmat_fname']

        if 'bsemat_fname' in kwargs:
            self.bsemat_fname = kwargs['bsemat_fname']
        else:
            self.bsedmat_fname = kwargs['bsedmat_fname']
            self.bsexmat_fname = kwargs['bsexmat_fname']

        self.eqp_fname = kwargs['eqp_fname']

        ex = 'absorption.cplx.x' if self._flavor_complex else 'absorption.real.x'
        self.runscript['ABSORPTION'] = ex
        self.runscript.append('$MPIRUN $ABSORPTION &> {}'.format(self._output_fname))

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

    @property
    def wfnq_fi_fname(self):
        return self._wfn_fi_fname

    @wfnq_fi_fname.setter
    def wfnq_fi_fname(self, value):
        self._wfnq_fi_fname = value
        self.update_link(value, 'WFNq_fi')

    @property
    def eps0mat_fname(self):
        return self._eps0mat_fname

    @eps0mat_fname.setter
    def eps0mat_fname(self, value):
        self._eps0mat_fname = value
        dest = 'eps0mat.h5' if self._use_hdf5 else 'eps0mat'
        self.update_link(value, dest)

    @property
    def epsmat_fname(self):
        return self._epsmat_fname

    @epsmat_fname.setter
    def epsmat_fname(self, value):
        self._epsmat_fname = value
        dest = 'epsmat.h5' if self._use_hdf5 else 'epsmat'
        self.update_link(value, dest)

    @property
    def bsemat_fname(self):
        return self._bsemat_fname

    @bsemat_fname.setter
    def bsemat_fname(self, value):
        self._bsemat_fname = value
        dest = 'bsemat.h5' if self._use_hdf5 else 'bsemat'
        self.update_link(value, dest)

    @property
    def bsedmat_fname(self):
        return self._bsedmat_fname

    @bsedmat_fname.setter
    def bsedmat_fname(self, value):
        self._bsedmat_fname = value
        dest = 'bsedmat.h5' if self._use_hdf5 else 'bsedmat'
        self.update_link(value, dest)

    @property
    def bsexmat_fname(self):
        return self._bsexmat_fname

    @bsexmat_fname.setter
    def bsexmat_fname(self, value):
        self._bsexmat_fname = value
        dest = 'bsexmat.h5' if self._use_hdf5 else 'bsexmat'
        self.update_link(value, dest)

    @property
    def bsemat_fname(self):
        return self._bsemat_fname

    @bsemat_fname.setter
    def bsemat_fname(self, value):
        self._bsemat_fname = value
        dest = 'bsemat.h5' if self._use_hdf5 else 'bsemat'
        self.update_link(value, dest)

    @property
    def sigma_fname(self):
        return self._sigma_fname

    @sigma_fname.setter
    def sigma_fname(self, value):
        self._sigma_fname = value
        self.update_link(value, 'sigma_hp.log')

    @property
    def eqp_fname(self):
        return self._eqp_fname

    @eqp_fname.setter
    def eqp_fname(self, value):
        self._eqp_fname = value
        self.update_link(value, 'eqp_co.dat')

    def write(self):
        super(AbsorptionTask, self).write()
        with self.exec_from_dirname():
            self.input.write()

