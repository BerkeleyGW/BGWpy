from __future__ import print_function

import os
import warnings

from ..core.util import exec_from_dir, last_lines_contain
from ..core import Task, MPITask
from ..BGW import get_kpt_grid, get_kpt_grid_nosym

class QETask(MPITask):
    """Base class for Quantum Espresso calculations."""

    _input_fname = ''
    _output_fname = ''

    _TAG_JOB_DONE = 'JOB DONE'

    _mandatory = """
    prefix
    structure
    """.split()

    def __init__(self, dirname, **kwargs):

        super(QETask, self).__init__(dirname, **kwargs)

        self.prefix = kwargs['prefix']
        self.savedir = self.prefix + '.save'
        self.pseudo_dir = kwargs.get('pseudo_dir', self.dirname)
        self.pseudos = kwargs.get('pseudos', [])

        self.runscript['PW'] = kwargs.get('PW', 'pw.x')
        self.runscript['PWFLAGS'] = kwargs.get('PWFLAGS', '')  # TODO, use this...

    def exec_from_savedir(self):
        original = os.path.realpath(os.curdir)
        if os.path.realpath(original) == os.path.realpath(self.dirname):
            return exec_from_dir(self.savedir)
        return exec_from_dir(os.path.join(self.dirname, self.savedir))

    def get_kpts(self, kwargs):

        symkpt = kwargs.get('symkpt', True)

        if 'ngkpt' in kwargs:
            if symkpt:
                kpts, wtks = get_kpt_grid(
                            kwargs['structure'],
                            kwargs['ngkpt'],
                            kshift=kwargs.get('kshift',[0,0,0]),
                            qshift=kwargs.get('qshift',[0,0,0]),
                            )
            else:
                kpts, wtks = get_kpt_grid_nosym(
                            kwargs['ngkpt'],
                            kshift=kwargs.get('kshift',[0,0,0]),
                            qshift=kwargs.get('qshift',[0,0,0]),
                            )
        else:
            kpts = kwargs['kpts']
            wtks = kwargs['wtks']

        return kpts, wtks

    def check_pseudos(self):
        for pseudo in self.pseudos:
            fname = os.path.join(self.dirname, self.pseudo_dir, pseudo)
            if not os.path.exists(fname):
                warnings.warn('Pseudopotential not found:\n{}'.format(fname))

    def write(self):
        self.check_pseudos()
        super(QETask, self).write()
        with self.exec_from_dirname():
            self.input.write()
            if not os.path.exists(self.savedir):
                os.mkdir(self.savedir)

    _pseudo_dir = './'
    @property
    def pseudo_dir(self):
        return self._pseudo_dir

    @pseudo_dir.setter
    def pseudo_dir(self, value):
        if os.path.realpath(value) == value:
            self._pseudo_dir = value
        else:
            self._pseudo_dir = os.path.relpath(value, self.dirname)

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

        if last_lines_contain(self.output_fname, self._TAG_JOB_DONE):
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

