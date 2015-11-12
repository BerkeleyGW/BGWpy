from __future__ import print_function
import os

from ..core import Task, MPITask
from . import get_kpt_grid
from . import EpsilonInput


class EpsilonTask(MPITask):
    """Inverse dielectric function calculation."""

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
        nbnd : int
            Number of bands included in the calculation.
        nbnd_occ : int
            Number of occupied bands.
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
        structure = kwargs['structure']
        ngkpt = kwargs['ngkpt']
        kpts_ush, wtks_ush = get_kpt_grid(structure, ngkpt)

        # Input file
        self.input = EpsilonInput(
            kwargs['ecuteps'],
            kwargs['nbnd'],
            kwargs['nbnd_occ'],
            kwargs['qshift'],
            kpts_ush[1:],
            *kwargs.get('extra_lines',[]),
            **kwargs.get('extra_variables',{}))

        self.input.fname = 'epsilon.inp'

        # Set up the run script
        self.wfn_fname = kwargs['wfn_fname']
        self.wfnq_fname = kwargs['wfnq_fname']

        self.runscript['EPSILON'] = 'epsilon.cplx.x'
        self.runscript['EPSILONOUT'] = 'epsilon.out'
        self.runscript.append('$MPIRUN $EPSILON &> $EPSILONOUT')

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
        return os.path.join(self.dirname, 'eps0mat')
    
    @property
    def eps0mat_h5_fname(self):
        return os.path.join(self.dirname, 'eps0mat.h5')
    
    @property
    def epsmat_fname(self):
        return os.path.join(self.dirname, 'epsmat')
    
    @property
    def epsmat_h5_fname(self):
        return os.path.join(self.dirname, 'epsmat.h5')
    
