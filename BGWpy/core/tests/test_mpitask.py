import os
from copy import copy
import pickle
import unittest
from collections import OrderedDict

from ...tests import TestTask
from .. import MPITask

class TestMPITask(TestTask):
    """Test basic functions of Task."""

    def get_task(self, **kwargs):
        kwargs.setdefault('dirname', os.path.join(self.tmpdir, 'Task'))
        task = MPITask(**kwargs)
        return task

    def test_mpi_variables(self):
        """Test MPI variables."""
        common = dict(
            mpirun = 'mpirun',
            nproc = 6,
            nproc_flag = '-n',
            nodes = 2,
            nodes_flag = '-N',
            nproc_per_node = 3,
            nproc_per_node_flag = '--npernode')

        kwargs = copy(common)
        kwargs['mpirun'] = 'mpiexec'
        task = self.get_task(**kwargs)
        self.assertEqual(task.mpirun_variable, 'mpiexec -n 6 --npernode 3 -N 2')

        kwargs = copy(common)
        kwargs['nodes'] = None
        task = self.get_task(**kwargs)
        self.assertEqual(task.mpirun_variable, 'mpirun -n 6 --npernode 3')

        kwargs = copy(common)
        kwargs['nproc'] = None
        task = self.get_task(**kwargs)
        self.assertEqual(task.mpirun_variable, 'mpirun --npernode 3 -N 2')

        kwargs = copy(common)
        kwargs['nodes'] = None
        kwargs['nproc_per_node'] = None
        task = self.get_task(**kwargs)
        self.assertEqual(task.mpirun_variable, 'mpirun -n 6')

