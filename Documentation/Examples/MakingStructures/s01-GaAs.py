"""
Construct a Structure object and write the structure file.

BGWpy relies on pymatgen.Structure objects to construct
the primitive cells for all calculations.

See http://pymatgen.org/ for more information.
"""

from pathlib import Path

import numpy as np
from pymatgen.core import Structure
from pymatgen.core.lattice import Lattice

if __name__ == "__main__":
    # Construct the structure object.
    acell_angstrom = 5.6535
    rprim = np.array([[0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]]) * acell_angstrom
    structure = Structure(
        lattice=Lattice(rprim),
        species=["Ga", "As"],
        coords=[3 * [0.0], 3 * [0.25]],
    )

    # Create a directory to store the structure.
    dirname = Path("01-GaAs")
    dirname.mkdir(exist_ok=True)

    # Write file in Crystallographic Information Framework.
    # This the format defined by the International Union of Crystallography.
    structure.to(filename=str(dirname / "GaAs.cif"))

    # Write in json format. This is the prefered format
    # since it preserves the above definition of the unit cell.
    structure.to(filename=str(dirname / "GaAs.json"))
