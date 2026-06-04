from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .constructor import get_bands_input
from .qetask import QeTask

# Public
__all__ = ["QeWfnTask"]


class QeWfnTask(QeTask):
    """Wavefunctions calculation."""

    _TASK_NAME = "Wfn"

    _input_fname = "wfn.in"
    _output_fname = "wfn.out"

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """
        Arguments
        ---------

        dirname : str | Path
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
        nbnd : int, optional
            Number of bands to be computed.
        charge_density_fname : str
            Path to the charge density file produced
            by a density calculation ('charge-density.dat' or
            'charge-density.hdf5').
        data_file_fname : str
            Path to the xml data file produced
            by a density calculation ('data-file.xml').
        spin_polarization_fname : str, optional
            Path to the spin polarization file produced
            by a density calculation ('spin-polarization.dat').
        ekin_density_fname : str, optional
            Path to the kinetic energy density file produced
            by a density calculation ('ekin-density.dat' or 'ekin-density.hdf5').
            Only required for meta-GGA functionals.
        ngkpt : list(3), float, optional
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

        """

        super().__init__(dirname, **kwargs)
        self.add_pseudos_copy()

        kpts, wtks = self.get_kpts(**kwargs)

        self.charge_density_fname = kwargs["charge_density_fname"]
        if "spin_polarization_fname" in kwargs:
            self.spin_polarization_fname = kwargs["spin_polarization_fname"]
        if "ekin_density_fname" in kwargs:
            self.ekin_density_fname = kwargs["ekin_density_fname"]

        self.data_file_fname = kwargs["data_file_fname"]

        # Input file
        self.input = get_bands_input(
            self.prefix,
            self.pseudo_dir,
            self.pseudos,
            self.structure,
            kwargs["ecutwfc"],
            kpts,
            wtks,
            nbnd=kwargs.get("nbnd"),
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
        return self._charge_density_fname

    @charge_density_fname.setter
    def charge_density_fname(self, value: str | Path) -> None:
        self._charge_density_fname = str(value)
        name = "charge-density.hdf5" if self._use_hdf5_qe else "charge-density.dat"
        dest = Path(self.savedir) / name
        self.update_link(value, dest)

    @property
    def ekin_density_fname(self) -> str:
        return self._ekin_density_fname

    @ekin_density_fname.setter
    def ekin_density_fname(self, value: str | Path | None) -> None:
        self._ekin_density_fname = str(value) if value else ""
        if value:
            name = "ekin-density.hdf5" if self._use_hdf5_qe else "ekin-density.dat"
            dest = Path(self.savedir) / name
            self.update_link(value, dest)

    @property
    def spin_polarization_fname(self) -> str:
        return self._spin_polarization_fname

    @spin_polarization_fname.setter
    def spin_polarization_fname(self, value: str | Path) -> None:
        self._spin_polarization_fname = str(value)
        dest = Path(self.savedir) / "spin-polarization.dat"
        self.update_link(value, dest)

    @property
    def data_file_fname(self) -> str:
        return self._data_file_fname

    @data_file_fname.setter
    def data_file_fname(self, value: str | Path) -> None:
        self._data_file_fname = str(value)
        if self.version >= 6:
            dest = Path(self.savedir) / "data-file-schema.xml"
        else:
            dest = Path(self.savedir) / "data-file.xml"
        self.update_copy(value, dest)

    def add_pseudos_copy(self) -> None:
        """
        Add instructions in the runscript to copy the pseudopotential files.
        This is necessary, because otherwise, Quantum Espresso expect that
        the relative path for the pseudopotential directory be the same
        for the wavefunction calculation as for the density calculation.
        """
        pseudo_dir = Path(self.pseudo_dir)
        sourcedir = pseudo_dir if pseudo_dir.is_absolute() else (Path(self.dirname) / pseudo_dir)

        for pseudo in self.pseudos:
            source = sourcedir / pseudo
            dest = Path(self.savedir) / pseudo
            self.update_copy(source, dest)

    # Override parent property to trigger pseudopotential copying when pseudo_dir changes.
    # This ensures pseudos are copied to the save directory, which is required by QE.
    @property
    def pseudo_dir(self) -> str:
        return str(self._pseudo_dir)

    @pseudo_dir.setter
    def pseudo_dir(self, value: str | Path) -> None:
        # Check if value is an absolute path
        if Path(value).is_absolute():
            self._pseudo_dir = str(value)
        else:
            self._pseudo_dir = os.path.relpath(str(value), self.dirname)
        input_obj = getattr(self, "input", None)
        if input_obj is not None and hasattr(input_obj, "control"):
            input_obj.control["pseudo_dir"] = self._pseudo_dir
        if hasattr(self, "pseudos"):
            self.add_pseudos_copy()
