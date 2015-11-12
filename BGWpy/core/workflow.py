from __future__ import print_function
import os
import subprocess
import pickle
import contextlib

from .util import exec_from_dir
from .runscript import RunScript
from .task import Task


class Workflow(Task):
    """
    Sequence of tasks.

    The tasks are written from the main directory (Workflow.dirname).

    e.g. for a flow of tasks executed in a single directory, use:

        >>> workflow = Workflow('FlowDirectory')
        >>> task = Task('FlowDirectory')

    then add the tasks in merging mode:
        >>> workflow.add_task(task, merge=True)

    while in a sub-directory mode:

        >>> task = Task('FlowDirectory/TaskDirectory')
        >>> workflow.add_task(task, merge=False)

    """

    def __init__(self, dirname='./', runscript_fname='run.sh', tasks=None, *args, **kwargs):
        super(Workflow, self).__init__(dirname, runscript_fname, *args, **kwargs)
        self.tasks = list()

    def add_task(self, task, merge=True):
        """
        Add a task to the workflow.


        Arguments
        ---------

        task: Task.

        Keyword arguments
        -----------------

        merge (True):
            Merge the execution in a single runscript.

        """
        if merge:
            assert self.dirname == task.dirname, (
                    'Only tasks with the same dirname can be merged to a flow.')
            self.runscript.merge(task.runscript)

        else:

            # Check that there is no clash in runscript file names.
            for t in self.tasks:
                if (t.dirname == task.dirname and
                    t.runscript.fname == task.runscript.fname):
                        raise Exception(
                            "Two tasks with the same directory name" +
                            " and runscript file name are being added." +
                            " Use the variable 'runscript_fname' to set" +
                            " the task's runscript file name.")

            # Adding some safety would makes the script less readable...
            # There must be a better way.
            #self.runscript.append('if [ -d {} ]'.format(task.dirname))
            #self.runscript.append('then')
            self.runscript.append('cd {}'.format(os.path.relpath(task.dirname, self.dirname)))
            self.runscript.append('bash {}'.format(task.runscript.fname))
            self.runscript.append('cd {}'.format(os.path.relpath(self.dirname, task.dirname, )))
            #self.runscript.append('else')
            #self.runscript.append('exit 1')
            #self.runscript.append('fi')

        self.tasks.append(task)

    def add_tasks(self, tasks, *args, **kwargs):
        for task in tasks:
            self.add_task(task, *args, **kwargs)

    def write(self):
        super(Workflow, self).write()
        for task in self.tasks:
            task.write()
        with self.exec_from_dirname():
            # Overwrite any runscript of the children tasks
            self.runscript.write()

    #def run_tasks(self):
    #    for task in self.tasks:
    #        task.run()

    def report(self, *args, **kwargs):
        for task in self.tasks:
            task.report(*args, **kwargs)

