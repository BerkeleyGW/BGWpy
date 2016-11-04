import os
import unittest
import tempfile, shutil

class TestTask(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.local_testdir = 'tmp.Tests'
        self.local_tmpdir = os.path.join(
            self.local_testdir, os.path.split(self.tmpdir)[-1])

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def recover_tmpdir(self):
        """Debug tool to copy the execution directory locally."""
        if not os.path.exists(self.local_testdir):
            os.mkdir(self.local_testdir)
        shutil.copytree(self.tmpdir, self.local_tmpdir, symlinks=True)

    def assertCompleted(self, task):
        completed = task.get_status() == task._STATUS_COMPLETED
        if not completed:
            self.recover_tmpdir()
        assert completed, 'Task failed. Directory copied to: {}'.format(self.local_tmpdir)

