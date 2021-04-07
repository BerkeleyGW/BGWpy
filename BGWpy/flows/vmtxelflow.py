"""Workflow to compute dipole operator matrix elements."""
from os.path import join as pjoin
import warnings

from ..config import flavors
from ..config import is_dft_flavor_espresso, is_dft_flavor_abinit, check_dft_flavor
from ..external import Structure
from ..core import Workflow
from ..BGW import VmtxelTask

__all__ = ['VmtxelFlow']

class VmtxelFlow(Workflow):

    def __init__(self, **kwargs):

        super(VmtxelFlow, self).__init__(**kwargs)

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
            raise NotImplementedError()
            fnames = self.make_dft_tasks_espresso(**kwargs)
            kwargs.update(fnames)
    
        # Abinit flavor
        elif is_dft_flavor_abinit(self.dft_flavor):
            fnames = self.make_dft_tasks_abinit(**kwargs)
            kwargs.update(fnames)

        self.vmtxeltask = VmtxelTask(dirname=pjoin(self.dirname, '21-vmtxel'), **kwargs)

        self.add_task(self.vmtxeltask)

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


        # Wavefunctions on fine k-point grids
        self.wfntask_fi_ush = AbinitBgwFlow(
            dirname = pjoin(self.dirname, '05-wfn_fi'),
            nband = self.nbnd_fine,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = 3*[.0],
            symkpt = False,
            **kwargs)
        
        self.wfntask_fi_qsh = AbinitBgwFlow(
            dirname = pjoin(self.dirname, '06-wfnq_fi'),
            nband = None,
            ngkpt = self.ngkpt_fi,
            kshift = self.kshift_fi,
            qshift = self.qshift_fi,
            symkpt = False,
            **kwargs)
        
        self.add_tasks([self.wfntask_fi_ush, self.wfntask_fi_qsh])                                                                                             

        fnames = dict(wfn_fi_fname = self.wfntask_fi_ush.wfn_fname,
                      wfnq_fi_fname = self.wfntask_fi_qsh.wfn_fname
                    )

        return fnames


