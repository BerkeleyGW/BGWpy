from __future__ import print_function

import os
import warnings

from ..core import Task
from ..BGW.kgrid import get_kpt_grid, get_kpt_grid_nosym

# Public
__all__ = ['DFTTask']


class DFTTask(Task):
    """
    Base class for DFT calculations.
    Handles k-points grids and pseudopotentials.
    """

    def __init__(self, dirname, **kwargs):
        """
        Keyword Arguments
        -----------------

        pseudo_dir : str
            Path to the directory containing pseudopotential files.
        pseudos : list, str
            List of pseudopotential files.
        """
        super(DFTTask, self).__init__(dirname, **kwargs)

        self.pseudo_dir = kwargs.get('pseudo_dir', self.dirname)
        self.pseudos = kwargs.get('pseudos', [])

    def get_kpts(self, **kwargs):
        """
        Get the k-points and their weights.

        Keyword Arguments
        -----------------

        symkpt : bool (True)
            Use symmetries to reduce the k-point grid.
        structure : pymatgen.Structure object
            Mandatory if symkpt.
        ngkpt : list(3), float, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
            K-points are either specified using ngkpt or using kpts and wtks.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.

        """

        symkpt = kwargs.get('symkpt', True)

        if 'ngkpt' in kwargs:
            if symkpt:
                kpts, wtks = get_kpt_grid(
                            kwargs['structure'],
                            kwargs['ngkpt'],
                            kshift=kwargs.get('kshift',[0,0,0]),
                            qshift=kwargs.get('qshift',[0,0,0]),
                            )
            else:
                kpts, wtks = get_kpt_grid_nosym(
                            kwargs['ngkpt'],
                            kshift=kwargs.get('kshift',[0,0,0]),
                            qshift=kwargs.get('qshift',[0,0,0]),
                            )
        else:
            kpts = kwargs['kpts']
            wtks = kwargs['wtks']

        return kpts, wtks

    def check_pseudos(self):
        """Check that pseudopotential files exist."""
        for pseudo in self.pseudos:
            fname = os.path.relpath(
                    os.path.join(self.dirname, self.pseudo_dir, pseudo))
            if not os.path.exists(fname):
                warnings.warn('Pseudopotential not found:\n{}'.format(fname))

    _pseudo_dir = './'
    @property
    def pseudo_dir(self):
        return self._pseudo_dir

    @pseudo_dir.setter
    def pseudo_dir(self, value):
        if os.path.realpath(value) == value.rstrip(os.path.sep):
            self._pseudo_dir = value
        else:
            self._pseudo_dir = os.path.relpath(value, self.dirname)

