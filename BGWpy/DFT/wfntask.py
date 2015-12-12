from .dfttask import DFTTask
__all__ = ['WfnTask', 'WfnBgwConverter']


class WfnTask(DFTTask):

    # @abstractproperty
    def wfn_fname(self):
        pass


class WfnBgwConverter(DFTTask):

    # @abstractproperty
    def wfn_fname_in(self):
        pass

    def wfn_fname_out(self):
        pass


