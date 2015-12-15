from __future__ import print_function

from os.path import join as pjoin

from ..external import Structure
from ..core import Workflow
from ..QE import QeScfTask, QeWfnTask, Qe2BgwTask
from ..BGW import EpsilonTask, SigmaTask

__all__ = ['GWFlowSemicond']

class GWFlowSemicond(Workflow):
    """
    A one-shot GW workflow, suitable for semiconductors, made of the
    following tasks:
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
        truncation_flag : str, optional
            Which truncation flag to use in BerkeleyGW, e.g. "cell_slab_truncation".
        sigma_kpts : list of list(3), optional
            K-points to evaluate self-energy operator. Defaults to all
            k-points defined by the Monkhorst-Pack grid ngkpt.
        epsilon_extra_lines : list, optional
            Any other lines that should appear in the epsilon input file.
        epsilon_extra_variables : dict, optional
            Any other variables that should be declared in the epsilon input file.
        sigma_extra_lines : list, optional
            Any other lines that should appear in the sigma input file.
        sigma_extra_variables : dict, optional
            Any other variables that should be declared in the sigma input file.

        """

        super(GWFlowSemicond, self).__init__(**kwargs)

        kwargs.pop('dirname')

        self.structure = kwargs['structure']
        self.ngkpt = kwargs.pop('ngkpt')
        self.kshift = kwargs.pop('kshift', [0., 0., 0.,])
        has_kshift = any([i!=0 for i in self.kshift])
        self.qshift = kwargs.pop('qshift')
        self.nbnd = kwargs.pop('nbnd')
        self.truncation_flag = kwargs.pop('truncation_flag', '')
        self.sigma_kpts = kwargs.pop('sigma_kpts', None)

        # Ground state density calculation (SCF)
        self.scftask = QeScfTask(
            dirname = pjoin(self.dirname, '1-mf/1-scf'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            **kwargs)
        
        # Wavefunctions and eigenvalues calculation (NSCF) on a k-shifted grid
        self.wfntask_ksh = QeWfnTask(
            dirname = pjoin(self.dirname, '1-mf/2.1-wfn'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            nbnd = self.nbnd,
            charge_density_fname = self.scftask.charge_density_fname,
            data_file_fname = self.scftask.data_file_fname,
            **kwargs)
        
        
        # Interfacing PW with BerkeleyGW.
        self.pw2bgwtask_ksh = Qe2BgwTask(
            dirname = self.wfntask_ksh.dirname,
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            wfn_fname = 'WFN',
            rho_fname = 'RHO',
            vxc_diag_nmax = kwargs.pop('vxc_diag_nmax', self.nbnd-1),
            **kwargs)
        
        
        # Wavefunctions and eigenvalues calculation (NSCF) on a k+q-shifted grid
        self.wfntask_qsh = QeWfnTask(
            dirname = pjoin(self.dirname, '1-mf/2.2-wfnq'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            qshift = self.qshift,
            nbnd = self.nbnd,
            charge_density_fname = self.scftask.charge_density_fname,
            data_file_fname = self.scftask.data_file_fname,
            **kwargs)
        # WFNq only need valence states, so we delete the nbnd input keyword
        del self.wfntask_qsh.input.system['nbnd']
        
        
        # Interfacing PW with BerkeleyGW.
        self.pw2bgwtask_qsh = Qe2BgwTask(
            dirname = self.wfntask_qsh.dirname,
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            qshift = self.qshift,
            wfn_fname = 'WFNq',
            **kwargs)
       
        # If kshift==[0,0,0], WFN==WFN_co and we can skip these tasks
        if has_kshift:
            # Wavefunctions and eigenvalues calculation (NSCF) on an unshifted grid
            self.wfntask_ush = QeWfnTask(
                dirname = pjoin(self.dirname, '3-wfn_co'),
                ngkpt = self.ngkpt,
                nbnd = self.nbnd,
                charge_density_fname = self.scftask.charge_density_fname,
                data_file_fname = self.scftask.data_file_fname,
                **kwargs)
        
            # Interfacing PW with BerkeleyGW.
            self.pw2bgwtask_ush = Qe2BgwTask(
                dirname = self.wfntask_ush.dirname,
                ngkpt = self.ngkpt,
                wfn_fname = 'WFN',
                rho_fname = 'RHO',
                vxc_diag_nmax = kwargs.pop('vxc_diag_nmax', self.nbnd-1),
                **kwargs)

            sigma_src_task = self.pw2bgwtask_ush
        else:
            sigma_src_task = self.pw2bgwtask_ksh
        
        
        # Dielectric matrix computation and inversion (epsilon)
        self.epsilontask = EpsilonTask(
            dirname = pjoin(self.dirname, '2-bgw/1-epsilon'),
            ngkpt = self.ngkpt,
            qshift = self.qshift,
            extra_lines = (kwargs.pop('epsilon_extra_lines', [])
                           + [self.truncation_flag]),
            extra_variables = kwargs.pop('epsilon_extra_variables', {}),
            wfn_fname = self.pw2bgwtask_ksh.wfn_fname,
            wfnq_fname = self.pw2bgwtask_qsh.wfn_fname,
            **kwargs)
        
        
        # Self-energy calculation (sigma)
        self.sigmatask = SigmaTask(
            dirname = pjoin(self.dirname, '2-bgw/2-sigma'),
            ngkpt = self.ngkpt,
            extra_lines = (kwargs.pop('sigma_extra_lines', [])
                           + [self.truncation_flag]),
            extra_variables = kwargs.pop('sigma_extra_variables', {}),
            wfn_co_fname = sigma_src_task.wfn_fname,
            rho_fname = sigma_src_task.rho_fname,
            vxc_fname = sigma_src_task.vxc_fname,
            eps0mat_fname = self.epsilontask.eps0mat_fname,
            epsmat_fname = self.epsilontask.epsmat_fname,
            **kwargs)

        # Manually set k-points for Sigma calculation, if requested
        if self.sigma_kpts is None:
            self.sigma_kpts = self.sigmatask.input.kpts
        else:
            self.sigmatask.input.kpts = self.sigma_kpts
        
        # Add all task without merging (executed from a sub-directory)
        tasks = [self.scftask,
                 self.wfntask_ksh, self.pw2bgwtask_ksh,
                 self.wfntask_qsh, self.pw2bgwtask_qsh]
        if has_kshift:
            tasks += [self.wfntask_ush, self.pw2bgwtask_ush]
        tasks += [self.epsilontask, self.sigmatask]
        self.add_tasks(tasks, merge=False)
