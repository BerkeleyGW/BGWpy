import numpy as np
import pymatgen

acell_angstrom = 5.6535
rprim = np.array([[0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]]) * acell_angstrom
structure = pymatgen.Structure(
    lattice=pymatgen.core.lattice.Lattice(rprim),
    species=["Ga", "As"],
    coords=[3 * [0.0], 3 * [0.25]],
)

structure.to(filename="GaAs.cif")
structure.to(filename="GaAs.json")
