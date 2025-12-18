import pymatgen

structure = pymatgen.Structure(  # type: ignore[attr-defined]
    lattice=pymatgen.core.lattice.Lattice(  # type: ignore[attr-defined]
        [[0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]]
    ).scale(5.4309456887829**3 / 4),
    species=["Si", "Si"],
    coords=[3 * [-0.125], 3 * [0.125]],
)

structure.to(filename="Si.cif")
structure.to(filename="Si.json")
