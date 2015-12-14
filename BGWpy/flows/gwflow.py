from __future__ import print_function

from os.path import join as pjoin

from ..external import Structure
from ..core import Workflow
from ..QE import ScfTask, WfnTask, PW2BGWTask
from ..BGW import EpsilonTask, SigmaTask

__all__ = ['GWFlow']

class GWFlow(Workflow):
    """
    A one-shot GW workflow made of the following tasks:
        DFT charge density, wavefunctions and eigenvalues
        Dielectric Matrix (Epsilon and Epsilon^-1)
        Self-energy (Sigma)
    """

    def __init__(self, **kwargs):
        """
        Keyword arguments
        -----------------
        (All mandatory unless specified otherwise)

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        prefix : str
            Prefix required by QE as a rootname.
        pseudo_dir : str
            Directory in which pseudopotential files are found.
        pseudos : list, str
            Pseudopotential files.
        ngkpt : list(3), float
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float
            Q-point used to treat the Gamma point.
        nbnd : int
            Number of bands to be computed.
        ecutwfc : float
            Energy cutoff for the wavefunctions
        ecuteps : float
            Energy cutoff for the dielectric function.
        ibnd_min : int
            Minimum band index for GW corrections.
        ibnd_max : int
            Maximum band index for GW corrections.
        epsilon_extra_lines : list, optional
            Any other lines that should appear in the epsilon input file.
        epsilon_extra_variables : dict, optional
            Any other variables that should be declared in the epsilon input file.
        sigma_extra_lines : list, optional
            Any other lines that should appear in the sigma input file.
        sigma_extra_variables : dict, optional
            Any other variables that should be declared in the sigma input file.

        """

        super(GWFlow, self).__init__(**kwargs)

        kwargs.pop('dirname', None)

        self.structure = kwargs['structure']
        self.ngkpt = kwargs.pop('ngkpt')
        self.kshift = kwargs.pop('kshift')
        self.qshift = kwargs.pop('qshift')
        self.nbnd = kwargs.pop('nbnd')

        # Ground state density calculation (SCF)
        self.scftask = ScfTask(
            dirname = pjoin(self.dirname, '01-density'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            **kwargs)
        
        # Wavefunctions and eigenvalues calculation (NSCF) on a k-shifted grid
        self.wfntask_ksh = WfnTask(
            dirname = pjoin(self.dirname, '02-wfn'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            nbnd = self.nbnd,
            charge_density_fname = self.scftask.charge_density_fname,
            data_file_fname = self.scftask.data_file_fname,
            **kwargs)
        
        
        # Interfacing PW with BerkeleyGW.
        self.pw2bgwtask_ksh = PW2BGWTask(
            dirname = self.wfntask_ksh.dirname,
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            wfn_fname = 'wfn.cplx',
            **kwargs)
        
        
        # Wavefunctions and eigenvalues calculation (NSCF) on a k+q-shifted grid
        self.wfntask_qsh = WfnTask(
            dirname = pjoin(self.dirname, '03-wfnq'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            qshift = self.qshift,
            nbnd = None,
            charge_density_fname = self.scftask.charge_density_fname,
            data_file_fname = self.scftask.data_file_fname,
            **kwargs)
        
        
        # Interfacing PW with BerkeleyGW.
        self.pw2bgwtask_qsh = PW2BGWTask(
            dirname = self.wfntask_qsh.dirname,
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            qshift = self.qshift,
            wfn_fname = 'wfnq.cplx',
            **kwargs)
        
        
        # Wavefunctions and eigenvalues calculation (NSCF) on an unshifted grid
        self.wfntask_ush = WfnTask(
            dirname = pjoin(self.dirname, '04-wfn_co'),
            ngkpt = self.ngkpt,
            nbnd = self.nbnd,
            charge_density_fname = self.scftask.charge_density_fname,
            data_file_fname = self.scftask.data_file_fname,
            **kwargs)
        
        
        # Interfacing PW with BerkeleyGW.
        self.pw2bgwtask_ush = PW2BGWTask(
            dirname = self.wfntask_ush.dirname,
            ngkpt = self.ngkpt,
            wfn_fname = 'wfn_co.cplx',
            rho_fname = 'rho.real',
            vxc_diag_nmax = kwargs.pop('vxc_diag_nmax', self.nbnd-1),
            **kwargs)
        
        
        # Dielectric matrix computation and inversion (epsilon)
        self.epsilontask = EpsilonTask(
            dirname = pjoin(self.dirname, '05-epsilon'),
            ngkpt = self.ngkpt,
            qshift = self.qshift,
            extra_lines = kwargs.pop('epsilon_extra_lines', []),
            extra_variables = kwargs.pop('epsilon_extra_variables', {}),
            wfn_fname = self.pw2bgwtask_ksh.wfn_fname,
            wfnq_fname = self.pw2bgwtask_qsh.wfn_fname,
            **kwargs)
        
        
        # Self-energy calculation (sigma)
        self.sigmatask = SigmaTask(
            dirname = pjoin(self.dirname, '06-sigma'),
            ngkpt = self.ngkpt,
            extra_lines = kwargs.pop('sigma_extra_lines', []),
            extra_variables = kwargs.pop('sigma_extra_variables', {}),
            wfn_co_fname = self.pw2bgwtask_ush.wfn_fname,
            rho_fname = self.pw2bgwtask_ush.rho_fname,
            vxc_dat_fname = self.pw2bgwtask_ush.vxc_fname,
            eps0mat_fname = self.epsilontask.eps0mat_fname,
            epsmat_fname = self.epsilontask.epsmat_fname,
            **kwargs)
        
        
        # Add all task without merging (executed from a sub-directory)
        self.add_tasks([self.scftask,
                        self.wfntask_ksh, self.pw2bgwtask_ksh,
                        self.wfntask_qsh, self.pw2bgwtask_qsh,
                        self.wfntask_ush, self.pw2bgwtask_ush,
                        self.epsilontask, self.sigmatask],
                        merge=False)

