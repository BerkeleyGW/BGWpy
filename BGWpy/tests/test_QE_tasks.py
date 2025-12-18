from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from BGWpy import Qe2BgwTask, QeScfTask, QeWfnTask, Structure, data

from . import TestTask

# Note: The tests are redundant, because
# tests cannot be interdependent.


class TestQETasksMaker(TestTask):
    _structure_fname = data.structure_GaAs

    # Common arguments for tasks.
    common_kwargs: ClassVar[dict] = {
        "prefix": "GaAs",
        "pseudo_dir": data.pseudo_dir,
        "pseudos": data.pseudos_GaAs,
        "structure": Structure.from_file(_structure_fname),
        "ngkpt": [2, 2, 2],
        "kshift": [0.5, 0.5, 0.5],
        "ecutwfc": 8.0,
        "nbnd": 9,
    }

    def get_scftask(self, **kwargs):
        """Construct a QeScfTask."""
        for key, val in self.common_kwargs.items():
            kwargs.setdefault(key, val)

        kwargs.setdefault("dirname", Path(self.tmpdir) / "Density")
        return QeScfTask(**kwargs)

    def get_wfntask(self, scftask, **kwargs):
        """Construct a QeWfnTask."""
        for key, val in self.common_kwargs.items():
            kwargs.setdefault(key, val)

        kwargs.setdefault("dirname", Path(self.tmpdir) / "Wfn")

        return QeWfnTask(
            charge_density_fname=scftask.charge_density_fname,
            data_file_fname=scftask.data_file_fname,
            **kwargs,
        )

    def get_pw2bgwtask(self, wfntask, **kwargs):
        """Construct a Qe2BgwTask."""
        for key, val in self.common_kwargs.items():
            kwargs.setdefault(key, val)

        kwargs.setdefault("wfn_fname", "wfn.cplx")

        return Qe2BgwTask(dirname=wfntask.dirname, **kwargs)


class TestQETasks(TestQETasksMaker):
    def test_scftask(self):
        """Test density calculation."""
        task = self.get_scftask()
        task.write()
        task.run()
        task.report()
        self.assertCompleted(task)

    def test_wfntask(self):
        """Test density and wavefunction calculation."""
        scftask = self.get_scftask()
        wfntask = self.get_wfntask(scftask)

        for task in (scftask, wfntask):
            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

    def test_pw2bgwtask(self):
        """Test density and wavefunction calculation."""
        scftask = self.get_scftask()
        wfntask = self.get_wfntask(scftask)
        pw2bgwtask = self.get_pw2bgwtask(wfntask)

        for task in (scftask, wfntask, pw2bgwtask):
            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)
