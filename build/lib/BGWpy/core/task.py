from __future__ import print_function
import sys
import os
import subprocess
import pickle
import contextlib

from .util import exec_from_dir
from .runscript import RunScript


class Task(object):
    """Task executed from a single directory, from a single script."""
    _dirname = '.'

    _TASK_NAME = 'Task'

    _STATUS_COMPLETED = 'Completed'
    _STATUS_UNSTARTED = 'Unstarted'
    _STATUS_UNFINISHED = 'Unfinished'
    _STATUS_UNKNOWN = 'Unknown'

    def __init__(self, dirname='./', runscript_fname='run.sh', store_variables=True, *args, **kwargs):
        """
        Keyword arguments
        -----------------

        dirname : str ('./')
            Main directory from which the scripts are executed.
        runscript_fname : str ('run.sh')
            Name of the main execution script.
        store_variables : bool (True)
            Write all the initialization variables in a pkl file
            at writing time. Must be set at initialization
            in order to be effective.

        """

        self.dirname = dirname
        self.runscript = RunScript()
        self.runscript.fname = runscript_fname
        self.variables = kwargs if store_variables else dict()

    @property
    def dirname(self):
        return self._dirname

    @dirname.setter
    def dirname(self, value):
        self._dirname = value
        # TODO: Update the links

    @property
    def runscript_fname(self):
        return self.runscript.fname

    @contextlib.contextmanager
    def exec_from_dirname(self):
        """Exec commands from main directory then come back."""
        original = os.path.realpath(os.curdir)
        os.chdir(self.dirname)
        try:
            yield
        finally:
            os.chdir(original)

    def exec_from_dirname(self):
        return exec_from_dir(self.dirname)

    def run(self):
        with self.exec_from_dirname():
            self.runscript.run()

    def write(self):
        subprocess.call(['mkdir', '-p', self.dirname])
        with self.exec_from_dirname():
            self.runscript.write()

            if self.variables:
                with open('variables.pkl', 'write') as f:
                    pickle.dump(self.variables, f)

    def update_link(self, target, dest):
        """
        Modify or add a symbolic link.
        If dest is already defined in a link, then the target is replaced.
        The target will be expressed relative to the dirname.
        The destination *must* be relative to the dirname.
        """
        reltarget = os.path.relpath(target,
                        os.path.join(self.dirname, os.path.dirname(dest)))
        for link in self.runscript.links:
            if link[1] == dest:
                link[0] = reltarget
                break
        else:
            self.runscript.add_link(reltarget, dest)
        
    def update_copy(self, source, dest):
        """
        Modify or add a file to copy.
        If dest is already defined in a link, then the source is replaced.
        The source will be expressed relative to the dirname.
        The destination *must* be relative to the dirname.
        """
        relsource = os.path.relpath(source, self.dirname)
        for copy in self.runscript.copies:
            if copy[1] == dest:
                copy[0] = relsource
                break
        else:
            self.runscript.add_copy(relsource, dest)

    def get_status(self):
        """
        Return the status of the task. Possible status are:
        Completed, Unstarted, Unfinished, Unknown.
        """
        return self._STATUS_UNKNOWN
        
    def report(self, file=sys.stdout):
        status = self.get_status()
        s = 'Status     :   {}'.format(status)
        s = '{:<20}  -  Status :  {}'.format(self._TASK_NAME, status)
        print(s, file=file)


# =========================================================================== #


class MPITask(Task):
    """Task whose run script defines MPI variables for the main execution."""

    _mpirun = 'mpirun'
    _nproc_flag = '-n'
    _nproc_per_node_flag = '--npernode'

    _nproc = 1
    _nproc_per_node = 1

    def __init__(self, *args, **kwargs):
        """
        Keyword arguments
        -----------------

        dirname : str ('./')
            Main directory from which the scripts are executed.
        runscript_fname : str ('run.sh')
            Name of the main execution script.
        nproc : int (1)
            The number of processors per node,
            that is, the number of parallel executions.
        nproc_per_node : int (nproc)
            Number of processors (parallel executions) per node.
        mpirun : str ('mpirun')
            The command to call the mpi runner,
            with the flag to specify the number of processors.
        nproc_flag: str ('-n')
            The number of processors per node,
            that is, the number of parallel executions.
        nproc_per_node_flag : str ('--npernode')
            The flag to specify the number of processors per node.

        """

        super(MPITask, self).__init__(*args, **kwargs)

        self.mpirun = kwargs.get('mpirun', 'mpirun')
        self.nproc_flag = kwargs.get('nproc_flag', '-n')
        self.nproc_per_node_flag = kwargs.get('nproc_per_node_flag', '--npernode')

        self.nproc = kwargs.get('nproc', 1)
        self.nproc_per_node = kwargs.get('nproc_per_node', self.nproc)

        # This is mostly for backward compatibility
        if 'mpirun_n' in kwargs:
            self.mpirun_n = kwargs['mpirun_n']

    def _declare_mpirun(self):
        self.runscript['MPIRUN'] = self.mpirun_variable

    def _nullify_mpirun(self):
        self.runscript['MPIRUN'] = ''

    def _declare_if_mpirun(self):
        if self.mpirun:
            self._declare_mpirun()
        else:
            self._nullify_mpirun()

    @property
    def mpirun_variable(self):
        return '{} {} {} {} {}'.format(
                                 self.mpirun,
                                 self.nproc_flag, self.nproc,
                                 self.nproc_per_node_flag, self.nproc_per_node)

    @property
    def mpirun(self):
        return self._mpirun

    @mpirun.setter
    def mpirun(self, value):
        self._mpirun = value
        self._declare_if_mpirun()

    @property
    def nproc(self):
        return self._nproc

    @nproc.setter
    def nproc(self, value):
        self._nproc = value
        self._declare_if_mpirun()

    @property
    def nproc_per_node(self):
        return self._nproc_per_node

    @nproc_per_node.setter
    def nproc_per_node(self, value):
        self._nproc_per_node = value
        self._declare_if_mpirun()

    @property
    def nproc_flag(self):
        return self._nproc_flag

    @nproc_flag.setter
    def nproc_flag(self, value):
        self._nproc_flag = value
        self._declare_if_mpirun()

    @property
    def nproc_per_node_flag(self):
        return self._nproc_per_node_flag

    @nproc_per_node_flag.setter
    def nproc_per_node_flag(self, value):
        self._nproc_per_node_flag = value
        self._declare_if_mpirun()

    @property
    def mpirun_n(self):
        return self.mpirun + ' ' + self.nproc_flag

    @mpirun_n.setter
    def mpirun_n(self, value):
        if not value:
            self.nproc_flag = ''
            self.mpirun = ''

        parts = value.split()

        if len(parts) == 0:
            self.nproc_flag = ''
            self.mpirun = ''

        elif len(parts) == 1:
            self.nproc_flag = ''
            self.mpirun = parts[0]

        elif len(parts) == 2:
            self.nproc_flag = parts[1]
            self.mpirun = parts[0]

        else:
            self.nproc_flag = parts[1]
            self.mpirun = parts[0]

