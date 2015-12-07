
from .dfttask import DFTFlow
from .wfntask import WfnTask, WfnBgwConverter

__all__ = ['WfnBgwFlow']

class WfnBgwFlow(DFTFlow):
    """A workflow for wavefunction calculation and conversion to BGW."""

    def __init__(self, flavor='qe', **kwargs):
        """
        Arguments
        ---------
        """

        if self.is_flavor_QE:

            from .. import QE

            self.wfntask = QE.WfnTask(**kwargs)
            self.wfnbgwtask = QE.PW2BGWTask(**kwargs)

        elif self.is_flavor_abinit:

            from .. import Abinit

            self.wfntask = Abinit.AbinitWfnTask(**kwargs)
            self.wfnbgwtask = Abinit.Abi2BgwTask(**kwargs)

        self.tasks.extend([self.wfntask, self.wfnbgwtask])


    def __init__(self, *args, **kwargs):
        super(WfnBgwFlow, self).__init__(kwargs['dirname'], *args, **kwargs)

    def _set_kqshift(self):
        raise NotImplementedError()

