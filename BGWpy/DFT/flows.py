from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .dfttask import DFTFlow

if TYPE_CHECKING:
    from typing import Any

__all__ = ["WfnBgwFlow"]


class WfnBgwFlow(DFTFlow, ABC):
    """Abstract base class for wavefunction calculation and conversion to BGW.

    This class defines the interface that concrete implementations (e.g.,
    QeBgwFlow, AbinitBgwFlow) must implement. It cannot be instantiated directly.

    Abstract Properties
    -------------------
    rho_fname : str
        Charge density file name for BerkeleyGW
    wfn_fname : str
        Wavefunctions file name for BerkeleyGW
    vxc_fname : str
        Exchange-correlation potential file name for BerkeleyGW
    vxc_dat_fname : str
        Exchange-correlation potential data file name for BerkeleyGW

    Notes
    -----
    Subclasses must implement all abstract properties to be instantiable.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def rho_fname(self) -> str:
        """str: The charge density file name for BerkeleyGW.

        Must be implemented by subclasses to return the appropriate
        charge density file name for the DFT code being used.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def wfn_fname(self) -> str:
        """str: The wavefunctions file name for BerkeleyGW.

        Must be implemented by subclasses to return the appropriate
        wavefunctions file name for the DFT code being used.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def vxc_fname(self) -> str:
        """str: The exchange-correlation potential file name for BerkeleyGW.

        Must be implemented by subclasses to return the appropriate
        vxc file name for the DFT code being used. Some codes may
        raise NotImplementedError if they use vxc_dat_fname instead.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def vxc_dat_fname(self) -> str:
        """str: The exchange-correlation potential data file name for BerkeleyGW.

        Must be implemented by subclasses to return the appropriate
        vxc data file name for the DFT code being used. Some codes may
        raise NotImplementedError if they use vxc_fname instead.
        """
        raise NotImplementedError

    @property
    def kih_dat_fname(self) -> str:
        """str: The KIH matrix elements file name for BerkeleyGW.

        Only Quantum Espresso's pw2bgw writes this file; other codes leave
        this property raising NotImplementedError.
        """
        msg = f"{type(self).__name__} does not produce a kih.dat file."
        raise NotImplementedError(msg)
