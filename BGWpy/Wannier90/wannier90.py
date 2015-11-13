import numpy as np

from ..core import Writable, arr_str

__all__ = ['Wannier90Input']

class Wannier90Input(Writable):

    def __init__(self, structure, nbnd, nwann, kbounds, klabels,
                       mp_grid, kpts, projections=None, **variables):

        self.structure = structure
        self.nbnd = nbnd
        self.nwann = nwann
        self.kbounds = kbounds
        self.klabels = klabels
        self.mp_grid = mp_grid
        self.kpts = kpts
        self.projections = projections
        self.variables = variables

    def __str__(self):

        S = ''

        S += 'num_bands = {}\n'.format(self.nbnd)
        S += 'num_wann = {}\n'.format(self.nwann)
        S += 'dis_froz_max = 12.1\n'
        S += 'bands_plot = .true.\n'

        for key, val in self.variables.items():
            S += '{} = {}\n'.format(key, val)

        S += '\nBegin Atoms_Frac\n'
        for site in self.structure.sites:
            frac_coords = site.frac_coords
            for i in range(3):
                if abs(frac_coords[i]) > .5:
                    frac_coords[i] += -1. * np.sign(frac_coords[i])
            S += '  {}  {}\n'.format(site.specie.symbol, arr_str(frac_coords))
        S += 'End Atoms_Frac\n'


        S += '\nBegin Projections\n'
        if self.projections:
            if isinstance(self.projections, dict):
                for key, val in self.projections.items():
                    S += '{} : {}\n'.format(key, val)
            elif '__iter__' in dir(self.projections):
                for proj in self.projections:
                    S += proj + '\n'
        else:
            S += 'random\n'
        S += 'End Projections\n'

        S += '\nBegin kpoint_path\n'
        for i in range(len(self.kbounds)-1):
            S += self.klabels[i] + ' '
            for j in range(3):
                S += '{:.4f} '.format(self.kbounds[i][j])
            S += self.klabels[i+1] + ' '
            for j in range(3):
                S += '{:.4f} '.format(self.kbounds[i+1][j])
            S += '\n'
        S += 'End kpoint_path\n'

        S += '\nBegin Unit_Cell_Cart\n'
        S += 'Angstrom\n'
        latt_vec = np.round(self.structure.lattice_vectors(), 8)
        S += arr_str(latt_vec) + '\n'
        S += 'End Unit_Cell_Cart\n'

        S += 'mp_grid      = {} {} {}\n'.format(*self.mp_grid)

        S += '\nBegin kpoints\n'
        for k in self.kpts:
            for ki in k:
                S += '{:.9f} '.format(ki)
            S += '1.0\n'
        S += 'End kpoints\n'

        return S


