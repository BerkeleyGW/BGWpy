from __future__ import print_function
import os
from copy import copy

from . import TestTask
from .test_BGW_tasks import TestBGWTasksMaker

from .. import data
from .. import Structure, QeScfTask
from .. import EpsilonTask, SigmaTask

class TestSigmaTasksMaker(TestBGWTasksMaker):

    # Common arguments for tasks.
    common_kwargs = copy(TestBGWTasksMaker.common_kwargs)
    common_kwargs.update(
        ecuteps = 5.0,
        ibnd_min = 1,
        ibnd_max = 8,
        )

    def get_sigma_HF(self, pw2bgwtask_ush):
        kwargs = copy(self.common_kwargs)
        kwargs.update(extra_lines = ['screening_semiconductor'])
        kwargs.update(extra_variables = {'frequency_dependence' : -1})
        kwargs.update(ngqpt=kwargs['ngkpt'])
        return SigmaTask(
            dirname = os.path.join(self.tmpdir, 'Sigma'),
            wfn_co_fname = pw2bgwtask_ush.wfn_fname,
            rho_fname = pw2bgwtask_ush.rho_fname,
            vxc_dat_fname = pw2bgwtask_ush.vxc_dat_fname,
            **kwargs)


class TestSigma(TestSigmaTasksMaker):
    """Test specific features of sigma."""

    def test_HF(self):
        """Test Hartree-Fock calculation."""
        scftask = self.get_scftask()

        wfntask_ush = self.get_wfntask_ush(scftask)
        pw2bgwtask_ush = self.get_pw2bgwtask_ush(wfntask_ush)

        sigmatask = self.get_sigma_HF(pw2bgwtask_ush)

        for task in (scftask,
                     wfntask_ush, pw2bgwtask_ush,
                     sigmatask,
                    ):

            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

