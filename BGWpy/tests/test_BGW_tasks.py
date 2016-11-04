from __future__ import print_function
import os
from copy import copy

from . import TestTask
from .test_QE_tasks import TestQETasksMaker

from .. import data
from .. import Structure, QeScfTask
from .. import EpsilonTask, SigmaTask
from .. import KernelTask, AbsorptionTask

# Note: The tests are redundant,
# because tests cannot be interdependent.

class TestBGWTasksMaker(TestQETasksMaker):

    # Common arguments for tasks.
    common_kwargs = copy(TestQETasksMaker.common_kwargs)
    common_kwargs.update(
        ecuteps = 5.0,
        ibnd_min = 1,
        ibnd_max = 8,

        nbnd_val = 4,
        nbnd_cond = 4,

        nbnd_val_co=4,
        nbnd_cond_co=4,
        nbnd_val_fi=4,
        nbnd_cond_fi=4,
        )

    def get_wfntask_ksh(self, scftask):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.5,.5,.5], qshift=[.0,.0,.0])
        return self.get_wfntask(scftask, **kwargs)

    def get_pw2bgwtask_ksh(self, wfntask_ksh):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.5,.5,.5], qshift=[.0,.0,.0])
        return self.get_pw2bgwtask(wfntask_ksh, **kwargs)

    def get_wfntask_qsh(self, scftask):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.5,.5,.5], qshift=[.001,.0,.0])
        return self.get_wfntask(scftask,
                        dirname=os.path.join(self.tmpdir, 'Wfnq'), **kwargs)

    def get_pw2bgwtask_qsh(self, wfntask_qsh):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.5,.5,.5], qshift=[.001,.0,.0])
        return self.get_pw2bgwtask(wfntask_qsh, **kwargs)

    def get_wfntask_ush(self, scftask):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.0,.0,.0], qshift=[.0,.0,.0])
        return self.get_wfntask(scftask,
                                dirname=os.path.join(self.tmpdir, 'wfn_co'),
                                **kwargs)

    def get_pw2bgwtask_ush(self, wfntask_ush):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.0,.0,.0], qshift=[.0,.0,.0])
        kwargs.update(
            wfn_fname = 'wfn_co.cplx',
            rho_fname = 'rho.real',
            vxc_diag_nmax = 8)

        return self.get_pw2bgwtask(wfntask_ush, **kwargs)

    def get_wfntask_fi(self, scftask):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.5,.5,.5], qshift=[.0,.0,.0])
        kwargs.update(symkpt = False)
        return self.get_wfntask(scftask,
                                dirname=os.path.join(self.tmpdir, 'Wfn_fi'),
                                **kwargs)

    def get_pw2bgwtask_fi(self, wfntask_fi):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.5,.5,.5], qshift=[.0,.0,.0])
        kwargs.update(wfn_fname = 'wfn_fi.cplx')
        return self.get_pw2bgwtask(wfntask_fi, **kwargs)

    def get_wfntask_fiq(self, scftask):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.5,.5,.5], qshift=[.001,.0,.0])
        kwargs.update(symkpt = False)
        return self.get_wfntask(scftask,
                                dirname=os.path.join(self.tmpdir, 'Wfnq_fi'),
                                **kwargs)

    def get_pw2bgwtask_fiq(self, wfntask_fiq):
        kwargs = copy(self.common_kwargs)
        kwargs.update(kshift=[.5,.5,.5], qshift=[.001,.0,.0])
        kwargs.update(wfn_fname = 'wfn_fi.cplx')
        return self.get_pw2bgwtask(wfntask_fiq, **kwargs)


    def get_epsilontask(self, pw2bgwtask_ksh, pw2bgwtask_qsh):
        kwargs = copy(self.common_kwargs)
        kwargs.update(qshift=[.001,.0,.0])
        return EpsilonTask(
            dirname = os.path.join(self.tmpdir, 'Epsilon'),
            wfn_fname = pw2bgwtask_ksh.wfn_fname,
            wfnq_fname = pw2bgwtask_qsh.wfn_fname,
            **kwargs)

    def get_sigmatask(self, pw2bgwtask_ush, epsilontask):
        kwargs = copy(self.common_kwargs)
        kwargs.update(extra_lines = ['screening_semiconductor'])
        return SigmaTask(
            dirname = os.path.join(self.tmpdir, 'Sigma'),
            wfn_co_fname = pw2bgwtask_ush.wfn_fname,
            rho_fname = pw2bgwtask_ush.rho_fname,
            vxc_dat_fname = pw2bgwtask_ush.vxc_dat_fname,
            eps0mat_fname = epsilontask.eps0mat_fname,
            epsmat_fname = epsilontask.epsmat_fname,
            **kwargs)

    def get_kerneltask(self, pw2bgwtask_ush, epsilontask):
        kwargs = copy(self.common_kwargs)
        kwargs.update(
            extra_lines = ['screening_semiconductor',
                           'use_symmetries_coarse_grid']
            )

        return KernelTask(
            dirname = os.path.join(self.tmpdir, 'Kernel'),
            wfn_co_fname=pw2bgwtask_ush.wfn_fname,
            eps0mat_fname = epsilontask.eps0mat_fname,
            epsmat_fname = epsilontask.epsmat_fname,
            **kwargs)

    def get_absorptiontask(self, pw2bgwtask_ush,
                           pw2bgwtask_fi, pw2bgwtask_fiq,
                           epsilontask, sigmatask, kerneltask):

        kwargs = copy(self.common_kwargs)
        kwargs.update(
            extra_lines = [
                'use_symmetries_coarse_grid',
                'no_symmetries_fine_grid',
                'no_symmetries_shifted_grid',
                'screening_semiconductor',
                'use_velocity',
                'gaussian_broadening',
                'eqp_co_corrections',
                ],
            extra_variables = {'energy_resolution' : 0.15,},

            )

        if AbsorptionTask._use_hdf5:
            kwargs['bsemat_fname'] = kerneltask.bsemat_fname
        else:
            kwargs['bsedmat_fname'] = kerneltask.bsedmat_fname
            kwargs['bsexmat_fname'] = kerneltask.bsexmat_fname

        return AbsorptionTask(
            dirname = os.path.join(self.tmpdir, 'Absorption'),
            wfn_co_fname = pw2bgwtask_ush.wfn_fname,
            eps0mat_fname = epsilontask.eps0mat_fname,
            epsmat_fname = epsilontask.epsmat_fname,
            wfn_fi_fname = pw2bgwtask_fi.wfn_fname,
            wfnq_fi_fname = pw2bgwtask_fiq.wfn_fname,
            sigma_fname = sigmatask.sigma_fname,
            eqp_fname = sigmatask.eqp1_fname,
            **kwargs)



