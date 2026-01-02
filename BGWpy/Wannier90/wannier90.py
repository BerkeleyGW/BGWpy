from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

if TYPE_CHECKING:
    from pymatgen.core import Structure

from BGWpy.core import Writable
from BGWpy.core.F90io import arr_str

__all__ = ["Wannier90Input"]


class Wannier90Input(Writable):
    structure: Structure

    def __init__(
        self,
        structure: Structure,
        nbnd: int,
        nwann: int,
        kbounds: ArrayLike,
        klabels: list[str],
        mp_grid: ArrayLike,
        kpts: ArrayLike,
        projections: dict[str, str] | str | list[str] | None = None,
        **variables: Any,
    ) -> None:
        self.structure = structure
        self.nbnd = nbnd
        self.nwann = nwann
        # Convert ArrayLike inputs to concrete numpy arrays
        self.kbounds: NDArray[np.float64] = np.asarray(kbounds, dtype=np.float64)
        self.klabels = klabels
        self.mp_grid: NDArray[np.float64] = np.asarray(mp_grid, dtype=np.float64)
        self.kpts: NDArray[np.float64] = np.asarray(kpts, dtype=np.float64)
        self.projections = projections
        self.variables = variables

    def __str__(self) -> str:
        # Validate input dimensions
        if len(self.mp_grid) != 3:
            msg = f"mp_grid must have exactly 3 elements, got {len(self.mp_grid)}"
            raise ValueError(msg)

        if len(self.klabels) != len(self.kbounds):
            msg = f"klabels and kbounds must have same length, got {len(self.klabels)} and {len(self.kbounds)}"
            raise ValueError(msg)

        result_str = ""

        result_str += f"num_bands = {self.nbnd}\n"
        result_str += f"num_wann = {self.nwann}\n"
        result_str += "dis_froz_max = 12.1\n"
        result_str += "bands_plot = .true.\n"

        for key, val in self.variables.items():
            result_str += f"{key} = {val}\n"

        result_str += "\nBegin Atoms_Frac\n"
        for site in self.structure.sites:
            frac_coords = site.frac_coords.copy()
            for i in range(3):
                if abs(frac_coords[i]) > 0.5:
                    frac_coords[i] += -1.0 * np.sign(frac_coords[i])
            result_str += f"  {site.specie.symbol}  {arr_str(frac_coords)}\n"
        result_str += "End Atoms_Frac\n"

        result_str += "\nBegin Projections\n"
        if self.projections:
            if isinstance(self.projections, dict):
                for key, val in self.projections.items():
                    result_str += f"{key} : {val}\n"
            elif isinstance(self.projections, str):
                result_str += self.projections + "\n"
            elif hasattr(self.projections, "__iter__"):
                for proj in self.projections:
                    result_str += proj + "\n"
        else:
            result_str += "random\n"
        result_str += "End Projections\n"

        result_str += "\nBegin kpoint_path\n"
        for i in range(len(self.kbounds) - 1):
            result_str += self.klabels[i] + " "
            for j in range(3):
                result_str += f"{self.kbounds[i][j]:.4f} "
            result_str += self.klabels[i + 1] + " "
            for j in range(3):
                result_str += f"{self.kbounds[i + 1][j]:.4f} "
            result_str += "\n"
        result_str += "End kpoint_path\n"

        result_str += "\nBegin Unit_Cell_Cart\n"
        result_str += "Angstrom\n"
        latt_vec = np.round(self.structure.lattice.matrix, 8)
        result_str += arr_str(latt_vec) + "\n"
        result_str += "End Unit_Cell_Cart\n"

        result_str += "mp_grid      = {} {} {}\n".format(*self.mp_grid)

        result_str += "\nBegin kpoints\n"
        for k in self.kpts:
            for ki in k:
                result_str += f"{ki:.9f} "
            result_str += "1.0\n"
        result_str += "End kpoints\n"

        return result_str
