from __future__ import annotations

from pathlib import Path

from BGWpy.core import Task
from BGWpy.tests import TestTask


class TestBasicTask(TestTask):
    """Test basic functions of Task."""

    def get_task(self, **kwargs):
        kwargs.setdefault("dirname", Path(self.tmpdir) / "Task")
        return Task(**kwargs)

    def test_task_write(self):
        """Test Task writing."""
        task = self.get_task()
        task.write()
        assert Path(task.dirname).exists()
        assert (Path(task.dirname) / task.runscript.fname).exists()

    def test_run(self):
        """Test Runscript run function."""
        task = self.get_task()
        task.write()
        task.run()