class TestBGWTasks(TestBGWTasksMaker):

    def test_epsilon(self):
        """Test Epsilon calculation."""
        scftask = self.get_scftask()

        wfntask_ksh = self.get_wfntask_ksh(scftask)
        pw2bgwtask_ksh = self.get_pw2bgwtask_ksh(wfntask_ksh)

        wfntask_qsh = self.get_wfntask_qsh(scftask)
        pw2bgwtask_qsh = self.get_pw2bgwtask_qsh(wfntask_qsh)

        epsilontask = self.get_epsilontask(pw2bgwtask_ksh, pw2bgwtask_qsh)

        for task in (scftask,
                     wfntask_ksh, pw2bgwtask_ksh,
                     wfntask_qsh, pw2bgwtask_qsh,
                     epsilontask,
                    ):

            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

    def test_sigma(self):
        """Test Sigma calculation."""
        scftask = self.get_scftask()

        wfntask_ksh = self.get_wfntask_ksh(scftask)
        pw2bgwtask_ksh = self.get_pw2bgwtask_ksh(wfntask_ksh)

        wfntask_qsh = self.get_wfntask_qsh(scftask)
        pw2bgwtask_qsh = self.get_pw2bgwtask_qsh(wfntask_qsh)

        wfntask_ush = self.get_wfntask_ush(scftask)
        pw2bgwtask_ush = self.get_pw2bgwtask_ush(wfntask_ush)

        epsilontask = self.get_epsilontask(pw2bgwtask_ksh, pw2bgwtask_qsh)
        sigmatask = self.get_sigmatask(pw2bgwtask_ush, epsilontask)

        for task in (scftask,
                     wfntask_ksh, pw2bgwtask_ksh,
                     wfntask_qsh, pw2bgwtask_qsh,
                     wfntask_ush, pw2bgwtask_ush,
                     epsilontask, sigmatask,
                    ):

            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

    def test_kernel(self):
        """Test Kernel calculation."""
        scftask = self.get_scftask()

        wfntask_ksh = self.get_wfntask_ksh(scftask)
        pw2bgwtask_ksh = self.get_pw2bgwtask_ksh(wfntask_ksh)

        wfntask_qsh = self.get_wfntask_qsh(scftask)
        pw2bgwtask_qsh = self.get_pw2bgwtask_qsh(wfntask_qsh)

        wfntask_ush = self.get_wfntask_ush(scftask)
        pw2bgwtask_ush = self.get_pw2bgwtask_ush(wfntask_ush)

        epsilontask = self.get_epsilontask(pw2bgwtask_ksh, pw2bgwtask_qsh)
        sigmatask = self.get_sigmatask(pw2bgwtask_ush, epsilontask)
        kerneltask = self.get_kerneltask(pw2bgwtask_ush, epsilontask)

        for task in (scftask,
                     wfntask_ksh, pw2bgwtask_ksh,
                     wfntask_qsh, pw2bgwtask_qsh,
                     wfntask_ush, pw2bgwtask_ush,
                     epsilontask, sigmatask, kerneltask
                    ):

            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

    def test_absorption(self):
        """Test Absorption calculation."""
        scftask = self.get_scftask()

        wfntask_ksh = self.get_wfntask_ksh(scftask)
        pw2bgwtask_ksh = self.get_pw2bgwtask_ksh(wfntask_ksh)

        wfntask_qsh = self.get_wfntask_qsh(scftask)
        pw2bgwtask_qsh = self.get_pw2bgwtask_qsh(wfntask_qsh)

        wfntask_ush = self.get_wfntask_ush(scftask)
        pw2bgwtask_ush = self.get_pw2bgwtask_ush(wfntask_ush)

        wfntask_fi = self.get_wfntask_fi(scftask)
        pw2bgwtask_fi = self.get_pw2bgwtask_fi(wfntask_fi)

        wfntask_fiq = self.get_wfntask_fiq(scftask)
        pw2bgwtask_fiq = self.get_pw2bgwtask_fiq(wfntask_fiq)

        epsilontask = self.get_epsilontask(pw2bgwtask_ksh, pw2bgwtask_qsh)
        sigmatask = self.get_sigmatask(pw2bgwtask_ush, epsilontask)
        kerneltask = self.get_kerneltask(pw2bgwtask_ush, epsilontask)
        absorptiontask = self.get_absorptiontask(pw2bgwtask_ush, pw2bgwtask_fi,
                                                 pw2bgwtask_fiq, epsilontask,
                                                 sigmatask, kerneltask)

        for task in (scftask,
                     wfntask_ksh, pw2bgwtask_ksh,
                     wfntask_qsh, pw2bgwtask_qsh,
                     wfntask_ush, pw2bgwtask_ush,
                     wfntask_fi, pw2bgwtask_fi,
                     wfntask_fiq, pw2bgwtask_fiq,
                     epsilontask, sigmatask,
                     kerneltask, absorptiontask,
                    ):

            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

