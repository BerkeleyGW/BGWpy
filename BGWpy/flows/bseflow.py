""" """
import os
from os.path import join as pjoin
import subprocess
import pickle


from ..external import Structure
from ..core import Workflow
from ..QE import ScfTask, WfnTask, PW2BGWTask
from ..BGW import EpsilonTask, SigmaTask, KernelTask, AbsorptionTask

__all__ = ['BSEFlow']

class BSEFlow(Workflow):
    """
    A Flow of calculations made of the following tasks:
        DFT charge density, wavefunctions and eigenvalues
        Dielectric Matrix (Epsilon and Epsilon^-1)
        Self-energy (Sigma)
        Kernel
        Absorption
    
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
        ngkpt_fine : list(3), float
            Fine K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift_fine : list(3), float, optional
            Relative shift of the fine k-points grid along each direction,
            as a fraction of the smallest division along that direction.
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
        nbnd_val : int
            Number of valence bands in kernel.
        nbnd_cond : int
            Number of conduction bands in kernel.
        nbnd_val_co : int
            Number of valence bands on the coarse grid.
        nbnd_cond_co : int
            Number of conduction bands on the coarse grid.
        nbnd_val_fi : int
            Number of valence bands on the fine grid.
        nbnd_cond_fi : int
            Number of conduction bands on the fine grid.
        nbnd_absorption : int
            Number of bands to be computed for absorption.
        epsilon_extra_lines : list, optional
            Any other lines that should appear in the epsilon input file.
        epsilon_extra_variables : dict, optional
            Any other variables that should be declared in the epsilon input file.
        sigma_extra_lines : list, optional
            Any other lines that should appear in the sigma input file.
        sigma_extra_variables : dict, optional
            Any other variables that should be declared in the sigma input file.
        kernel_extra_lines : list, optional
            Any other lines that should appear in the kernel input file.
        kernel_extra_variables : dict, optional
            Any other variables that should be declared in the kernel input file.
        absorption_extra_lines : list, optional
            Any other lines that should appear in the absorption input file.
        absorption_extra_variables : dict, optional
            Any other variables that should be declared in the absorption input file.

        """

        super(BSEFlow, self).__init__(**kwargs)

        kwargs.pop('dirname')

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
            vxc_fname = self.pw2bgwtask_ush.vxc_fname,
            eps0mat_fname = self.epsilontask.eps0mat_fname,
            epsmat_fname = self.epsilontask.epsmat_fname,
            **kwargs)


        # Kernel calculation (BSE)
        self.kerneltask = KernelTask(
            dirname = pjoin(self.dirname, '07-kernel'),
            extra_lines = kwargs.pop('kernel_extra_lines', []),
            extra_variables = kwargs.pop('kernel_extra_variables', {}),
            wfn_co_fname = self.pw2bgwtask_ush.wfn_fname,
            eps0mat_fname = self.epsilontask.eps0mat_fname,
            epsmat_fname = self.epsilontask.epsmat_fname,
            **kwargs)


        # BSE parameters
        self.ngkpt_fi = kwargs.pop('ngkpt_fine', self.ngkpt)
        self.kshift_fi = kwargs.pop('kshift_fine', self.kshift)
        self.qshift_fi = kwargs.pop('qshift_fine', self.qshift)
        self.nbnd_absorption = kwargs.pop('nbnd_absorption', self.nbnd)


        # Wavefunctions and eigenvalues calculation (NSCF)
        # on an finer, unshifted grid
        self.wfntask_fi_ush = WfnTask(
            dirname = pjoin(self.dirname, '08-wfn_fi'),
            nbnd = self.nbnd_absorption,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = 3*[.0],
            symkpt=False,
            charge_density_fname = self.scftask.charge_density_fname,
            data_file_fname = self.scftask.data_file_fname,
            **kwargs)
        
        
        # Interfacing PW with BerkeleyGW.
        self.pw2bgwtask_fi_ush = PW2BGWTask(
            dirname = self.wfntask_fi_ush.dirname,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = 3*[.0],
            wfn_fname = 'wfn_fi.cplx',
            **kwargs)
        
        # Wavefunctions and eigenvalues calculation (NSCF)
        # on an finer, q-shifted grid
        self.wfntask_fi_qsh = WfnTask(
            dirname = pjoin(self.dirname, '09-wfnq_fi'),
            nbnd = self.nbnd_absorption,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = self.qshift_fi,
            symkpt=False,
            charge_density_fname = self.scftask.charge_density_fname,
            data_file_fname = self.scftask.data_file_fname,
            **kwargs)
        
        
        # Interfacing PW with BerkeleyGW.
        self.pw2bgwtask_fi_qsh = PW2BGWTask(
            dirname = self.wfntask_fi_qsh.dirname,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = self.qshift_fi,
            wfn_fname = 'wfnq_fi.cplx',
            **kwargs)

        # Absorption calculation (BSE)
        self.absorptiontask = AbsorptionTask(
            dirname = pjoin(self.dirname, '10-absorption'),
            extra_lines = kwargs.get('absorption_extra_lines', []),
            extra_variables = kwargs.get('absorption_extra_variables', {}),

            wfn_co_fname = self.pw2bgwtask_ush.wfn_fname,
            wfn_fi_fname = self.pw2bgwtask_fi_ush.wfn_fname,
            wfnq_fi_fname = self.pw2bgwtask_fi_qsh.wfn_fname,

            eps0mat_fname = self.epsilontask.eps0mat_fname,
            epsmat_fname = self.epsilontask.epsmat_fname,
            bsedmat_fname = self.kerneltask.bsedmat_fname,
            bsexmat_fname = self.kerneltask.bsexmat_fname,
            sigma_fname = self.sigmatask.sigma_fname,
            eqp_fname = self.sigmatask.eqp1_fname,
            **kwargs)


        # Add all tasks
        self.add_tasks([self.scftask,
                        self.wfntask_ksh, self.pw2bgwtask_ksh,
                        self.wfntask_qsh, self.pw2bgwtask_qsh,
                        self.wfntask_ush, self.pw2bgwtask_ush,
                        self.epsilontask, self.sigmatask,
                        self.kerneltask,
                        self.wfntask_fi_ush, self.pw2bgwtask_fi_ush,
                        self.wfntask_fi_qsh, self.pw2bgwtask_fi_qsh,
                        self.absorptiontask, 
                        ],
                        merge=False, # Execute from their own directory
                        )

