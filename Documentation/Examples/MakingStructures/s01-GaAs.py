"""
Construct a Structure object and write the structure file.

BGWpy relies on pymatgen.Structure objects to construct
the primitive cells for all calculations.

See http://pymatgen.org/ for more information.
"""

from pathlib import Path

import numpy as np
import pymatgen

# Construct the structure object.
acell_angstrom = 5.6535
rprim = np.array([[0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]]) * acell_angstrom
structure = pymatgen.core.Structure(
    lattice=pymatgen.core.lattice.Lattice(rprim),
    species=["Ga", "As"],
    coords=[3 * [0.0], 3 * [0.25]],
)

# Create a directory to store the structure.
dirname = "01-GaAs"
if not Path(dirname).exists():
    Path(dirname).mkdir()

# Write file in Crystallographic Information Framework.
# This the format defined by the International Union of Crystallography.
structure.to(filename=str(Path(dirname) / "GaAs.cif"))

# Write in json format. This is the prefered format
# since it preserves the above definition of the unit cell.
structure.to(filename=str(Path(dirname) / "GaAs.json"))
