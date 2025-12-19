from __future__ import annotations

from pathlib import Path
from typing import Any

from .constructor import get_scf_input
from .qetask import QeTask

# Public
__all__ = ["QeScfTask"]


class QeScfTask(QeTask):
    """Charge density calculation."""

    _TASK_NAME = "SCF"

    _input_fname = "scf.in"
    _output_fname = "scf.out"

    def __init__(self, dirname: str, **kwargs: Any) -> None:
        """
        Arguments
        ---------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.


        Keyword arguments
        -----------------
        (All mandatory unless specified otherwise)

        prefix : str
            Prefix required by QE as a rootname.
        pseudo_dir : str
            Directory in which pseudopotential files are found.
        pseudos : list, str
            Pseudopotential files.
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ecutwfc : float
            Energy cutoff for the wavefunctions
        ngkpt : list(3), int, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
            K-points are either specified using ngkpt or using kpts and wtks.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
        symkpt : bool (True), optional
            Use symmetries for the k-point grid generation.
        kpts : 2D list(nkpt,3), float, optional of k-points.
            K-points are either specified using ngkpt or using kpts and wtks.
        wtks : list(nkpt), float, optional
            Weights of each k-point.


        Properties
        ----------

        charge_density_fname : str
            Path to the charge density file produced ('charge-density.dat' or
            'charge-density.hdf5').

        data_file_fname : str
            Path to the xml data file produced ('data-file.xml').

        spin_polarization_fname : str, optional
            Path to the spin polarization file produced ('spin-polarization.dat').
        """

        super().__init__(dirname, **kwargs)

        kpts, wtks = self.get_kpts(**kwargs)

        # Input file
        assert self.structure is not None, "structure must be provided"
        self.input = get_scf_input(
            self.prefix,
            self.pseudo_dir,
            self.pseudos,
            self.structure,
            kwargs["ecutwfc"],
            kpts,
            wtks,
        )

        if "variables" in kwargs:
            self.input.set_variables(kwargs["variables"])

        self.input.fname = self._input_fname

        # Run script
        self.runscript.append(
            f"$MPIRUN $PW $PWFLAGS -in {self._input_fname} &> {self._output_fname}"
        )

    @property
    def charge_density_fname(self) -> str:
        name = "charge-density.hdf5" if self._use_hdf5_qe else "charge-density.dat"
        return str(Path(self.dirname) / self.savedir / name)

    @property
    def spin_polarization_fname(self) -> str:
        return str(Path(self.dirname) / self.savedir / "spin-polarization.dat")

    @property
    def data_file_fname(self) -> str:
        # It seems newer versions of QE have switched from data-file.xml to
        # data-file-schema.xml
        if self.version >= 6:
            return str(Path(self.dirname) / self.savedir / "data-file-schema.xml")
        return str(Path(self.dirname) / self.savedir / "data-file.xml")
