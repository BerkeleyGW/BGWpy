from __future__ import print_function

import os

from ..core.util import exec_from_dir
from ..core import Task, MPITask
from ..BGW import get_kpt_grid, get_kpt_grid_nosym

class QETask(MPITask):

    _mandatory = """
    prefix
    structure
    """.split()

    def __init__(self, dirname, **kwargs):

        super(QETask, self).__init__(dirname, **kwargs)

        self.prefix = kwargs['prefix']
        self.savedir = self.prefix + '.save'
        self.pseudo_dir = kwargs.get('pseudo_dir', self.dirname)

        self.runscript['PW'] = kwargs.get('PW', 'pw.x')
        self.runscript['PW_flags'] = kwargs.get('PW_flags', '')  # TODO, use this...

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

    def write(self):
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

