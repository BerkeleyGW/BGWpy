from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path


class TestTask(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.local_testdir = "tmp.Tests"
        self.local_tmpdir = Path(self.local_testdir) / Path(self.tmpdir).name

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def recover_tmpdir(self):
        """Debug tool to copy the execution directory locally."""
        if not Path(self.local_testdir).exists():
            Path(self.local_testdir).mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.tmpdir, self.local_tmpdir, symlinks=True)

    def assertCompleted(self, task):
        completed = task.get_status() == task._STATUS_COMPLETED
        if not completed:
            self.recover_tmpdir()
        assert completed, f"Task failed. Directory copied to: {self.local_tmpdir}"
