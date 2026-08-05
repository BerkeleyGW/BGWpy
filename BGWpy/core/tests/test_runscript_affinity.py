"""Tests for the CPU affinity repair applied when a run script is executed."""

import os
import tempfile
import unittest
import warnings
from pathlib import Path

need_affinity = unittest.skipUnless(
    hasattr(os, "sched_getaffinity") and (os.cpu_count() or 1) > 1,
    "requires Linux affinity control and more than one CPU",
)


@need_affinity
class TestWidenCpuAffinity(unittest.TestCase):
    """A driver pinned to one CPU must not pass that mask on to MPI ranks."""

    def setUp(self):
        from BGWpy.core import runscript

        self.runscript = runscript
        self.original_affinity = os.sched_getaffinity(0)
        # The warning fires once per process; reset so each test sees it.
        runscript._warned_cpu_affinity = False
        self.addCleanup(os.sched_setaffinity, 0, self.original_affinity)

    def test_widens_when_pinned_to_one_cpu(self):
        """A single-CPU mask is widened, and the previous one is returned."""
        os.sched_setaffinity(0, {next(iter(self.original_affinity))})

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            previous = self.runscript._widen_cpu_affinity()

        self.assertEqual(len(previous), 1)
        self.assertGreater(len(os.sched_getaffinity(0)), 1)
        self.assertEqual(len(caught), 1)
        self.assertIn("single CPU", str(caught[0].message))

    def test_no_op_when_not_pinned(self):
        """An unrestricted mask is left alone, with nothing reported."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            previous = self.runscript._widen_cpu_affinity()

        self.assertIsNone(previous)
        self.assertEqual(os.sched_getaffinity(0), self.original_affinity)
        self.assertEqual(len(caught), 0)

    def test_warns_only_once(self):
        """A flow runs many tasks; the warning must not repeat for each."""
        one_cpu = {next(iter(self.original_affinity))}

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for _ in range(3):
                os.sched_setaffinity(0, one_cpu)
                self.runscript._widen_cpu_affinity()

        self.assertEqual(len(caught), 1)

    def test_disabled_by_configuration(self):
        """fix_cpu_affinity = False leaves a deliberate pinning in place."""
        from BGWpy.config import default_runscript

        one_cpu = {next(iter(self.original_affinity))}
        os.sched_setaffinity(0, one_cpu)

        original_flag = default_runscript.get("fix_cpu_affinity", True)
        default_runscript["fix_cpu_affinity"] = False
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                previous = self.runscript._widen_cpu_affinity()
        finally:
            default_runscript["fix_cpu_affinity"] = original_flag

        self.assertIsNone(previous)
        self.assertEqual(os.sched_getaffinity(0), one_cpu)
        self.assertEqual(len(caught), 0)

    def test_child_process_is_not_confined(self):
        """The point of the exercise: the launched script sees every CPU."""
        from BGWpy.core.runscript import RunScript

        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "cpus"
            script = Path(tmpdir) / "run.sh"
            script.write_text(f"nproc > {report}\n")

            os.sched_setaffinity(0, {next(iter(self.original_affinity))})
            runscript = RunScript()
            runscript.fname = str(script)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                returncode = runscript.run()

            self.assertEqual(returncode, 0)
            self.assertGreater(int(report.read_text().strip()), 1)
            # The driver's own mask is restored once the child has finished.
            self.assertEqual(len(os.sched_getaffinity(0)), 1)


if __name__ == "__main__":
    unittest.main()
