from __future__ import print_function
import os

from ..core import Task, MPITask
from . import get_kpt_grid
from . import SigmaInput


class SigmaTask(MPITask):
    """Self-energy calculation."""

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
            of the reciprocal lattice.
        qshift : list(3), float
            Q-point used to treat the Gamma point.
        nbnd : int
            Number of bands included in the calculation.
        nbnd_occ : int
            Number of occupied bands.
        ecuteps : float
            Energy cutoff for the dielectric function.
        ecutsigx : float
            Energy cutoff for the bare coulomb interaction (exchange part).
        ibnd_min : int
            Minimum band index for GW corrections.
        ibnd_max : int
            Maximum band index for GW corrections.
        wfn_co_fname : str
            Path to the wavefunction file produced by pw2bgw.
        rho_fname : str
            Path to the density file produced by pw2bgw.
        vxc_fname : str
            Path to the vxc file produced by pw2bgw.
        eps0mat_fname : str
            Path to the eps0mat file produced by epsilon.
        epsmat_fname : str
            Path to the epsmat file produced by epsilon.
        extra_lines : list, optional
            Any other lines that should appear in the input file.
        extra_variables : dict, optional
            Any other variables that should be declared in the input file.


        Properties
        ----------

        sigma_fname : str
            Path to the sigma_hp.log file produced.

        """

        super(SigmaTask, self).__init__(dirname, **kwargs)

        # Compute k-points grids
        # TODO maybe make these properties
        structure = kwargs.pop('structure')
        ngkpt = kwargs['ngkpt']
        kpts_ush, wtks_ush = get_kpt_grid(structure, ngkpt)

        # Input file
        self.input = SigmaInput(
            kwargs['ecuteps'],
            kwargs['ecutsigx'],
            kwargs['nbnd'],
            kwargs['nbnd_occ'],
            kwargs['ibnd_min'],
            kwargs['ibnd_max'],
            kpts_ush,
            *kwargs.get('extra_lines',[]),
            **kwargs.get('extra_variables',{}))

        self.input.fname = 'sigma.inp'

        # Set up the run script
        self.wfn_co_fname = kwargs['wfn_co_fname']
        self.rho_fname = kwargs['rho_fname']
        self.vxc_fname = kwargs['vxc_fname']
        self.eps0mat_fname = kwargs['eps0mat_fname']
        self.epsmat_fname = kwargs['epsmat_fname']

        self.runscript['SIGMA'] = 'sigma.cplx.x'
        self.runscript['SIGMAOUT'] = 'sigma.out'
        self.runscript.append('$MPIRUN $SIGMA &> $SIGMAOUT')

    @property
    def wfn_co_fname(self):
        return self._wfn_co_fname

    @wfn_co_fname.setter
    def wfn_co_fname(self, value):
        self._wfn_co_fname = value
        self.update_link(value, 'WFN_inner')

    @property
    def rho_fname(self):
        return self._rho_fname

    @rho_fname.setter
    def rho_fname(self, value):
        self._rho_fname = value
        self.update_link(value, 'RHO')

    @property
    def vxc_fname(self):
        return self._vxc_fname

    @vxc_fname.setter
    def vxc_fname(self, value):
        self._vxc_fname = value
        self.update_link(value, 'vxc.dat')

    @property
    def eps0mat_fname(self):
        return self._eps0mat_fname

    @eps0mat_fname.setter
    def eps0mat_fname(self, value):
        self._eps0mat_fname = value
        dest = 'eps0mat'
        if value.endswith('.h5'):
            dest += '.h5'
        self.update_link(value, dest)

    @property
    def epsmat_fname(self):
        return self._epsmat_fname

    @epsmat_fname.setter
    def epsmat_fname(self, value):
        self._epsmat_fname = value
        dest = 'epsmat'
        if value.endswith('.h5'):
            dest += '.h5'
        self.update_link(value, dest)

    def write(self):
        super(SigmaTask, self).write()
        with self.exec_from_dirname():
            self.input.write()

    @property
    def sigma_fname(self):
        return os.path.join(self.dirname, 'sigma_hp.log')
    
