from abc import ABC, abstractmethod

from .dfttask import DFTFlow

__all__ = ["WfnBgwFlow"]


class WfnBgwFlow(DFTFlow, ABC):
    """Abstract base class for wavefunction calculation and conversion to BGW.

    This class defines the interface that concrete implementations (e.g.,
    QeBgwFlow, AbinitBgwFlow) must implement. It cannot be instantiated directly.

    Abstract Properties
    -------------------
    rho_fname : Charge density file name
    wfn_fname : Wavefunctions file name
    vxc_fname : Exchange-correlation potential file name
    vxc_dat_fname : Exchange-correlation potential data file name

    Notes
    -----
    Subclasses must implement all abstract methods and properties to be instantiable.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def rho_fname(self):
        """str: The charge density file name for BerkeleyGW.

        Must be implemented by subclasses to return the appropriate
        charge density file name for the DFT code being used.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def wfn_fname(self):
        """str: The wavefunctions file name for BerkeleyGW.

        Must be implemented by subclasses to return the appropriate
        wavefunctions file name for the DFT code being used.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def vxc_fname(self):
        """str: The exchange-correlation potential file name for BerkeleyGW.

        Must be implemented by subclasses to return the appropriate
        vxc file name for the DFT code being used. Some codes may
        raise NotImplementedError if they use vxc_dat_fname instead.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def vxc_dat_fname(self):
        """str: The exchange-correlation potential data file name for BerkeleyGW.

        Must be implemented by subclasses to return the appropriate
        vxc data file name for the DFT code being used. Some codes may
        raise NotImplementedError if they use vxc_fname instead.
        """
        raise NotImplementedError
