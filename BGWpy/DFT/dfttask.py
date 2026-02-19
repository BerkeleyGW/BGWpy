"""Base DFT task and flow classes for BGWpy.

This module provides base classes for DFT calculations that can be used
with different DFT codes (Quantum Espresso, Abinit).
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy import ndarray

from BGWpy.BGW import KgridTask
from BGWpy.core import MPITask, Workflow

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray
    from pymatgen.core import Structure

__all__ = ["DFTFlow", "DFTTask"]


class DFTTask(MPITask):
    """Base class for DFT calculations.

    Handles structure, pseudopotentials and k-points grids.

    Attributes
    ----------
    flavor : str
        DFT code flavor ('qe' or 'abinit').
    pseudo_dir : str
        Path to the directory containing pseudopotential files.
    pseudos : list[str]
        List of pseudopotential filenames.
    structure : Structure | None
        Structure object containing unit cell information.
    kgridtask : KgridTask
        Task for generating k-point grids.
    version : int
        Version of the DFT code (for QE compatibility).
    """

    flavor: str
    _pseudo_dir: str
    pseudos: list[str]
    structure: Structure
    kgridtask: KgridTask
    version: int
    _ngkpt: NDArray[np.float64] | None
    _kshift: NDArray[np.float64] | None
    _qshift: NDArray[np.float64] | None

    def __init__(self, dirname: str, **kwargs: Any) -> None:
        """Initialize a DFT task.

        Parameters
        ----------
        dirname : str
            Directory in which the files are written and the code is executed.

        Other Parameters
        ----------------
        flavor : str, default='qe'
            DFT code used for density and wavefunctions ('qe' or 'abinit').
        pseudo_dir : str, optional
            Path to the directory containing pseudopotential files.
            Defaults to dirname.
        pseudos : list[str], optional
            List of pseudopotential files. Defaults to empty list.
        structure : Structure
            Structure object containing unit cell information. Required.
        version : int, default=6
            Version of QE (only used if flavor is 'qe').
        **kwargs : Any
            Additional keyword arguments passed to parent class.
        """
        super().__init__(dirname, **kwargs)

        self.flavor = kwargs.pop("flavor", "qe")
        self.pseudo_dir = kwargs.get("pseudo_dir", self.dirname)
        self.pseudos = kwargs.get("pseudos", [])
        if "structure" not in kwargs:
            msg = "structure is required for DFT tasks"
            raise ValueError(msg)
        self.structure = kwargs["structure"]

        # Initialize property backing attributes
        # Subclasses may set these via property setters
        self._ngkpt = None
        self._kshift = None
        self._qshift = None

        # Store ngkpt, kshift, qshift if provided in kwargs
        if "ngkpt" in kwargs:
            self.ngkpt = kwargs["ngkpt"]
        if "kshift" in kwargs:
            self.kshift = kwargs["kshift"]
        if "qshift" in kwargs:
            self.qshift = kwargs["qshift"]

        # Patches for newer versions of QE. Originally BGWpy was written for
        # QE v5 but currently defaults to QE v6.
        if self.is_flavor_QE:
            self.version = kwargs.pop("version", 6)

        # This task is not part of a workflow.
        # It is executed on-the-fly and leaves no trace (clean_after=True).
        self.kgridtask = KgridTask(dirname=dirname, **kwargs)

    @property
    def is_flavor_QE(self) -> bool:
        """Check if using Quantum Espresso flavor."""
        return any(tag in self.flavor.lower() for tag in ["qe", "espresso"])

    @property
    def is_flavor_abinit(self) -> bool:
        """Check if using Abinit flavor."""
        return any(tag in self.flavor.lower() for tag in ["abi", "abinit"])

    def get_kpts(
        self,
        **kwargs: Any,
    ) -> tuple[list[list[float]] | NDArray[np.float64], list[float] | NDArray[np.float64]]:
        """Get the k-points and their weights.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments including:
            - symkpt : bool, default=True
                Use symmetries to reduce the k-point grid.
            - structure : Structure
                Mandatory if symkpt is True.
            - ngkpt : list(3), int, optional
                K-points grid dimensions.
            - kshift : list(3), float, optional
                Relative shift of the k-points grid.
            - qshift : list(3), float, optional
                Absolute shift of the k-points grid.
            - kpts : list[list[float]], optional
                Explicit k-points (used if ngkpt not provided).
            - wtks : list[float], optional
                Explicit k-point weights (used if ngkpt not provided).

        Returns
        -------
        kpts : list[list[float]] | NDArray[np.float64]
            List of k-points.
        wtks : list[float] | NDArray[np.float64]
            List of k-point weights.
        """
        symkpt: bool = kwargs.get("symkpt", True)

        if "ngkpt" in kwargs:
            if symkpt:
                kpts, wtks = self.kgridtask.get_kpoints()
            else:
                kpts, wtks = self.kgridtask.get_kpt_grid_nosym()
        else:
            # If ngkpt not provided, kpts and wtks are required
            kpts, wtks = kwargs["kpts"], kwargs["wtks"]

        return kpts, wtks

    def check_pseudos(self) -> None:
        """Check that pseudopotential files exist.

        Warns if any pseudopotential file is not found.
        """
        for pseudo in self.pseudos:
            fname = os.path.relpath(Path(self.dirname) / self.pseudo_dir / pseudo)
            if not Path(fname).exists():
                warnings.warn(f"Pseudopotential not found:\n{fname}", stacklevel=2)

    @property
    def pseudo_dir(self) -> str:
        """Get the pseudopotential directory."""
        return self._pseudo_dir

    @pseudo_dir.setter
    def pseudo_dir(self, value: str) -> None:
        """Set the pseudopotential directory.

        If an absolute path is given, it is used as-is.
        Otherwise, a relative path from dirname is computed.
        """
        if Path(value).is_absolute():
            self._pseudo_dir = str(value)
        else:
            self._pseudo_dir = os.path.relpath(str(value), self.dirname)

    @property
    def ngkpt(self) -> NDArray[np.float64] | None:
        """Get the k-point grid dimensions."""
        return self._ngkpt

    @ngkpt.setter
    def ngkpt(self, ngkpt: ArrayLike) -> None:
        """Set the k-point grid dimensions."""
        self._ngkpt = np.array(ngkpt)

    @property
    def kshift(self) -> NDArray[np.float64] | None:
        """Get the k-point shift."""
        return self._kshift

    @kshift.setter
    def kshift(self, kshift: ArrayLike) -> None:
        """Set the k-point shift."""
        self._kshift = np.array(kshift)

    @property
    def qshift(self) -> NDArray[np.float64] | None:
        """Get the q-point shift."""
        return self._qshift

    @qshift.setter
    def qshift(self, qshift: ArrayLike) -> None:
        """Set the q-point shift."""
        self._qshift = np.array(qshift)

    @property
    def kqshift(self) -> ndarray:
        """Get the combined k+q shift.

        Returns
        -------
        ndarray
            The sum of kshift and qshift * ngkpt.

        Raises
        ------
        ValueError
            If kshift, qshift, or ngkpt is None.
        """
        if self._kshift is None or self._qshift is None or self._ngkpt is None:
            msg = "kshift, qshift, and ngkpt must all be set to compute kqshift"
            raise ValueError(msg)
        return self._kshift + self._qshift * self._ngkpt


# =========================================================================== #


class DFTFlow(Workflow, DFTTask):
    """Workflow for DFT calculations.

    This class combines Workflow and DFTTask functionality, allowing
    multiple DFT tasks to be organized and executed as a workflow.

    Attributes
    ----------
    Inherits all attributes from Workflow and DFTTask.
    """

    def __init__(self, dirname: str | None = None, **kwargs: Any) -> None:
        """Initialize a DFT workflow.

        Parameters
        ----------
        dirname : str | None, optional
            Directory in which the workflow is executed.
            If None, will use default from Task base class.

        Other Parameters
        ----------------
        flavor : str, default='qe'
            DFT code used for density and wavefunctions.
        pseudo_dir : str
            Path to the directory containing pseudopotential files.
        pseudos : list[str]
            List of pseudopotential files.
        structure : Structure
            Structure object containing unit cell information.
        **kwargs : Any
            Additional keyword arguments passed to parent classes.

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
