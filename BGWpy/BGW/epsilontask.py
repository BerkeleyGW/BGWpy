from __future__ import print_function
import os

from .bgwtask import BGWTask
from .kgrid   import KgridTask, get_kpt_grid
from .inputs  import EpsilonInput

# Public
__all__ = ['EpsilonTask']


class EpsilonTask(BGWTask):
    """Inverse dielectric function calculation."""

    _TASK_NAME = 'Epsilon'
    _input_fname  = 'epsilon.inp'
    _output_fname = 'epsilon.out'

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

        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ngkpt : list(3), float
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice. This is actually a Q-points grid
            in a GW calculation.
        qshift : list(3), float
            Q-point used to treat the Gamma point.
        ecuteps : float
            Energy cutoff for the dielectric function.
        wfn_fname : str
            Path to the wavefunction file produced by pw2bgw.
        wfnq_fname : str
            Path to the q-shifted wavefunction file produced by pw2bgw.
        extra_lines : list, optional
            Any other lines that should appear in the input file.
        extra_variables : dict, optional
            Any other variables that should be declared in the input file.


        Properties
        ----------

        eps0mat_fname : str
            Path to the eps0mat file produced.
        eps0mat_h5_fname : str
            Path to the eps0mat.h5 file produced.
        epsmat_fname : str
            Path to the epsmat file produced.
        epsmat_h5_fname : str
            Path to the epsmat.h5 file produced.

        """

        super(EpsilonTask, self).__init__(dirname, **kwargs)

        # Compute k-points grids
        # TODO maybe make these properties
        #structure = kwargs['structure']
        #ngkpt = kwargs['ngkpt']
        #kpts_ush, wtks_ush = get_kpt_grid(structure, ngkpt)
        kgrid_kwargs = dict()
        for key in ('structure', 'ngkpt', 'fft', 'use_tr', 'clean_after'):
            if key in kwargs:
                kgrid_kwargs[key] = kwargs[key]
        self.kgridtask = KgridTask(dirname=dirname, **kgrid_kwargs)

        symkpt = kwargs.get('symkpt', True)
        if symkpt:
            kpts_ush, wtks_ush = self.kgridtask.get_kpoints()
        else:
            kpts_ush, wtks_ush = self.kgridtask.get_kpt_grid_nosym()

        extra_lines = kwargs.get('extra_lines',[])
        extra_variables = kwargs.get('extra_variables',{})

        # Input file
        self.input = EpsilonInput(
            kwargs['ecuteps'],
            kwargs['qshift'],
            kpts_ush[1:],
            *extra_lines,
            **extra_variables)

        self.input.fname = self._input_fname

        # Set up the run script
        self.wfn_fname = kwargs['wfn_fname']
        self.wfnq_fname = kwargs['wfnq_fname']

        ex = 'epsilon.cplx.x' if self._flavor_complex else 'epsilon.real.x'
        self.runscript['EPSILON'] = ex
        self.runscript.append('$MPIRUN $EPSILON &> {}'.format(self._output_fname))

    @property
    def wfn_fname(self):
        return self._wfn_fname

    @wfn_fname.setter
    def wfn_fname(self, value):
        self._wfn_fname = value
        self.update_link(value, 'WFN')

    @property
    def wfnq_fname(self):
        return self._wfnq_fname

    @wfnq_fname.setter
    def wfnq_fname(self, value):
        self._wfnq_fname = value
        self.update_link(value, 'WFNq')

    def write(self):
        super(EpsilonTask, self).write()
        with self.exec_from_dirname():
            self.input.write()

    @property
    def eps0mat_fname(self):
        # Eventually, hdf5 will be mandatory.
        basename = 'eps0mat.h5' if self._use_hdf5 else 'eps0mat'
        return os.path.join(self.dirname, basename)
    
    @property
    def epsmat_fname(self):
        basename = 'epsmat.h5' if self._use_hdf5 else 'epsmat'
        return os.path.join(self.dirname, basename)
    
