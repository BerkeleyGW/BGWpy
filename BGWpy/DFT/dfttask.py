from __future__ import annotations

import os
import warnings
from pathlib import Path

from numpy import array

from BGWpy.BGW import KgridTask
from BGWpy.core import MPITask, Workflow

# Public
__all__ = ["DFTFlow", "DFTTask"]


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
        pseudos : list, str of pseudopotential files.
        """

        # too restrictive

        super().__init__(dirname, **kwargs)

        self.flavor = kwargs.pop("flavor", "qe")
        self.pseudo_dir = kwargs.get("pseudo_dir", self.dirname)
        self.pseudos = kwargs.get("pseudos", [])
        self.structure = kwargs.get("structure")

        # Initialize property backing attributes
        # Subclasses may set these via property setters
        self._ngkpt = None
        self._kshift = None
        self._qshift = None

        # Patches for newer verisons of qe. Originally bgwpy was written for
        # QE v5 but currently defaults to QE v6.
        if self.is_flavor_QE:
            self.version = kwargs.pop("version", 6)

        # This task is not part of a workflow.
        # It is executed on-the-fly and leaves no trace (clean_after=True).
        self.kgridtask = KgridTask(dirname=dirname, **kwargs)

    @property
    def is_flavor_QE(self):
        return any(tag in self.flavor.lower() for tag in ["qe", "espresso"])

    @property
    def is_flavor_abinit(self):
        return any(tag in self.flavor.lower() for tag in ["abi", "abinit"])

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

        symkpt = kwargs.get("symkpt", True)

        if "ngkpt" in kwargs:
            if symkpt:
                kpts, wtks = self.kgridtask.get_kpoints()
            else:
                kpts, wtks = self.kgridtask.get_kpt_grid_nosym()
        else:
            # If ngkpt not provided, kpts and wtks are required
            kpts, wtks = kwargs["kpts"], kwargs["wtks"]

        return kpts, wtks

    def check_pseudos(self):
        """Check that pseudopotential files exist."""
        for pseudo in self.pseudos:
            fname = os.path.relpath(Path(self.dirname) / self.pseudo_dir / pseudo)
            if not Path(fname).exists():
                warnings.warn(f"Pseudopotential not found:\n{fname}", stacklevel=2)

    _pseudo_dir = "./"

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
    def __init__(self, dirname=None, **kwargs):
        """
        Initialize a DFT workflow.

        Parameters
        ----------
        dirname : str or Path, optional
            Directory in which the workflow is executed.
            If None, will use default from Task base class.

        Keyword Arguments
        -----------------
        flavor : str ['qe', 'abinit']
            DFT code used for density and wavefunctions.
        pseudo_dir : str
            Path to the directory containing pseudopotential files.
        pseudos : list, str of pseudopotential files.
        structure : pymatgen.Structure
            Structure object containing unit cell information.

        Notes
        -----
        This class uses multiple inheritance (Workflow, DFTTask).
        The dirname parameter can be passed as either a positional or
        keyword argument. All DFT-specific attributes are initialized
        via the DFTTask.__init__ in the super() chain.
        """
        # Handle dirname to work with both Workflow and DFTTask signatures
        # Workflow expects (tasks=None, *args, **kwargs)
        # DFTTask expects (dirname, **kwargs)
        if dirname is not None:
            kwargs.setdefault("dirname", dirname)

        # Call super().__init__ which will chain through:
        # Workflow.__init__ -> DFTTask.__init__ -> MPITask.__init__ -> Task.__init__
        super().__init__(**kwargs)

        # All instance attributes are already set by DFTTask.__init__
        # No need to duplicate the initialization here
