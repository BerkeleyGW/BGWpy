from __future__ import print_function

import os
import warnings
from numpy import array

from ..core import MPITask, Workflow
from ..BGW import KgridTask

# Public
__all__ = ['DFTTask', 'DFTFlow']

class DFTTask(MPITask):
    """
    Base class for DFT calculations.
    Handles structure, pseudopotentials and k-points grids.
    """

    def __init__(self, dirname, **kwargs):
        """
        Keyword Arguments
        -----------------

        flavor : str ['qe', 'abinit']
            DFT code used for density and wavefunctions.
        pseudo_dir : str
            Path to the directory containing pseudopotential files.
        pseudos : list, str
            List of pseudopotential files.
        """

        # too restrictive
        #self.ngkpt  = kwargs.pop('ngkpt', 3*[1])
        #self.kshift = kwargs.pop('kshift', 3*[.0])
        #self.qshift = kwargs.pop('qshift', 3*[.0])

        super(DFTTask, self).__init__(dirname, **kwargs)

        self.flavor     = kwargs.pop('flavor',  'qe')
        self.pseudo_dir = kwargs.get('pseudo_dir', self.dirname)
        self.pseudos    = kwargs.get('pseudos', [])
        self.structure  = kwargs.get('structure')

        # Patches for newer verisons of qe. Originally bgwpy was written for
        # QE v5 but currently defaults to QE v6.
        if self.is_flavor_QE:
            self.version = kwargs.pop('version',  6)

        # This task is not part of a workflow.
        # It is executed on-the-fly and leaves no trace (clean_after=True). 
        self.kgridtask = KgridTask(dirname=dirname, **kwargs)

    @ property
    def is_flavor_QE(self):
        return any([tag in self.flavor.lower() for tag in ['qe', 'espresso']])

    @ property
    def is_flavor_abinit(self):
        return any([tag in self.flavor.lower() for tag in ['abi', 'abinit']])

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
                kpts, wtks = self.kgridtask.get_kpoints()
            else:
                kpts, wtks = self.kgridtask.get_kpt_grid_nosym()
        else:
            kpts, wtks = kwargs['kpts'], kwargs['wtks']

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

    @property
    def ngkpt(self):
        return self._ngkpt

    @ngkpt.setter
    def ngkpt(self, ngkpt):
        self._ngkpt = array(ngkpt)

    @property
    def kshift(self):
        return self._kshift

    @kshift.setter
    def kshift(self, kshift):
        self._kshift = array(kshift)

    @property
    def qshift(self):
        return self._qshift

    @qshift.setter
    def qshift(self, qshift):
        self._qshift = array(qshift)

    @property
    def kqshift(self):
        return self.kshift + self.qshift * self.ngkpt


# =========================================================================== #


class DFTFlow(Workflow, DFTTask):

    def __init__(self, *args, **kwargs):
        """
        Keyword Arguments
        -----------------

        flavor : str ['qe', 'abinit']
            DFT code used for density and wavefunctions.
        pseudo_dir : str
            Path to the directory containing pseudopotential files.
        pseudos : list, str
            List of pseudopotential files.
        """
        super(DFTFlow, self).__init__(*args, **kwargs)

        #self.flavor     = kwargs.pop('flavor',  'qe')
        self.pseudo_dir = kwargs.get('pseudo_dir', self.dirname)
        self.pseudos = kwargs.get('pseudos', [])
        self.structure = kwargs.get('structure')

