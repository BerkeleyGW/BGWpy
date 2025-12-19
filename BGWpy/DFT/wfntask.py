from __future__ import annotations

from abc import ABC, abstractmethod

from .dfttask import DFTTask

__all__ = ["WfnBgwConverter", "WfnTask"]


class WfnTask(DFTTask, ABC):
    """Abstract base class for wavefunction calculation tasks.

    Subclasses must implement the wfn_fname method to specify
    the output wavefunction file name for their specific DFT code.
    """

    @property
    @abstractmethod
    def wfn_fname(self) -> str:
        """Return the wavefunction file name.

        Returns
        -------
        str
            The wavefunction file name for this task.
        """
        raise NotImplementedError


class WfnBgwConverter(DFTTask, ABC):
    """Abstract base class for wavefunction to BGW format conversion tasks.

    Subclasses must implement the input and output file name methods
    for their specific DFT code's wavefunction format.
    """

    @property
    @abstractmethod
    def wfn_fname_in(self) -> str:
        """Return the input wavefunction file name.

        Returns
        -------
        str
            The input wavefunction file name (DFT code format).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def wfn_fname_out(self) -> str:
        """Return the output wavefunction file name.

        Returns
        -------
        str
            The output wavefunction file name (BGW format).
        """
        raise NotImplementedError
