from __future__ import print_function
import os

from ..core.util import last_lines_contain
from ..core import Task, MPITask


class BGWTask(MPITask):
    """Base class for BerkeleyGW calculations."""

    _input_fname = ''
    _output_fname = ''

    _TAG_TOTAL_TIME = 'TOTAL:'

    def get_status(self):

        if not self.input_fname or not self.output_fname:
            return self._STATUS_UNKNOWN

        if not os.path.exists(self.input_fname):
            return self._STATUS_UNSTARTED

        if not os.path.exists(self.output_fname):
            return self._STATUS_UNSTARTED

        input_creation_time = os.path.getmtime(self.input_fname)
        output_creation_time = os.path.getmtime(self.output_fname)

        if input_creation_time > output_creation_time:
            return self._STATUS_UNSTARTED

        if last_lines_contain(self.output_fname, self._TAG_TOTAL_TIME):
            return self._STATUS_COMPLETED

        return self._STATUS_UNFINISHED

    @property
    def input_fname(self):
        basename = self._input_fname
        if 'input' in dir(self):
            basename = self.input.fname
        return os.path.join(self.dirname, basename)

    @input_fname.setter
    def input_fname(self, value):
        if os.path.basename(value) != value:
            raise Exception('Cannot use a path for input_fname')
        self._input_fname = value
        if 'input' in dir(self):
            self.input.fname = value

    @property
    def output_fname(self):
        return os.path.join(self.dirname, self._output_fname)

