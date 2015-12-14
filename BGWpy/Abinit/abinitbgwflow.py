
from os.path import join as pjoin

from . import AbinitScfTask, AbinitWfnTask, Abi2BgwTask
from ..DFT import WfnBgwFlow

__all__ = ['AbinitBgwFlow']

class AbinitBgwFlow(WfnBgwFlow):

    _ScfTask = AbinitScfTask
    _WfnTask = AbinitWfnTask
    _WfnBgwTask = Abi2BgwTask

    def __init__(self, **kwargs):
        """
        """
        # FIXME doc

        super(AbinitBgwFlow, self).__init__(**kwargs)

        kwargs.pop('dirname', None)

        self.with_density = kwargs.get('with_density', False)

        if self.with_density:
            self.scftask = self._ScfTask(
                dirname = kwargs.get('density_dirname',
                                     pjoin(self.dirname, '01-Density')),
                                     **kwargs)

            kwargs.setdefault('charge_density_fname',
                              self.scftask.charge_density_fname)

            self.add_task(self.scftask, merge=False)

        self.wfntask = self._WfnTask(
            dirname = kwargs.get('wfn_dirname',
                                 pjoin(self.dirname, '02-Wavefunctions')),
                                 **kwargs)

        self.add_task(self.wfntask, merge=False)

        self.wfbgwntask = self._WfnBgwTask(
            dirname = self.wfntask.dirname,
            wfng_flag = True,
            rhog_flag = True,
            vxcg_flag = True,
            rho_fname = self.scftask.rho_fname,
            vxc_fname = self.scftask.vxc_fname,
            wfn_fname = self.wfntask.wfn_fname,
            **kwargs)

        self.add_task(self.wfbgwntask, merge=False)






