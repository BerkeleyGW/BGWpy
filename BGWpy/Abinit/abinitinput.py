from __future__ import annotations

import numpy as np

from BGWpy.core import Writable

from .abidata import input_variable_blocks
from .utils import listify
from .variable import SpecialInputVariable

__all__ = ["AbinitInput"]


class AbinitInput(Writable):
    """Abinit input file."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.variables = {}
        self.variables_blocks = []
        self.decimals = {}

        for name, register in input_variable_blocks.items():
            self.variables_blocks.append(VariableBlock(name, register))
        self.variables_blocks.append(VariableBlock("Other"))

    def __str__(self):
        lines = []

        # Clear blocks
        for block in self.variables_blocks:
            block.clear()

        # Sort variables in blocks
        for name, value in self.variables.items():
            variable = SpecialInputVariable(name, value)
            if name in self.decimals:
                variable.decimals = self.decimals[name]
            for block in self.variables_blocks:
                if variable.basename in block.register:
                    block.append(variable)
                    break
            else:
                self.variables_blocks[-1].append(variable)

        # Make the string
        for block in self.variables_blocks:
            if block:
                lines.append(str(block))
                lines.append("")
            block.clear()

        return "\n".join(lines) + "\n"

    def clear(self):
        """Clear variables."""
        self.variables.clear()
        for block in self.variables_blocks:
            block.clear()

    def __getitem__(self, key: str):
        """Get a variable value by key."""
        return self.variables[key]

    def __setitem__(self, key: str, value):
        """Set a variable value by key."""
        self.variables[key] = value

    def set_variable(self, name, value, decimals=None):  # TODO ndecimal or ndigits
        """a single variable."""
        self.variables[name] = value
        if value is None:
            del self.variables[name]
            return
        if decimals is not None:
            self.decimals[name] = decimals

    def set_variables(self, variables, dataset=0, **kwargs):
        """
        Sets variables by providing a dictionary, or expanding a dictionary,
        and possibly append them by a dataset index.

        Example::

            >> kpoint_grid_shifted = {
            >>     'kptopt' : 1,
            >>     'ngkpt' : 3*[4],
            >>     'nshiftk' : 4,
            >>     'shiftk' : [[0.5,0.5,0.5],
            >>                 [0.5,0.0,0.0],
            >>                 [0.0,0.5,0.0],
            >>                 [0.0,0.0,0.5]],}
            >>
            >> kpoint_grid_unshifted = {
            >>     'kptopt' : 1,
            >>     'ngkpt' : 3*[4],
            >>     'nshiftk' : 1,
            >>     'shiftk' : [0,0,0],}
            >>
            >> cell = {
            >>     'ntypat' : 1
            >>     'znucl'  : 6.0
            >>     'natom'  : 2
            >>     'typat'  : [1, 1]
            >>     'xred'   : [[0,0,0],[0.25,0.25,0.25]]
            >>     'acell'  : 3*[6.9]
            >>     'rprim'  : [[0.0,0.5,0.5],
            >>                 [0.5,0.0,0.5],
            >>                 [0.5,0.5,0.0]]}
            >>
            >> f = InputFile()
            >> f.set_variables(ndtset=3, ecut=4.0, ecutsm=0.5)
            >>
            >> f.set_variables(cell)    # These two lines
            >> f.set_variables(**cell)  # are equivalent.
            >>
            >> # Here we append a dataset index at the end of all variables.
            >> f.set_variables(kpoint_grid_shifted, dataset=1)
            >> f.set_variables(kpoint_grid_unshifted, dataset=[2, 3])
            >>
            >> f.write('myfile.in')  # The name was not set at initialization.
        """

        if not dataset:
            dataset = [""]

        for ds in listify(dataset):
            for key, val in variables.items():
                newkey = key + str(ds)
                self.set_variable(newkey, val, **kwargs)

    def set_structure(self, structure):
        variables = structure_to_abivars(structure)
        self.set_variables(variables)


# =========================================================================== #


class VariableBlock(list):
    """A block of abinit variables."""

    def __init__(self, title, register=""):
        # The block title
        self.title = title

        # A register of all possible input variable.
        if isinstance(register, str):
            self.register = register.split()
        else:
            self.register = list(register)

    def clear(self):
        del self[:]

    def __str__(self):
        lines = [f"#== {self.title} ==#"]
        for variable in sorted(self):
            svar = str(variable)
            if svar:
                lines.append(svar)
        return "\n".join(lines)


# =========================================================================== #


def structure_to_abivars(structure):
    """Get abinit variables from a pymatgen.Structure object."""

    from scipy import constants

    bohr_to_ang = constants.physical_constants["Bohr radius"][0] / constants.angstrom
    rprim = structure.lattice.matrix / bohr_to_ang

    xred = [site.frac_coords.round(14).tolist() for site in structure.sites]

    natom = structure.num_sites
    ntypat = structure.n_elems

    znucl_atom = structure.atomic_numbers

    itypat = 0
    typat = []
    znucl = []
    for z in znucl_atom:
        if z not in znucl:
            itypat += 1
            znucl.append(z)
            typat.append(itypat)
        else:
            i = znucl.index(z)
            typat.append(i + 1)

    return {
        "rprim": rprim.tolist(),
        "acell": np.ones(3, dtype=float).tolist(),
        "natom": natom,
        "ntypat": ntypat,
        "znucl": znucl,
        "typat": typat,
        "xred": xred,
    }
