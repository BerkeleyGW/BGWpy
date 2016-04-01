
from .dfttask import DFTFlow
from .wfntask import WfnTask, WfnBgwConverter

__all__ = ['WfnBgwFlow']

class WfnBgwFlow(DFTFlow):
    """A workflow for wavefunction calculation and conversion to BGW."""

    def __init__(self, *args, **kwargs):
        super(WfnBgwFlow, self).__init__(*args, **kwargs)

    def _set_kqshift(self):
        raise NotImplementedError()

    @property
    def rho_fname(self):
        raise NotImplementedError()

    @property
    def wfn_fname(self):
        raise NotImplementedError()

    @property
    def vxc_fname(self):
        raise NotImplementedError()

    @property
    def vxc_dat_fname(self):
        raise NotImplementedError()
