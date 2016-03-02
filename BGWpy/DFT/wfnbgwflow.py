from ..core import Workflow
from .dfttask import DFTTask
from . import ScfTask, WfnTask, WfnBgwConverter

class WfnBgwFlow(Workflow):

    _ScfTask = ScfTask
    _WfnTask = WfnTask
    _WfnBgwTask = WfnBgwConverter

    def __init__(self, **kwargs):

        self.with_density = kwargs.get('with_density', False)

        if self.with_density:
            self.rhotask = self._ScfTask(**kwargs)

            kwargs.setdefault('charge_density_fname', self.rhotask.charge_density_fname)

        self.wfntask = self._WfnTask(**kwargs)
        self.wfnbgwntask = self._WfnBgwTask(**kwargs)

    # @abstractproperty
    def rho_fname(self):
        pass

    # @abstractproperty
    def rhog_fname(self):
        pass

    # @abstractproperty
    def vxc_fname(self):
        pass

    # @abstractproperty
    def wfn_fname(self):
        pass

