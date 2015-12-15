
from os.path import join as pjoin

from . import QeScfTask, QeWfnTask, Qe2BgwTask
from ..DFT import WfnBgwFlow

__all__ = ['QeBgwFlow']

class QeBgwFlow(WfnBgwFlow):

    _ScfTask = QeScfTask
    _WfnTask = QeWfnTask
    _WfnBgwTask = Qe2BgwTask

