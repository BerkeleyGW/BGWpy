from __future__ import print_function
import sys
import os
import warnings
import subprocess
import pickle
import contextlib

from ..config import default_mpi
from .util import exec_from_dir, last_lines_contain
from .runscript import RunScript

# Public
__all__ = ['Task', 'MPITask', 'IOTask']


class Task(object):
    """Task executed from a single directory, from a single script."""
    _dirname = '.'

    _TASK_NAME = 'Task'

    _STATUS_COMPLETED = 'Completed'
    _STATUS_UNSTARTED = 'Unstarted'
    _STATUS_UNFINISHED = 'Unfinished'
    _STATUS_UNKNOWN = 'Unknown'

    _report_colors = {
        _STATUS_COMPLETED : '\033[92m',
        _STATUS_UNSTARTED : '\033[94m',
        _STATUS_UNFINISHED : '\033[91m',
        _STATUS_UNKNOWN : '\033[95m',
        }
    _end_color = '\033[0m'

    def __init__(self, dirname='./', runscript_fname='run.sh', store_variables=False, *args, **kwargs):
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

        self._TASK_NAME = '{:<10} : {}'.format(self._TASK_NAME, self.dirname)

    @property
    def dirname(self):
        return self._dirname

    @dirname.setter
    def dirname(self, value):
        self._dirname = value
        # TODO: Update the links

    @property
    def runscript_fname(self):
        basename = self.runscript.fname
        return os.path.join(self.dirname, basename)

    @runscript_fname.setter
    def runscript_fname(self, value):
        if os.path.basename(value) != value:
            raise Exception('Cannot use a path for runscript_fname')
        self.runscript.fname = value

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
                with open('variables.pkl', 'w') as f:
                    pickle.dump(self.variables, f)

    def update_link(self, target, dest):
        """
        Modify or add a symbolic link.
        If dest is already defined in a link, then the target is replaced.
        The target will be expressed relative to the dirname.
        The destination *must* be relative to the dirname.
        If target is empty or None, the link is suppressed.
        """
        if not target:
            self.remove_link(dest)
            return

        reltarget = os.path.relpath(
            target, os.path.join(self.dirname, os.path.dirname(dest)))

        for link in self.runscript.links:
            if link[1] == dest:
                link[0] = reltarget
                break
        else:
            self.runscript.add_link(reltarget, dest)

    def remove_link(self, dest):
        """Remove a link from the name of the destination."""
        for i, link in enumerate(self.runscript.links):
            if link[1] == dest:
                del self.runscript.links[i]
                break
        
    def update_copy(self, source, dest):
        """
        Modify or add a file to copy.
        If dest is already defined in a link, then the source is replaced.
        The source will be expressed relative to the dirname.
        The destination *must* be relative to the dirname.
        """
        relsource = os.path.relpath(source, os.path.realpath(self.dirname))
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

    def is_complete(self):
        """True if the task reports a completed status."""
        status = self.get_status()
        return (status is self._STATUS_COMPLETED)
        
    def report(self, file=None, color=True, **kwargs):
        """
        Report whether the task completed normally.

        Keyword arguments
        -----------------
        file: (sys.stdout)
            Write the task status in an open file.
        check_time: bool (False)
            Consider a task as unstarted if output is older than input.
        color: bool (True)
            Color the output. Use this flag to disable the colors
            e.g. if you want to pipe the output to a file.
            No color are used whenever a 'file' argument is given.
        """
        status = self.get_status(**kwargs)

        if file is None and color:
            col = self._report_colors[status]
            status = col + str(status) + self._end_color

        s = '   {:<50}  -  Status :  {}'.format(self._TASK_NAME, status)

        file = file if file is not None else sys.stdout
        print(s, file=file)


# =========================================================================== #


