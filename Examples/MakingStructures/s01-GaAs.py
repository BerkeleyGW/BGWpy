"""
Construct a Structure object and write the structure file.

BGWpy relies on pymatgen.Structure objects to construct
the primitive cells for all calculations.

See http://pymatgen.org/ for more information.
"""
import os
import numpy as np
import pymatgen

# Construct the structure object.
acell_angstrom =  5.6535
rprim = np.array([[.0,.5,.5],[.5,.0,.5],[.5,.5,.0]]) * acell_angstrom
structure = pymatgen.Structure(
    lattice = pymatgen.core.lattice.Lattice(rprim),
    species= ['Ga', 'As'],
    coords = [3*[.0], 3*[.25]],
    )

# Create a directory to store the structure.
dirname = '01-GaAs'
if not os.path.exists(dirname):
    os.mkdir(dirname)

# Write file in Crystallographic Information Framework.
# This the format defined by the International Union of Crystallography.
structure.to(filename=os.path.join(dirname, 'GaAs.cif'))

# Write in json format. This is the prefered format
# since it preserves the above definition of the unit cell.
structure.to(filename=os.path.join(dirname, 'GaAs.json'))

