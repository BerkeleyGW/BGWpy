from __future__ import print_function, division

from ..core import Writable
from .data import input_variable_blocks
from .utils import listify
from .variable import InputVariable, SpecialInputVariable

__all__ = ['AbinitInput']


class AbinitInput(Writable):
    """Abinit input file."""

    def __init__(self, **kwargs):

        super(AbinitInput, self).__init__(**kwargs)

        self.variables = dict()
        self.variables_blocks = list()

        for (name, register) in input_variable_blocks.items():
            self.variables_blocks.append(VariableBlock(name, register))
        self.variables_blocks.append(VariableBlock('Other'))

    def __str__(self):
        lines = list()
        
        # Clear blocks
        for block in self.variables_blocks:
            block.clear()

        # Sort variables in blocks
        for name, value in self.variables.items():
            variable = SpecialInputVariable(name, value)
            placed = False
            for block in self.variables_blocks:
                if variable.basename in block.register:
                    block.append(variable)
                    placed = True
                    break
            if not placed:
                self.variables_blocks[-1].append(variable)

        # Make the string
        for block in self.variables_blocks:
            if block:
                lines.append(str(block))
                lines.append('')
            block.clear()

        return '\n'.join(lines) + '\n'

    def clear(self):
        """Clear variables."""
        self.variables.clear()
        for block in self.variables_blocks:
            block.clear()

    def set_variable(self, name, value):  # TODO ndecimal | ndigits 
        """Set a single variable."""
        self.variables[name] = value

    def set_variables(self, variables=dict(), dataset=0, **kwargs):
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
        variables.update(kwargs)

        if not dataset:
            dataset = ['']

        for ds in listify(dataset):
            for (key, val) in variables.items():
                newkey = key + str(ds)
                self.set_variable(newkey, val)

    def set_structure(self, structure):
        variables = structure_to_abivars(structure)
        self.set_variables(variables)


# =========================================================================== #


class VariableBlock(list):
    """A block of abinit variables."""

    def __init__(self, title, register=''):

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
        lines = ['#== {} ==#'.format(self.title)]
        for variable in sorted(self):
            svar = str(variable)
            if svar:
                lines.append(svar)
        return '\n'.join(lines)



# =========================================================================== #


def structure_to_abivars(structure):
    """Get abinit variables from a pymatgen.Structure object."""
    d = structure.to_abivars()
    d['typat'] = d['typat'].tolist()
    d['xred'] = d['xred'].tolist()
    d['rprim'] = d['rprim'].tolist()
    return d

