"""Inteqp task for quasiparticle band structure interpolation.

This module provides the InteqpTask class for interpolating quasiparticle
corrections from a coarse k-point grid onto a fine k-point grid using
BerkeleyGW's inteqp.x executable.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING

from BGWpy.core import BasicInputFile

from .bgwtask import BGWTask

if TYPE_CHECKING:
    from typing import Any

__all__ = ["InteqpInput", "InteqpTask"]


class InteqpInput(BasicInputFile):
    """Input file for the inteqp code.

    Generates an ``inteqp.inp`` file for BerkeleyGW's inteqp.x executable,
    which interpolates quasiparticle corrections from a coarse k-point grid
    onto a fine k-point grid.

    Parameters
    ----------
    *keywords : str
        Any keyword flags (i.e. bare keywords with no value) to include in
        the input file, such as ``delaunay_interpolation`` or
        ``kpt_interpolation_linear``.
    **variables : Any
        Any keyword-value pairs to include in the input file. The four
        required band count keywords default to 1 if not specified:

        - ``number_val_bands_coarse``
        - ``number_val_bands_fine``
        - ``number_cond_bands_coarse``
        - ``number_cond_bands_fine``
    """

    def __init__(self, *keywords: str, **variables: Any) -> None:
        all_variables = OrderedDict(
            [
                ("number_val_bands_coarse", 1),
                ("number_val_bands_fine", 1),
                ("number_cond_bands_coarse", 1),
                ("number_cond_bands_fine", 1),
            ]
        )

        all_variables.update(variables)

        super().__init__(all_variables, keywords)


class InteqpTask(BGWTask):
    """Quasiparticle band structure interpolation task.

    This task interpolates quasiparticle (QP) corrections from a coarse
    k-point grid onto a fine k-point grid using BerkeleyGW's inteqp.x
    executable.

    Attributes
    ----------
    input : InteqpInput
        The inteqp input file object.

    Properties
    ----------
    eqp_co_fname : str
        Path to the coarse-grid quasiparticle corrections file (``eqp_co.dat``).
    wfn_co_fname : str
        Path to the coarse-grid wavefunction file (``WFN_co``).
    wfn_fi_fname : str
        Path to the fine-grid wavefunction file (``WFN_fi``).
    """

    _TASK_NAME = "Inteqp task"
    _input_fname = "inteqp.inp"
    _output_fname = "inteqp.log"

    def __init__(self, dirname: str, **kwargs: Any) -> None:
        """Initialize an inteqp task.

        Parameters
        ----------
        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.

        Other Parameters
        ----------------
        eqp_co_fname : str
            Path to the coarse-grid quasiparticle corrections file produced
            by sigma (typically ``eqp1.dat``, to be linked as ``eqp_co.dat``).
        wfn_co_fname : str
            Path to the coarse-grid wavefunction file (linked as ``WFN_co``).
        wfn_fi_fname : str
            Path to the fine-grid wavefunction file (linked as ``WFN_fi``).
        number_val_bands_coarse : int, default=1
            Number of occupied (valence) bands on the coarse k-point grid
            (``WFN_co``).
        number_val_bands_fine : int, default=1
            Number of occupied (valence) bands on the fine k-point grid
            (``WFN_fi``).
        number_cond_bands_coarse : int, default=1
            Number of unoccupied (conduction) bands on the coarse k-point
            grid (``WFN_co``).
        number_cond_bands_fine : int, default=1
            Number of unoccupied (conduction) bands on the fine k-point
            grid (``WFN_fi``).
        extra_lines : list[str], optional
            Any other keyword flags to include in the input file, e.g.
            ``['kpt_interpolation_linear', 'use_symmetries_coarse_grid']``.
        extra_variables : dict[str, Any], optional
            Any other keyword-value pairs to include in the input file, e.g.
            ``{'avgpot': 0.2}``.
        """
        super().__init__(dirname, **kwargs)

        self.eqp_co_fname = kwargs["eqp_co_fname"]
        self.wfn_co_fname = kwargs["wfn_co_fname"]
        self.wfn_fi_fname = kwargs["wfn_fi_fname"]

        self.input = InteqpInput(
            *kwargs.get("extra_lines", []),
            number_val_bands_coarse=kwargs.pop("number_val_bands_coarse", 1),
            number_val_bands_fine=kwargs.pop("number_val_bands_fine", 1),
            number_cond_bands_coarse=kwargs.pop("number_cond_bands_coarse", 1),
            number_cond_bands_fine=kwargs.pop("number_cond_bands_fine", 1),
            **kwargs.get("extra_variables", {}),
        )

        self.input.fname = self._input_fname

        ex = "inteqp.cplx.x" if self._flavor_complex else "inteqp.real.x"
        self.runscript["INTEQP"] = ex
        self.runscript.append(f"$MPIRUN $INTEQP &> {self._output_fname}")

    def write(self) -> None:
        """Write the task files to disk."""
        super().write()
        with self.exec_from_dirname():
            self.input.write()

    @property
    def eqp_co_fname(self) -> str:
        """Get path to the coarse-grid quasiparticle corrections file."""
        return self._eqp_co_fname

    @eqp_co_fname.setter
    def eqp_co_fname(self, value: str) -> None:
        """Set path to the coarse-grid QP corrections file and update symlink."""
        self._eqp_co_fname = value
        self.update_link(value, "eqp_co.dat")

    @property
    def wfn_co_fname(self) -> str:
        """Get path to the coarse-grid wavefunction file."""
        return self._wfn_co_fname

    @wfn_co_fname.setter
    def wfn_co_fname(self, value: str) -> None:
        """Set path to the coarse-grid wavefunction file and update symlink."""
        self._wfn_co_fname = value
        self.update_link(value, "WFN_co")

    @property
    def wfn_fi_fname(self) -> str:
        """Get path to the fine-grid wavefunction file."""
        return self._wfn_fi_fname

    @wfn_fi_fname.setter
    def wfn_fi_fname(self, value: str) -> None:
        """Set path to the fine-grid wavefunction file and update symlink."""
        self._wfn_fi_fname = value
        self.update_link(value, "WFN_fi")
