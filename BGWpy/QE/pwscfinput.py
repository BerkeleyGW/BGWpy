from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

import numpy as np

from BGWpy.core import Card, Namelist, Writable, fortran_str

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray
    from pymatgen.core import Structure


class PWscfInput(Writable):
    _structure: Structure | None = None
    _pseudos: list[str] | None = None

    control: Namelist
    system: Namelist
    electrons: Namelist
    ions: Namelist
    cell: Namelist
    atomic_species: Card
    atomic_positions: Card
    k_points: Card
    cell_parameters: Card
    constraints: Card
    occupations: Card
    atomic_forces: Card

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.control = Namelist("control")
        self.system = Namelist("system")
        self.electrons = Namelist("electrons")
        self.ions = Namelist("ions")
        self.cell = Namelist("cell")
        self.atomic_species = Card("ATOMIC_SPECIES", "")
        self.atomic_positions = Card("ATOMIC_POSITIONS", "crystal", quotes=False)
        self.k_points = Card("K_POINTS", "")
        self.cell_parameters = Card("CELL_PARAMETERS", "angstrom")
        self.constraints = Card("CONSTRAINTS", "")
        self.occupations = Card("OCCUPATIONS", "")
        self.atomic_forces = Card("ATOMIC_FORCES", "")

        if "variables" in kwargs:
            self.set_variables(kwargs["variables"])

    def _isrelax(self) -> bool:
        """True if this is a relaxation calculation."""
        calculation = str(self.control.get("calculation")).lower()
        return calculation in ("relax", "md", "vc-relax", "vc-md")

    def _isvc(self) -> bool:
        """True if the volume of the cell can change."""
        calculation = str(self.control.get("calculation")).lower()
        return calculation in ("vc-relax", "vc-md")

    def _isfreebrav(self) -> bool:
        """True if the bravais lattis is free."""
        ibrav = self.system.get("ibrav")
        if ibrav is None:
            return False
        return int(ibrav) == 0

    def _isconstrained(self) -> bool:
        """True if the ion dynamics is constrained."""
        return self.ions.get("ion_dynamics") in ("verlet", "damp")

    def _is_manual_occ(self) -> bool:
        """True if the occupation is specified manually."""
        return str(self.system.get("occupations", "")).lower() == "from_input"

    def set_variables(self, variables: dict[str, Any]) -> None:
        """
        Use a nested dictionary to set variables.
        The items in the variables dictionary should
        be dictionaries for namelist input variables,
        and lists for card input variables.
        In case of card input variables, the first item of the list
        must correspond to the option.

        Example:

        pwscfinput.set_variables({
            'control' : {
                'verbosity' : 'high',
                'nstep' : 1,
                },
            'system' : {
                'nbnd' : 10,
                },
            'electrons' : {
                'conv_thr' : 1e-6,
                },
            'cell_parameters' : ['angstrom',
                1., 0., 0.,
                0., 1., 0.,
                0., 0., 1.,
                ],
            'atomic_species' : ['',
                'Ga', 69.723, 'path/to/Ga/pseudo',
                'As', 74.921, 'path/to/As/pseudo',
                ],
            })
        """
        for key, val in variables.items():
            if key not in dir(self):
                continue
            obj = getattr(self, key)

            if isinstance(obj, Namelist):
                obj.update(val)
                # If diagonalization method is changed from 'david', remove david-specific parameters
                if (
                    key == "electrons"
                    and "diagonalization" in val
                    and val["diagonalization"] != "david"
                    and "diago_david_ndim" in obj
                ):
                    del obj["diago_david_ndim"]
            elif isinstance(obj, Card):
                obj.option = val[0]
                while obj:
                    obj.pop()
                obj.extend(val[1:])

    def __str__(self) -> str:
        # Perform checks
        self.check_pseudos_names()

        result_str = ""
        result_str += str(self.control)
        result_str += str(self.system)
        result_str += str(self.electrons)

        if self.ions or self._isrelax():
            result_str += str(self.ions)

        if self.cell or self._isvc():
            result_str += str(self.cell)

        if self.cell_parameters or self._isfreebrav():
            result_str += str(self.cell_parameters)

        # This card is special, since only parts of it need quotes.
        result_str += f"{self.atomic_species.name} {self.atomic_species.option}\n"
        for val in self.atomic_species:
            result_str += (
                f"   {fortran_str(val[0], quotes=False)} {fortran_str(val[1:], quotes=True)}\n"
            )

        result_str += str(self.atomic_positions)

        if self.constraints or self._isconstrained():
            result_str += str(self.constraints)

        if self.occupations or self._is_manual_occ():
            result_str += str(self.occupations)

        if self.atomic_forces:
            result_str += str(self.atomic_forces)

        result_str += str(self.k_points)

        return result_str

    def set_kpoints_crystal(
        self,
        kpts: Sequence[Sequence[float]] | NDArray[np.float64],
        wtks: Sequence[float] | NDArray[np.float64],
    ) -> None:
        self.k_points.option = "crystal"
        self.k_points.append(len(kpts))
        for k, w in zip(kpts, wtks, strict=True):
            self.k_points.append([*k, w])

    @property
    def structure(self) -> Structure | None:
        return self._structure

    @structure.setter
    def structure(self, structure: Structure) -> None:
        """A pymatgen.Structure object."""
        self._structure = structure

        # system specifications
        self.system["ibrav"] = 0
        self.system["nat"] = structure.num_sites
        self.system["ntyp"] = structure.n_elems

        # cell parameters
        self.cell_parameters.option = "angstrom"
        # for vec in structure.lattice_vectors():
        for vec in structure.lattice.matrix:
            self.cell_parameters.append(np.round(vec, 8))

        # atomic species
        types_of_specie = sorted(set(structure.species), key=structure.species.index)
        for element in types_of_specie:
            self.atomic_species.append([element.symbol, float(element.atomic_mass)])

        if self.pseudos:
            for i, pseudo in enumerate(self.pseudos):
                self.atomic_species[i].append(pseudo)

        # atomic positions
        self.atomic_positions.option = "crystal"
        for site in structure.sites:
            frac_coords = list(site.frac_coords)
            for i in range(3):
                if abs(frac_coords[i]) > 0.5:
                    frac_coords[i] += -1.0 * np.sign(frac_coords[i])
            self.atomic_positions.append([site.specie.symbol, *[round(x, 10) for x in frac_coords]])

    @property
    def pseudos(self) -> list[str] | None:
        return self._pseudos

    @pseudos.setter
    def pseudos(self, pseudos: list[str]) -> None:
        self._pseudos = pseudos
        if self.atomic_species:
            if len(pseudos) != len(self.atomic_species):
                msg = f"Number of pseudopotentials ({len(pseudos)}) must match number of atomic species ({len(self.atomic_species)})"
                raise ValueError(msg)
            for i, pseudo in enumerate(pseudos):
                # Replace pseudopotential if already has 3 elements, append if only has 2
                if len(self.atomic_species[i]) == 3:
                    self.atomic_species[i][2] = pseudo
                else:
                    self.atomic_species[i].append(pseudo)

    def check_pseudos_names(self) -> None:
        for symbol, _mass, pseudo in self.atomic_species:
            if symbol.lower() not in pseudo.lower():
                warnings.warn(f"Suspicious pseudo name for atom {symbol}: {pseudo}", stacklevel=2)
