"""Workflow to perform GW calculation."""
from __future__ import print_function

from os.path import join as pjoin

from ..config import dft_flavor, check_dft_flavor
from ..config import is_dft_flavor_espresso, is_dft_flavor_abinit
from ..external import Structure
from ..core import Workflow
from ..QE import QeScfTask, QeBgwFlow
from ..Abinit import AbinitScfTask, AbinitBgwFlow
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
        # FIXME doc: dft_flavor

        super(GWFlow, self).__init__(**kwargs)

        kwargs.pop('dirname', None)

        self.structure = kwargs['structure']
        self.ngkpt = kwargs.pop('ngkpt')
        self.kshift = kwargs.pop('kshift')
        self.qshift = kwargs.pop('qshift')

        nband_aliases = ('nbnd', 'nband')
        for key in nband_aliases:
            if key in kwargs:
                self.nbnd = kwargs.pop(key)
                break
        else:
            raise Exception('Number of bands must be specified with one of these keywords: {}.'
                            .format(nband_aliases))

        self.dft_flavor = check_dft_flavor(kwargs.get('dft_flavor',dft_flavor))

        # ==== DFT calculations ==== #

        # Quantum Espresso flavor
        if is_dft_flavor_espresso(self.dft_flavor):

            self.scftask = QeScfTask(
                dirname = pjoin(self.dirname, '01-Density'),
                ngkpt = self.ngkpt,
                kshift = self.kshift,
                **kwargs)

            kwargs.update(
                charge_density_fname = self.scftask.charge_density_fname,
                data_file_fname = self.scftask.data_file_fname,
                spin_polarization_fname = self.scftask.spin_polarization_fname)
            
            self.wfntask_ksh = QeBgwFlow(
                dirname = pjoin(self.dirname, '02-Wfn'),
                ngkpt = self.ngkpt,
                kshift = self.kshift,
                nbnd = self.nbnd,
                **kwargs)

            self.wfntask_qsh = QeBgwFlow(
                dirname = pjoin(self.dirname, '03-Wfnq'),
                ngkpt = self.ngkpt,
                kshift = self.kshift,
                qshift = self.qshift,
                nbnd = None,
                **kwargs)

            self.wfntask_ush = QeBgwFlow(
                dirname = pjoin(self.dirname, '04-Wfn_co'),
                ngkpt = self.ngkpt,
                nbnd = self.nbnd,
                rhog_flag = True,
                **kwargs)

            self.add_tasks([self.scftask, self.wfntask_ksh,
                            self.wfntask_qsh, self.wfntask_ush], merge=False)

            kwargs.update(wfn_fname = self.wfntask_ksh.wfn_fname,
                          wfnq_fname = self.wfntask_qsh.wfn_fname,
                          wfn_co_fname = self.wfntask_ush.wfn_fname,
                          rho_fname = self.wfntask_ush.rho_fname,
                          vxc_dat_fname = self.wfntask_ush.vxc_dat_fname)

        # Abinit flavor
        elif is_dft_flavor_abinit(self.dft_flavor):

            self.scftask = AbinitScfTask(
                dirname = pjoin(self.dirname, '01-Density'),
                ngkpt = self.ngkpt,
                kshift = self.kshift,
                **kwargs)
            
            kwargs.update(
                charge_density_fname = self.scftask.charge_density_fname,
                vxc_fname = self.scftask.vxc_fname)

            self.wfntask_ksh = AbinitBgwFlow(
                dirname = pjoin(self.dirname, '02-Wfn'),
                ngkpt = self.ngkpt,
                kshift = self.kshift,
                nband = self.nbnd,
                **kwargs)
            
            self.wfntask_qsh = AbinitBgwFlow(
                dirname = pjoin(self.dirname, '03-Wfnq'),
                ngkpt = self.ngkpt,
                kshift = self.kshift,
                qshift = self.qshift,
                nband = None,
                **kwargs)
            
            self.wfntask_ush = AbinitBgwFlow(
                dirname = pjoin(self.dirname, '04-Wfn_co'),
                ngkpt = self.ngkpt,
                nband = self.nbnd,
                rhog_flag = True,
                vxcg_flag = True,
                **kwargs)

            self.add_tasks([self.scftask, self.wfntask_ksh,
                            self.wfntask_qsh, self.wfntask_ush], merge=False)

            kwargs.update(wfn_fname = self.wfntask_ksh.wfn_fname,
                          wfnq_fname = self.wfntask_qsh.wfn_fname,
                          wfn_co_fname = self.wfntask_ush.wfn_fname,
                          rho_fname = self.wfntask_ush.rho_fname,
                          vxc_fname = self.wfntask_ush.vxc_fname)


        # ==== GW calculations ==== #
        
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
        
        self.add_tasks([self.epsilontask, self.sigmatask], merge=False)

