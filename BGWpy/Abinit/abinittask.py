from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from BGWpy.config import flavors
from BGWpy.core import IOTask
from BGWpy.DFT import DFTTask

from .abinitinput import AbinitInput

__all__ = ["AbinitTask"]


class AbinitTask(DFTTask, IOTask):
    """Base class for Abinit calculations."""

    _TAG_JOB_COMPLETED = "Calculation completed"

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """
        Arguments
        ---------

        dirname : str | Path
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
        # Since we override pseudos method, we need to initialize the input first.
        self.prefix = kwargs.get("prefix", "abinit")
        self.input = AbinitInput(fname=self.prefix + ".in")

        super().__init__(dirname, **kwargs)

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

        abivars = kwargs.get("input_variables", {})

        # Disable netcdf output (can be set as default behavior in Abinit)
        abivars.setdefault('iomode', 1)  # Disable netcdf output

        # Set filenames variables (must be within dirname)
        filenames = {
            'output_file' :  Path(self.output_fname).relative_to(self.dirname),
            'indata_prefix' : Path(self.idat_root).relative_to(self.dirname),
            'outdata_prefix' : Path(self.odat_root).relative_to(self.dirname),
            'tmpdata_prefix' : Path(self.tmp_root).relative_to(self.dirname),
            }
        abivars.update(filenames)

        # Finally set all variables
        self.input.set_variables(abivars)

        self.runscript["ABINIT"] = kwargs.get("ABINIT", "abinit")

        inp = Path(self.input_fname).relative_to(self.dirname)
        self.runscript.append(f"$MPIRUN $ABINIT {inp} &> {self.log_basename}")

    @property
    def output_fname(self) -> str:
        # This is always the last output file produced by Abinit
        return str(Path(self.dirname) / self.output_basename)

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
        return str(Path(self.input_data_dir) / "i")

    @property
    def odat_root(self) -> str:
        """The root name for output data files."""
        return str(Path(self.out_data_dir) / "o")

    @property
    def tmp_root(self) -> str:
        """The root name for temporaty data files."""
        return str(Path(self.tmp_data_dir) / "t")

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

    def write(self) -> None:
        # Main directory, etc...
        super().write()

        self.check_pseudos()

        # Sub-directories
        for d in (self.input_data_dir, self.out_data_dir, self.tmp_data_dir):
            if not Path(d).exists():
                Path(d).mkdir(parents=True, exist_ok=True)

        with self.exec_from_dirname():
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


    # Override parent property
    @property
    def pseudo_dir(self) -> str:
        """Get the pseudopotential directory."""
        return self._pseudo_dir

    @pseudo_dir.setter
    def pseudo_dir(self, value: str | Path) -> None:
        """Set the pseudopotential directory.

        Accepts a path as str or Path.
        If an absolute path is given, it is used as-is.
        Otherwise, a relative path from dirname is computed.
        """
        value_str = str(value)
        if not value_str:
            msg = "pseudo_dir must not be empty"
            raise ValueError(msg)
        if Path(value_str).is_absolute():
            self._pseudo_dir = value_str
        else:
            self._pseudo_dir = os.path.relpath(value_str, self.dirname)

        # Abinit lets you set the pseudo directory as an environment variable,
        # but here we explicitly write it in the input.
        self.input.set_variable('pp_dirpath', self._pseudo_dir)


    _pseudos = []
    @property
    def pseudos(self) -> str:
        """The list of pseudopotentials files relative to pseudo_dir."""
        return self._pseudos

    @pseudos.setter
    def pseudos(self, value: str | [str]) -> None:
        """Set the pseudopotential directory.

        Accepts a path as str or Path.
        If an absolute path is given, it is used as-is.
        Otherwise, a relative path from dirname is computed.
        """
        if isinstance(value, str):
            self._pseudos = [value]
        else:
            self._pseudos = value

        # Pass value to input object
        self.input.set_variable('pseudos', self._pseudos)

