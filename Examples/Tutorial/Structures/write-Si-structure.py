import pymatgen

structure = pymatgen.Structure(
    lattice = pymatgen.core.lattice.Lattice([[.0,.5,.5],[.5,.0,.5],[.5,.5,.0]]).scale(5.4309456887829**3/4),
    species= ['Si', 'Si'],
    coords = [3*[-.125], 3*[.125]],
    )

structure.to(filename='Si.cif')
structure.to(filename='Si.json')

