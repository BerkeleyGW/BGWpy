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
        # Use 4 processors for pw2bgw in tests (small scale; pw2bgw crashes if given too many processes)
        kwargs.setdefault("nproc", 4)

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

    def test_diagonalization_cg(self):
        """Test that diago_david_ndim is removed when diagonalization is changed to 'cg'."""
        task = self.get_scftask(
            variables={
                "electrons": {
                    "diagonalization": "cg",
                }
            }
        )
        # Check that diagonalization was set to 'cg'
        assert task.input.electrons["diagonalization"] == "cg"
        # Check that diago_david_ndim was removed
        assert "diago_david_ndim" not in task.input.electrons
        # Check that other parameters are still present
        assert task.input.electrons["diago_full_acc"] is True
        assert task.input.electrons["conv_thr"] == 1.0e-10

    def test_diagonalization_david(self):
        """Test that diago_david_ndim is kept when diagonalization is 'david'."""
        task = self.get_scftask(
            variables={
                "electrons": {
                    "diagonalization": "david",
                    "diago_david_ndim": 8,
                }
            }
        )
        # Check that diagonalization is 'david'
        assert task.input.electrons["diagonalization"] == "david"
        # Check that diago_david_ndim is present and was updated
        assert task.input.electrons["diago_david_ndim"] == 8
