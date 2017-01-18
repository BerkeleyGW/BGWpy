import os
import pickle
import unittest
from collections import OrderedDict

from ...tests import TestTask
from .. import Task

class TestBasicTask(TestTask):
    """Test basic functions of Task."""

    def get_task(self, **kwargs):
        kwargs.setdefault('dirname', os.path.join(self.tmpdir, 'Task'))
        task = Task(**kwargs)
        return task

    def test_task_write(self):
        """Test Task writing."""
        task = self.get_task()
        task.write()
        assert os.path.exists(task.dirname)
        assert os.path.exists(os.path.join(task.dirname,task.runscript.fname))

    def test_variable_storage(self):
        """Test storage of keyword arguments."""
        variables = dict(a=1,b=2,c=3)
        task = self.get_task(store_variables=True, **variables)
        assert task.variables == variables
        task.write()
        fname = os.path.join(task.dirname, 'variables.pkl')
        with open(fname, 'r') as f:
            read_variables = pickle.load(f)
        assert read_variables == variables

    def test_run(self):
        """Test Runscript run function."""
        task = self.get_task()
        task.write()
        task.run()
