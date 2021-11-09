from .dfttask import DFTTask
__all__ = ['WfnTask', 'WfnBgwConverter']


class WfnTask(DFTTask):

    def wfn_fname(self):
        pass


class WfnBgwConverter(DFTTask):

    def wfn_fname_in(self):
        pass

    def wfn_fname_out(self):
        pass


