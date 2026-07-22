"""ParaBands task for building a many-band ``WFN.h5``.

This module provides the ParabandsTask class, which wraps BerkeleyGW's
``parabands.x``. ParaBands re-diagonalizes the fixed DFT Hamiltonian to add many
empty states, avoiding the large ``nbnd`` that makes ``pw.x`` blow up in ``cdiaghg``.
Its inputs (a small binary WFN plus the ``VSC`` and, for norm-conserving
pseudopotentials, ``VKB`` potentials) come from pw2bgw
(:class:`~BGWpy.QE.qebgwtask.Qe2BgwTask`); its output is an HDF5 WFN.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import h5py
import numpy as np

from .bgwtask import BGWTask
from .inputs import ParabandsInput

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

__all__ = ["ParabandsTask", "read_wfn_h5_mnband"]


class ParabandsTask(BGWTask):
    """Run ``parabands.x`` to build a many-band ``WFN.h5`` from a small WFN.

    The ParaBands inputs (``WFN_in``, ``VSC``, ``VKB``) are symlinked into the run
    directory under the fixed names ``parabands.inp`` references, so the caller
    passes real paths (typically the outputs of a ``pw2bgw`` run with ``vscg_flag`` /
    ``vkbg_flag`` set to True, i.e. :class:`~BGWpy.QE.qebgwtask.Qe2BgwTask`).

    Parameters
    ----------
    dirname
        Directory in which the files are written and the code is executed.
    wfn_in_fname
        Path to the binary input WFN (small ``nbnd``) from pw2bgw.
    vsc_fname
        Path to the binary VSC file (self-consistent potential, G-space).
    nbnd
        Number of bands ParaBands should generate (the ``number_bands`` variable of
        ``parabands.inp``). ``-1`` means "as many as the plane-wave basis allows".
    vkb_fname
        Path to the binary VKB file (Kleinman-Bylander projectors). Strongly
        recommended; omitting it drops the non-local potential.
    wfn_out_fname
        Basename of the HDF5 output WFN (default ``"WFN.h5"``); must end in
        ``.h5``.
    solver_algorithm
        ParaBands solver algorithm. ``-1`` (default) lets ParaBands choose
        automatically -- ELPA (10) if it was compiled with ELPA support,
        otherwise ScaLAPACK bisection (0). Set explicitly to force a solver.
    extra_variables, extra_lines
        Extra ``parabands.inp`` variables (e.g. ``number_pools``, ``block_size``,
        the pseudobands block) and bare keyword lines (e.g. ``"use_pseudobands"``),
        matching the ``extra_variables`` / ``extra_lines`` convention of
        :class:`~BGWpy.BGW.epsilontask.EpsilonTask`.

    Properties
    ----------
    wfn_out_fname : str
        Full path to the ``WFN.h5`` file produced.
    """

    _TASK_NAME: str = "Parabands"
    _input_fname: str = "parabands.inp"
    _output_fname: str = "parabands.out"

    input: ParabandsInput
    _wfn_out_basename: str

    def __init__(
        self,
        dirname: str | Path,
        *,
        wfn_in_fname: str | Path,
        vsc_fname: str | Path,
        nbnd: int,
        vkb_fname: str | Path | None = None,
        wfn_out_fname: str = "WFN.h5",
        solver_algorithm: int = -1,
        extra_variables: Mapping[str, Any] | None = None,
        extra_lines: Iterable[str] = (),
        **kwargs: Any,
    ) -> None:
        super().__init__(dirname, **kwargs)

        if not self._use_hdf5:
            warnings.warn(
                "ParaBands writes its output WFN in HDF5 format, but BGWpy is "
                "configured without HDF5 (edit ~/.BGWpyrc). The output cannot be "
                "read by Epsilon/Sigma without HDF5 support.",
                stacklevel=2,
            )
        if not str(wfn_out_fname).endswith(".h5"):
            msg = f"ParaBands output must be HDF5 (a '.h5' name); got {wfn_out_fname!r}"
            raise ValueError(msg)
        self._wfn_out_basename = str(wfn_out_fname)

        variables: dict[str, Any] = {"solver_algorithm": solver_algorithm}
        if extra_variables:
            variables.update(extra_variables)

        self.input = ParabandsInput(
            "WFN_in",
            self._wfn_out_basename,
            *extra_lines,
            vsc_file="VSC",
            vkb_file="VKB" if vkb_fname is not None else None,
            nbnd=nbnd,
            **variables,
        )
        self.input.fname = self._input_fname

        # Symlink the (binary) inputs into the run dir under the names parabands.inp
        # references. ParaBands opens 'parabands.inp' from cwd and reads these by name.
        self.update_link(wfn_in_fname, "WFN_in")
        self.update_link(vsc_fname, "VSC")
        if vkb_fname is not None:
            self.update_link(vkb_fname, "VKB")

        ex = "parabands.cplx.x" if self._flavor_complex else "parabands.real.x"
        self.runscript["PARABANDS"] = ex
        self.runscript.append(f"$MPIRUN $PARABANDS &> {self._output_fname}")

    def write(self) -> None:
        """Write the runscript, input file, and links to disk."""
        super().write()
        with self.exec_from_dirname():
            self.input.write()

    @property
    def wfn_out_fname(self) -> str:
        """Full path to the HDF5 WFN produced by ParaBands."""
        return str(Path(self.dirname) / self._wfn_out_basename)


def read_wfn_h5_mnband(wfn_h5: str | Path) -> int:
    """Total band count (``mnband``) from a BerkeleyGW ``WFN.h5`` header.

    Reads only the band-count field. Useful for pseudobands WFNs, where the degeneracy
    structure is meaningless but ``mnband`` still sizes Epsilon/Sigma's
    ``number_bands`` (see :class:`~BGWpy.BGW.degeneracychecktask.DegeneracyCheckTask`
    for a full degeneracy check).
    """
    with h5py.File(str(wfn_h5), "r") as f:
        return int(np.asarray(f["mf_header/kpoints/mnband"]))
