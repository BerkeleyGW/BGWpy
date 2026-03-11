from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from BGWpy.core import IOTask
from BGWpy.DFT import DFTTask

from .abinitinput import AbinitInput

__all__ = ["AbinitTask"]


class AbinitTask(DFTTask, IOTask):
    """Base class for Abinit calculations."""

    _TAG_JOB_COMPLETED = "Calculation completed"

    def __init__(self, dirname: str, **kwargs: Any) -> None:
        """
        Arguments
        ---------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.


        Keyword arguments
        -----------------

        prefix : str
            Prefix used as a rootname for abinit calculations.
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ngkpt : list(3), int, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
        input_variables : dict
            Any other input variables for the Abinit input file.

        See also:
            BGWpy.DFT.DFTTask
            BGWpy.BGW.KgridTask

        """

        super().__init__(dirname, **kwargs)

        self.prefix = kwargs.get("prefix", "abinit")

        self.input = AbinitInput(fname=self.prefix + ".in")
        self.input.set_structure(self.structure)

        # Handle k-points and symmetries
        if self.kgridtask is None:
            msg = "'ngkpt' is required for AbinitTask."
            raise ValueError(msg)
        ((kpt, wtk), (symrel, tnons)) = self.kgridtask.get_kpoints_and_sym()
        nsym = len(symrel)
        if not kwargs.get("symkpt", True):
            kpt, wtk = self.kgridtask.get_kpt_grid_nosym()

        # Transpose all symmetry matrices
        symrel = np.linalg.inv(symrel.reshape((-1, 3, 3)).transpose((0, 2, 1)))
        symrel = np.array(symrel, dtype=np.int64)

        # A 2pi factor is added to tnons by kgrid for phase factor calculations
        tnons = np.round(tnons / (2 * np.pi), 5)

        self.input.set_variables({"symrel": symrel, "tnons": tnons, "nsym": nsym})
        # Convert kpt and wtk to numpy arrays
        kpt_array = np.asarray(kpt, dtype=np.float64)
        wtk_array = np.asarray(wtk, dtype=np.float64)
        self.set_kpoints(kpt_array, wtk_array)

        self.input.set_variables(kwargs.get("input_variables", {}))

        self.runscript["ABINIT"] = kwargs.get("ABINIT", "abinit")
        self.runscript.append(f"$MPIRUN $ABINIT < {self.filesfile_basename} &> {self.log_basename}")

    @property
    def output_fname(self) -> str:
        first = Path(self.dirname) / self.output_basename
        for s in reversed("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            last = Path(str(first) + s)
            if last.exists():
                return str(last)
        return str(first)

    @property
    def filesfile_basename(self) -> str:
        return self.prefix + ".files"

    @property
    def output_basename(self) -> str:
        return self.prefix + ".out"

    @property
    def log_basename(self) -> str:
        return self.prefix + ".log"

    @property
    def input_data_dir(self) -> str:
        return str(Path(self.dirname) / "input_data")

    @property
    def out_data_dir(self) -> str:
        return str(Path(self.dirname) / "out_data")

    @property
    def tmp_data_dir(self) -> str:
        return str(Path(self.dirname) / "tmp_data")

    @property
    def idat_root(self) -> str:
        """The root name for input data files."""
        return str(Path(self.input_data_dir) / "idat")

    @property
    def odat_root(self) -> str:
        """The root name for output data files."""
        return str(Path(self.out_data_dir) / "odat")

    @property
    def tmp_root(self) -> str:
        """The root name for temporaty data files."""
        return str(Path(self.tmp_data_dir) / "tmp")

    def get_odat(self, datatype: str, dtset: int = 0) -> str:
        """
        Returns an output data file name.

        Args:
            datatype:
                The type of datafile, e.g. 'DEN' or 'WFK'.

            dtset:
                The dataset index from which to take the data file.
                If 0 (the default), no dataset index is used.
        """
        fname = self.odat_root

        if int(dtset) > 0:
            fname += "_DS" + str(dtset)

        fname += "_" + datatype.lstrip("_")

        return fname

    def get_idat(self, datatype: str, dtset: int = 0) -> str:
        """
        Returns an input data file name.

        Args:
            datatype:
                The type of datafile, e.g. 'DEN' or 'WFK'.

            dtset:
                The dataset index from which to take the data file.
                If 0 (the default), no dataset index is used.
        """
        fname = self.idat_root

        if int(dtset) > 0:
            fname += "_DS" + str(dtset)

        fname += "_" + datatype.upper().lstrip("_")

        return fname

    def get_filesfile_content(self) -> str:
        result_str = ""
        result_str += os.path.relpath(self.input_fname, self.dirname) + "\n"
        result_str += self.output_basename + "\n"
        for path in (self.idat_root, self.odat_root, self.tmp_root):
            result_str += os.path.relpath(path, self.dirname) + "\n"

        for pseudo in self.pseudos:
            pseudo_path = Path(self.pseudo_dir) / pseudo
            result_str += str(pseudo_path) + "\n"  # pseudo_dir is already a relpath

        return result_str

    def write(self) -> None:
        # Main directory, etc...
        super().write()

        self.check_pseudos()

        # Sub-directories
        for d in (self.input_data_dir, self.out_data_dir, self.tmp_data_dir):
            if not Path(d).exists():
                Path(d).mkdir(parents=True, exist_ok=True)

        with self.exec_from_dirname():
            with open(self.filesfile_basename, "w") as f:
                f.write(self.get_filesfile_content())

            self.input.write()

    def set_kpoints(
        self, kpt: NDArray[np.float64], wtk: NDArray[np.float64], **kwargs: Any
    ) -> None:
        """kpoint variables."""
        wtk_normalized = np.array(wtk, dtype=np.float64) / sum(wtk)
        self.input.set_variables(
            {
                "kptopt": 0,
                "kpt": kpt,
                "nkpt": len(kpt),
                "ngkpt": None,
                "nshiftk": None,
                "shiftk": None,
            }
        )
        self.input.set_variable("wtk", wtk_normalized, decimals=16)

    def set_ngkpt(
        self,
        ngkpt: NDArray[np.float64],
        shiftk: list[list[float]] | None = None,
        **kwargs: Any,
    ) -> None:
        """kpoint variables."""
        if shiftk is None:
            shiftk = [3 * [0.0]]
        self.input.set_variables(
            {
                "kptopt": kwargs.get("kptopt", 1),
                "ngkpt": ngkpt,
                "nshiftk": len(shiftk),
                "shiftk": shiftk,
                "kpt": None,
                "wtk": None,
                "nkpt": None,
            }
        )
