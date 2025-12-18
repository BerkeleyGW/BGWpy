from copy import copy
from pathlib import Path

from BGWpy.core import MPITask
from BGWpy.tests import TestTask


class TestMPITask(TestTask):
    """Test basic functions of Task."""

    def get_task(self, **kwargs):
        kwargs.setdefault("dirname", Path(self.tmpdir) / "Task")
        return MPITask(**kwargs)

    def test_mpi_variables(self):
        """Test MPI variables."""
        common = {
            "mpirun": "mpirun",
            "nproc": 6,
            "nproc_flag": "-n",
            "nodes": 2,
            "nodes_flag": "-N",
            "nproc_per_node": 3,
            "nproc_per_node_flag": "--npernode",
        }

        kwargs = copy(common)
        kwargs["mpirun"] = "mpiexec"
        task = self.get_task(**kwargs)
        assert task.mpirun_variable == "mpiexec -n 6 --npernode 3 -N 2"

        kwargs = copy(common)
        kwargs["nodes"] = None
        task = self.get_task(**kwargs)
        assert task.mpirun_variable == "mpirun -n 6 --npernode 3"

        kwargs = copy(common)
        kwargs["nproc"] = None
        task = self.get_task(**kwargs)
        assert task.mpirun_variable == "mpirun --npernode 3 -N 2"

        kwargs = copy(common)
        kwargs["nodes"] = None
        kwargs["nproc_per_node"] = None
        task = self.get_task(**kwargs)
        assert task.mpirun_variable == "mpirun -n 6"