class MPITask(Task):
    """Task whose run script defines MPI variables for the main execution."""

    _mpirun = default_mpi['mpirun']
    _nproc = default_mpi['nproc']
    _nproc_flag = default_mpi['nproc_flag']
    _nproc_per_node = default_mpi['nproc_per_node']
    _nproc_per_node_flag = default_mpi['nproc_per_node_flag']
    _nodes = default_mpi['nodes']
    _nodes_flag = default_mpi['nodes_flag']

    def __init__(self, *args, **kwargs):
        """
        Keyword arguments
        -----------------

        dirname : str ('./')
            Main directory from which the scripts are executed.
        runscript_fname : str ('run.sh')
            Name of the main execution script.
        mpirun : str ('mpirun')
            Command to call the mpi runner.
        nproc : int (1)
            Number of processors or number of parallel executions.
        nproc_flag: str ('-n')
            Flag to specify nproc to the mpi runner.
        nproc_per_node : int (nproc)
            Number of processors (parallel executions) per node.
        nproc_per_node_flag : str ('--npernode')
            Flag to specify the number of processors per node.
        nodes : int (1)
            Number of nodes.
        nodes_flag: str ('-n')
            Flag to specify the number of nodes to the mpi runner.

        """

        super(MPITask, self).__init__(*args, **kwargs)

        self.mpirun = default_mpi['mpirun']
        self.nproc_flag = default_mpi['nproc_flag']
        self.nproc_per_node_flag = default_mpi['nproc_per_node_flag']
        self.nproc = default_mpi['nproc']
        self.nproc_per_node = default_mpi['nproc_per_node']

        for key in ('mpirun', 'nproc', 'nproc_flag',
                    'nproc_per_node', 'nproc_per_node_flag',
                    'nodes', 'nodes_flag'):
                   
            if key in kwargs:
                setattr(self, key, kwargs[key])

        # This is mostly for backward compatibility
        if 'mpirun_n' in kwargs:
            self.mpirun_n = kwargs['mpirun_n']

    def _declare_mpirun(self):
        self.runscript['MPIRUN'] = self.mpirun_variable

    @property
    def mpirun_variable(self):
        if not self.mpirun:
            return ''

        variable = str(self.mpirun)

        if self.nproc_flag and self.nproc:
            variable += ' {} {}'.format(self.nproc_flag, self.nproc)

        if self.nproc_per_node_flag and self.nproc_per_node:
            variable += ' {} {}'.format(self.nproc_per_node_flag, self.nproc_per_node)

        if self.nodes_flag and self.nodes:
            variable += ' {} {}'.format(self.nodes_flag, self.nodes)

        return variable

    @property
    def mpirun(self):
        return self._mpirun

    @mpirun.setter
    def mpirun(self, value):
        self._mpirun = value
        self._declare_mpirun()

    @property
    def nproc(self):
        return self._nproc

    @nproc.setter
    def nproc(self, value):
        self._nproc = value
        self._declare_mpirun()

    @property
    def nproc_flag(self):
        return self._nproc_flag

    @nproc_flag.setter
    def nproc_flag(self, value):
        self._nproc_flag = value
        self._declare_mpirun()

    @property
    def nproc_per_node(self):
        return self._nproc_per_node

    @nproc_per_node.setter
    def nproc_per_node(self, value):
        self._nproc_per_node = value
        self._declare_mpirun()

    @property
    def nproc_per_node_flag(self):
        return self._nproc_per_node_flag

    @nproc_per_node_flag.setter
    def nproc_per_node_flag(self, value):
        self._nproc_per_node_flag = value
        self._declare_mpirun()

    @property
    def nodes(self):
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        self._nodes = value
        self._declare_mpirun()

    @property
    def nodes_flag(self):
        return self._nodes_flag

    @nodes_flag.setter
    def nodes_flag(self, value):
        self._nodes_flag = value
        self._declare_mpirun()

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


# =========================================================================== #


class IOTask(Task):
    """
    Task that depends on an input and that produces an output,
    which might be checked for completion.
    """

    _input_fname = ''
    _output_fname = ''
    _TAG_JOB_COMPLETED = 'JOB COMPLETED'

    # It is important that this task has no __init__ function,
    # because it is mostly used with multiple-inheritance classes.

    def get_status(self, check_time=False):

        if self._input_fname:

            if not os.path.exists(self.input_fname):
                return self._STATUS_UNSTARTED

        if self._output_fname:

            if not os.path.exists(self.output_fname):
                return self._STATUS_UNSTARTED

        if check_time:
            input_creation_time = os.path.getmtime(self.input_fname)
            output_creation_time = os.path.getmtime(self.output_fname)

            if input_creation_time > output_creation_time:
                return self._STATUS_UNSTARTED

        if not self._TAG_JOB_COMPLETED:
            return self._STATUS_UNKNOWN

        if last_lines_contain(self.output_fname, self._TAG_JOB_COMPLETED):
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


