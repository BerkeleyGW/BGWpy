"""Workflow to perform BSE calculation."""
from os.path import join as pjoin
import warnings

from ..config import flavors
from ..config import is_dft_flavor_espresso, is_dft_flavor_abinit, check_dft_flavor
from ..external import Structure
from ..core import Workflow
from ..BGW import EpsilonTask, SigmaTask, KernelTask, AbsorptionTask

__all__ = ['BSEFlow']

class BSEFlow(Workflow):
    """
    A Flow of calculations made of the following tasks:
        - DFT charge density, wavefunctions and eigenvalues
        - Dielectric Matrix (Epsilon and Epsilon^-1)
        - Self-energy (Sigma)
        - Kernel
        - Absorption
    
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
        dft_flavor : 'espresso' | 'abinit'
            Choice of DFT code for density and wavefunctions calculations.
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
        nbnd_fine : int
            Number of bands to be computed on the fine grid for absorption.
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
        self.kshift = kwargs.pop('kshift', [.0,.0,.0])
        self.qshift = kwargs.pop('qshift')

        nband_aliases = ('nbnd', 'nband')
        for key in nband_aliases:
            if key in kwargs:
                self.nbnd = kwargs.pop(key)
                break
        else:
            raise Exception('Number of bands must be specified with one of these keywords: {}.'
                            .format(nband_aliases))

        # BSE parameters
        self.ngkpt_fi = kwargs.pop('ngkpt_fine', self.ngkpt)
        self.kshift_fi = kwargs.pop('kshift_fine', self.kshift)
        self.qshift_fi = kwargs.pop('qshift_fine', self.qshift)

        if 'nbnd_fine' not in kwargs:
            warnings.warn("'nbnd_fine' was not specified.\n" + 
                          "Thus, number of band computed on the fine grid will default to 'nbnd' (coarse grid).\n" +
                          "This is usually a waste and you might want to choose 'nbnd_fine' according to\n" +
                          "   nbnd_fine = nbnd_occupied + nbnd_cond_fi + 1.")
        self.nbnd_fine = kwargs.pop('nbnd_fine', self.nbnd)

        # ==== DFT calculations ==== #
        self.dft_flavor = check_dft_flavor(kwargs.get('dft_flavor', flavors['dft_flavor']))

        # Quantum Espresso flavor
        if is_dft_flavor_espresso(self.dft_flavor):
            fnames = self.make_dft_tasks_espresso(**kwargs)
            kwargs.update(fnames)

        # Abinit flavor
        elif is_dft_flavor_abinit(self.dft_flavor):
            fnames = self.make_dft_tasks_abinit(**kwargs)
            kwargs.update(fnames)
        
        # ==== BSE calculations ==== #

        # Dielectric matrix computation and inversion (epsilon)
        self.epsilontask = EpsilonTask(
            dirname = pjoin(self.dirname, '11-epsilon'),
            ngkpt = self.ngkpt,
            qshift = self.qshift,
            extra_lines = kwargs.pop('epsilon_extra_lines', []),
            extra_variables = kwargs.pop('epsilon_extra_variables', {}),
            **kwargs)
        
        # Self-energy calculation (sigma)
        self.sigmatask = SigmaTask(
            dirname = pjoin(self.dirname, '12-sigma'),
            ngkpt = self.ngkpt,
            extra_lines = kwargs.pop('sigma_extra_lines', []),
            extra_variables = kwargs.pop('sigma_extra_variables', {}),
            eps0mat_fname = self.epsilontask.eps0mat_fname,
            epsmat_fname = self.epsilontask.epsmat_fname,
            **kwargs)

        # Kernel calculation (BSE)
        self.kerneltask = KernelTask(
            dirname = pjoin(self.dirname, '13-kernel'),
            extra_lines = kwargs.pop('kernel_extra_lines', []),
            extra_variables = kwargs.pop('kernel_extra_variables', {}),
            eps0mat_fname = self.epsilontask.eps0mat_fname,
            epsmat_fname = self.epsilontask.epsmat_fname,
            **kwargs)

        # Absorption calculation (BSE)
        if AbsorptionTask._use_hdf5:
            kwargs['bsemat_fname'] = self.kerneltask.bsemat_fname
        else:
            kwargs['bsedmat_fname'] = self.kerneltask.bsedmat_fname
            kwargs['bsexmat_fname'] = self.kerneltask.bsexmat_fname

        self.absorptiontask = AbsorptionTask(
            dirname = pjoin(self.dirname, '14-absorption'),
            extra_lines = kwargs.get('absorption_extra_lines', []),
            extra_variables = kwargs.get('absorption_extra_variables', {}),

            eps0mat_fname = self.epsilontask.eps0mat_fname,
            epsmat_fname = self.epsilontask.epsmat_fname,
            eqp_fname = self.sigmatask.eqp1_fname,
            **kwargs)

        self.truncation_flag = kwargs.get('truncation_flag')

        # Add all tasks
        self.add_tasks([self.epsilontask, self.sigmatask,
                        self.kerneltask, self.absorptiontask], merge=False)

    @property
    def has_kshift(self):
        return any([i!=0 for i in self.kshift])

    _truncation_flag = ''
    @property
    def truncation_flag(self):
        return self._truncation_flag

    @truncation_flag.setter
    def truncation_flag(self, value):

        for task in (self.epsilontask, self.sigmatask,
                     self.kerneltask, self.absorptiontask):

            # Remove old value
            if self._truncation_flag in task.input.keywords:
                i = task.input.keywords.index(self._truncation_flag)
                del task.input.keywords[i]

            # Add new value
            if value:
                task.input.keywords.append(value)

        self._truncation_flag = value

    def make_dft_tasks_espresso(self, **kwargs):
        """
        Initialize all DFT tasks using Quantum Espresso.
        Return a dictionary of file names.
        """
        from ..QE import QeScfTask, QeBgwFlow

        if 'charge_density_fname' in kwargs:
            if 'data_file_fname' not in kwargs:
                raise Exception("Error, when providing charge_density_fname, data_file_fname is required.")

        else:

            self.scftask = QeScfTask(
                dirname = pjoin(self.dirname, '01-density'),
                ngkpt = self.ngkpt,
                kshift = self.kshift,
                **kwargs)

            self.add_task(self.scftask)
            
            kwargs.update(
                charge_density_fname = self.scftask.charge_density_fname,
                data_file_fname = self.scftask.data_file_fname,
                spin_polarization_fname = self.scftask.spin_polarization_fname)
        

        kwargs.update(
            charge_density_fname = self.scftask.charge_density_fname,
            data_file_fname = self.scftask.data_file_fname,
            spin_polarization_fname = self.scftask.spin_polarization_fname)
        
        # Wavefunction tasks for Epsilon
        self.wfntask_ksh = QeBgwFlow(
            dirname = pjoin(self.dirname, '02-wfn'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            nbnd = self.nbnd,
            rhog_flag = True,
            symkpt=False,
            **kwargs)

        self.wfntask_qsh = QeBgwFlow(
            dirname = pjoin(self.dirname, '03-wfnq'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            qshift = self.qshift,
            nbnd = None,
            symkpt=False,
            **kwargs)

        self.add_tasks([self.wfntask_ksh, self.wfntask_qsh])

        # Unshifted wavefunction tasks for Sigma
        # only if not already computed for Epsilon.
        if self.has_kshift:

            self.wfntask_ush = QeBgwFlow(
                dirname = pjoin(self.dirname, '04-wfn_co'),
                ngkpt = self.ngkpt,
                nbnd = self.nbnd,
                rhog_flag = True,
                symkpt=False,
                **kwargs)

            self.add_task(self.wfntask_ush)

        else:
            self.wfntask_ush = self.wfntask_ksh

        # Wavefunctions on fine k-point grids
        self.wfntask_fi_ush = QeBgwFlow(
            dirname = pjoin(self.dirname, '05-wfn_fi'),
            nbnd = self.nbnd_fine,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = 3*[.0],
            symkpt=False,
            **kwargs)
        
        self.wfntask_fi_qsh = QeBgwFlow(
            dirname = pjoin(self.dirname, '06-wfnq_fi'),
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = self.qshift_fi,
            symkpt=False,
            **kwargs)
        
        self.add_tasks([self.wfntask_fi_ush, self.wfntask_fi_qsh])

        fnames = dict(wfn_fname = self.wfntask_ksh.wfn_fname,
                      wfnq_fname = self.wfntask_qsh.wfn_fname,
                      wfn_co_fname = self.wfntask_ush.wfn_fname,
                      rho_fname = self.wfntask_ush.rho_fname,
                      vxc_dat_fname = self.wfntask_ush.vxc_dat_fname,
                      wfn_fi_fname = self.wfntask_fi_ush.wfn_fname,
                      wfnq_fi_fname = self.wfntask_fi_qsh.wfn_fname)

        return fnames

    def make_dft_tasks_abinit(self, **kwargs):
        """
        Initialize all DFT tasks using Abinit.
        Return a dictionary of file names.
        """
        from ..Abinit import AbinitScfTask, AbinitBgwFlow

        # Either charge density is provided or an SCF task is initialized.
        if 'charge_density_fname' in kwargs:
            if 'vxc_fname' not in kwargs:
                raise Exception("Error, when providing charge_density_fname, vxc_fname is required")

        else:
            self.scftask = AbinitScfTask(
                dirname = pjoin(self.dirname, '01-density'),
                ngkpt = self.ngkpt,
                kshift = self.kshift,
                **kwargs)

            self.add_task(self.scftask)
            
            kwargs.update(
                charge_density_fname = self.scftask.charge_density_fname,
                vxc_fname = self.scftask.vxc_fname)

        # Wavefunction tasks for Epsilon
        self.wfntask_ksh = AbinitBgwFlow(
            dirname = pjoin(self.dirname, '02-wfn'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            nband = self.nbnd,
            rhog_flag = True,
            **kwargs)
        
        self.wfntask_qsh = AbinitBgwFlow(
            dirname = pjoin(self.dirname, '03-wfnq'),
            ngkpt = self.ngkpt,
            kshift = self.kshift,
            qshift = self.qshift,
            nband = None,
            **kwargs)
        
        self.add_tasks([self.wfntask_ksh, self.wfntask_qsh])

        # Unshifted wavefunction tasks for Sigma
        # only if not already computed for Epsilon.
        if self.has_kshift:

            self.wfntask_ush = AbinitBgwFlow(
                dirname = pjoin(self.dirname, '04-wfn_co'),
                ngkpt = self.ngkpt,
                nband = self.nbnd,
                rhog_flag = True,
                vxcg_flag = True,
                **kwargs)

            self.add_task(self.wfntask_ush)

        else:
            self.wfntask_ush = self.wfntask_ksh

        # Wavefunctions on fine k-point grids
        self.wfntask_fi_ush = AbinitBgwFlow(
            dirname = pjoin(self.dirname, '05-wfn_fi'),
            nband = self.nbnd_fine,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = 3*[.0],
            symkpt=False,
            **kwargs)
        
        self.wfntask_fi_qsh = AbinitBgwFlow(
            dirname = pjoin(self.dirname, '06-wfnq_fi'),
            nband = None,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = self.qshift_fi,
            symkpt=False,
            **kwargs)
        
        self.add_tasks([self.wfntask_fi_ush, self.wfntask_fi_qsh])

        fnames = dict(wfn_fname = self.wfntask_ksh.wfn_fname,
                      wfnq_fname = self.wfntask_qsh.wfn_fname,
                      wfn_co_fname = self.wfntask_ush.wfn_fname,
                      rho_fname = self.wfntask_ush.rho_fname,
                      vxc_fname = self.wfntask_ush.vxc_fname,
                      wfn_fi_fname = self.wfntask_fi_ush.wfn_fname,
                      wfnq_fi_fname = self.wfntask_fi_qsh.wfn_fname)

        return fnames
