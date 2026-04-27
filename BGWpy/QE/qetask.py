from __future__ import annotations

import os
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

from BGWpy.config import flavors
from BGWpy.core import IOTask
from BGWpy.core.util import exec_from_dir
from BGWpy.DFT import DFTTask

# Public
__all__ = ["QeTask"]


class QeTask(DFTTask, IOTask):
    """Base class for Quantum Espresso calculations."""

    _TAG_JOB_COMPLETED = "JOB DONE"
    _use_hdf5_qe = flavors["use_hdf5_qe"]

    prefix: str
    savedir: str

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """
        Arguments
        ---------

        dirname : str | Path
            Directory in which the files are written and the code is executed.
            Will be created if needed.

        Keyword arguments
        -----------------

        See also:
            BGWpy.DFT.DFTTask

        """

        super().__init__(dirname, **kwargs)

        self.prefix = kwargs["prefix"]
        self.savedir = self.prefix + ".save"

        self.runscript["PW"] = kwargs.get("PW", "pw.x")
        self.runscript["PWFLAGS"] = kwargs.get("PWFLAGS", "")

    def exec_from_savedir(self) -> AbstractContextManager[None]:
        """Execute from the save directory."""
        original = Path.cwd()
        if original.resolve() == Path(self.dirname).resolve():
            return exec_from_dir(self.savedir)
        return exec_from_dir(Path(self.dirname) / self.savedir)

    def write(self) -> None:
        """Write the task files."""
        self.check_pseudos()
        super().write()
        with self.exec_from_dirname():
            self.input.write()  # type: ignore[attr-defined]
            if not Path(self.savedir).exists():
                Path(self.savedir).mkdir(parents=True, exist_ok=True)

    @property
    def pseudo_dir(self) -> str:
        return self._pseudo_dir

    @pseudo_dir.setter
    def pseudo_dir(self, value: str | Path) -> None:
        if Path(value).is_absolute():
            self._pseudo_dir = str(value)
        else:
            self._pseudo_dir = os.path.relpath(str(value), self.dirname)
        input_obj = getattr(self, "input", None)
        if input_obj is not None and hasattr(input_obj, "control"):  # type: ignore[attr-defined]
            input_obj.control["pseudo_dir"] = self._pseudo_dir  # type: ignore[attr-defined]
