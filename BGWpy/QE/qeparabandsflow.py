"""QE + ParaBands mean-field flow for one k-grid.

This module provides the QeParabandsFlow class, which produces the same BerkeleyGW
mean-field outputs as :class:`~BGWpy.QE.qebgwflow.QeBgwFlow` (``wfn_fname`` /
``rho_fname`` / ``vxc_fname`` / ``vxc_dat_fname``) but builds the many-band
``WFN.h5`` with ParaBands: a cheap QE nscf fixes the occupations, pw2bgw writes the
binary ``WFN_in`` plus the ``VSC`` / ``VKB`` potentials, and ``parabands.x``
re-diagonalizes to the large band count. A full GW mean-field set is three such flows
(shifted WFN, unshifted WFN_co, q-shifted WFNq).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from BGWpy.BGW.parabandstask import ParabandsTask
from BGWpy.DFT import WfnBgwFlow
from BGWpy.QE.qebgwtask import Qe2BgwTask
from BGWpy.QE.wfntask import QeWfnTask

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from pymatgen.core import Structure

__all__ = ["QeParabandsFlow"]


class QeParabandsFlow(WfnBgwFlow):
    """A ``WfnBgwFlow`` building a many-band WFN for one k-grid via ParaBands.

    Runs three sub-tasks, mirroring :class:`~BGWpy.QE.qebgwflow.QeBgwFlow`:

    1. :class:`~BGWpy.QE.wfntask.QeWfnTask` -- a cheap QE nscf (``seed_nbnd`` bands)
       to fix the occupations.
    2. :class:`~BGWpy.QE.qebgwtask.Qe2BgwTask` -- pw2bgw producing the binary
       ``WFN_in`` plus ``VSC`` and ``VKB`` (``vscg_flag`` / ``vkbg_flag``), and
       optionally the density + ``vxc.dat`` (``rhog_flag``).
    3. :class:`~BGWpy.BGW.parabandstask.ParabandsTask` -- ``parabands.x``
       re-diagonalizing the fixed DFT Hamiltonian to ``nbnd`` bands, writing
       ``WFN.h5``.

    Like ``QeBgwFlow`` it is parallelization-agnostic: pass ``pwflags`` and the
    per-task MPI-settings dicts. The three stages take separate MPI settings because
    they want different resources (the seed nscf pools over k-points, pw2bgw is
    rank-capped, ParaBands scales to all ranks). Drive it like any Task/Workflow
    (``write`` / ``run`` / ``get_status``); it is ``COMPLETED`` only when all three
    sub-tasks are.

    Parameters
    ----------
    dirname
        Directory for the seed nscf and pw2bgw; ParaBands runs in
        ``<dirname>/parabands``.
    structure, prefix, pseudo_dir, pseudos
        Standard QE settings.
    charge_density_fname, data_file_fname, ekin_density_fname, spin_polarization_fname
        SCF outputs seeding the nscf (``ekin_density_fname`` only for meta-GGA,
        ``spin_polarization_fname`` only for a spin-polarized calculation).
    ecutwfc
        Plane-wave cutoff (Ry).
    ngkpt, kshift, qshift
        The k-grid, its shift, and any q-shift for this grid.
    symkpt
        If True (default), reduce the seed k-grid by symmetry (propagated to the seed
        nscf and pw2bgw). Set False to keep the full unreduced BZ, as needed for a
        downstream GW run with ``no_symmetries``.
    seed_nbnd
        Bands for the QE seed nscf (n_occ + a small buffer).
    nbnd
        Bands ParaBands generates (the large target).
    variables
        Extra QE namelist variables for the seed nscf -- the hook for all ``pw.x``
        tuning, e.g. ``{"electrons": {"diagonalization": "cg"}}``. pw2bgw takes no
        such variables; its input is fully determined by the flags below.
    pwflags
        Parallel flags for the seed ``pw.x`` (e.g. ``-nk`` pools); not passed to
        pw2bgw, which does not pool over k-points.
    wfn_mpi_settings, pw2bgw_mpi_settings, parabands_mpi_settings
        MPI settings for the seed nscf, pw2bgw, and ParaBands respectively.
    rhog_flag
        If True, pw2bgw also writes the density (``RHO``) and the XC potential Sigma
        needs. ``vscg_flag`` / ``vkbg_flag`` are always on (ParaBands requires VSC/VKB)
        and not exposed; ``rhog_flag`` is the only pw2bgw toggle.
    use_vxcg
        Only with ``rhog_flag``. If True (default), pw2bgw writes the G-space XC
        potential ``VXC`` (exposed as ``vxc_fname``) and Sigma reconstructs
        ``<nk|Vxc|nk>`` from it, decoupling Sigma's QP band range from the seed nscf.
        If False, it writes the legacy ``vxc.dat`` (exposed as ``vxc_dat_fname``).
    wfn_out_fname
        Basename of the ParaBands HDF5 output (default ``"WFN.h5"``).
    solver_algorithm
        ParaBands solver algorithm; ``-1`` (default) auto-selects ELPA (10) where
        compiled, otherwise ScaLAPACK bisection (0). Set explicitly to force one.
    use_pseudobands
        If True, ParaBands compresses conduction states above the protection window
        into stochastic pseudobands, so Epsilon/Sigma converge the band sum with far
        fewer bands. Requires ``nbnd_cond_prot``; Sigma auto-detects the
        pseudobands WFN.
    nbnd_cond_prot
        Conduction bands kept exact -- the ``protected_cond_bands`` variable of
        ``parabands.inp`` (required with ``use_pseudobands``); make it large enough to
        contain every band Sigma/BSE corrects.
    pseudobands_accumulation_window, pseudobands_num_bands_per_slice
        ParaBands ``accumulation_window`` / ``num_bands_per_slice``; None uses
        ParaBands' defaults.
    parabands_extra_variables, parabands_extra_lines
        Passed through to :class:`~BGWpy.BGW.parabandstask.ParabandsTask` (merged with
        the pseudobands keywords when ``use_pseudobands`` is set).

    Notes
    -----
    Options are explicit arguments (no ``**kwargs`` passthrough): QE-side tuning goes
    through ``variables``, and ParaBands-stage config through the ``parabands_*`` /
    ``solver_algorithm`` / ``wfn_out_fname`` arguments.

    Properties
    ----------
    wfn_fname : str
        The ParaBands ``WFN.h5`` (for Epsilon/Sigma). Always produced.
    rho_fname : str
        The pw2bgw density. Requires ``rhog_flag``.
    vxc_fname : str
        The pw2bgw G-space ``VXC`` potential (the default XC source for Sigma).
        Requires ``rhog_flag`` and ``use_vxcg``.
    vxc_dat_fname : str
        The pw2bgw ``vxc.dat`` matrix elements (the legacy XC path). Requires
        ``rhog_flag`` and ``use_vxcg=False``.
    rhog_flag, use_vxcg : bool
        Read-only echoes of the constructor flags, to branch on without catching.

    The density/XC properties raise ``ValueError`` when this flow was not built to produce
    the file they name -- deliberately stricter than ``Qe2BgwTask`` / ``AbinitBgwFlow``,
    which return the path regardless.
    """

    def __init__(
        self,
        *,
        dirname: str | Path,
        structure: Structure,
        prefix: str,
        pseudo_dir: str | Path,
        pseudos: list[str],
        charge_density_fname: str | Path,
        data_file_fname: str | Path,
        ecutwfc: float,
        ngkpt: list[int],
        seed_nbnd: int,
        nbnd: int,
        kshift: list[float] | None = None,
        qshift: list[float] | None = None,
        symkpt: bool = True,
        ekin_density_fname: str | Path = "",
        spin_polarization_fname: str | Path = "",
        variables: Mapping[str, Any] | None = None,
        pwflags: str = "",
        wfn_mpi_settings: Mapping[str, Any] | None = None,
        pw2bgw_mpi_settings: Mapping[str, Any] | None = None,
        parabands_mpi_settings: Mapping[str, Any] | None = None,
        rhog_flag: bool = False,
        use_vxcg: bool = True,
        wfn_out_fname: str = "WFN.h5",
        solver_algorithm: int = -1,
        use_pseudobands: bool = False,
        nbnd_cond_prot: int | None = None,
        pseudobands_accumulation_window: float | None = None,
        pseudobands_num_bands_per_slice: int | None = None,
        parabands_extra_variables: Mapping[str, Any] | None = None,
        parabands_extra_lines: Iterable[str] = (),
    ) -> None:
        qe_settings = {
            "prefix": prefix,
            "pseudo_dir": str(pseudo_dir),
            "pseudos": pseudos,
        }
        grid = {
            "ngkpt": ngkpt,
            "kshift": list(kshift) if kshift is not None else [0.0, 0.0, 0.0],
            "qshift": list(qshift) if qshift is not None else [0.0, 0.0, 0.0],
        }
        variables = dict(variables) if variables else {}

        # WfnBgwFlow (DFTFlow) wants the DFT-level settings it and QeBgwFlow expect
        # (structure, pseudos, grid), but no MPI settings -- this flow stays
        # parallelization-agnostic; the three sub-tasks own their MPI dicts. prefix
        # goes only to the sub-tasks (DFTTask does not take it).
        super().__init__(
            dirname=dirname,
            structure=structure,
            pseudo_dir=str(pseudo_dir),
            pseudos=pseudos,
            **grid,
        )

        # Backs the read-only flag properties and the fname guards below: G-space VXC
        # with use_vxcg, vxc.dat without, neither when rhog_flag is False.
        self._rhog_flag = rhog_flag
        self._use_vxcg = use_vxcg

        # 1. QE seed nscf (a few bands above n_occ, to fix the occupations).
        self.wfntask = QeWfnTask(
            dirname=self.dirname,
            structure=structure,
            variables=variables,
            charge_density_fname=str(charge_density_fname),
            data_file_fname=str(data_file_fname),
            ekin_density_fname=str(ekin_density_fname),
            spin_polarization_fname=str(spin_polarization_fname),
            ecutwfc=ecutwfc,
            nbnd=seed_nbnd,
            symkpt=symkpt,
            PWFLAGS=pwflags,
            **qe_settings,
            **grid,
            **(dict(wfn_mpi_settings) if wfn_mpi_settings else {}),
        )
        self.wfntask.runscript.fname = "wfn.run.sh"
        self.add_task(self.wfntask, merge=False)

        # 2. pw2bgw: binary WFN_in + VSC + VKB (+ rho/vxc if rhog_flag).
        # (No PWFLAGS - pw2bgw.x does not pool over k-points)
        # With use_vxcg, write the G-space XC potential (VXC) instead of the vxc.dat
        # matrix elements: Sigma builds <nk|Vxc|nk> from VXC + the ParaBands wfns
        # (dont_use_vxcdat), so the QP band range is no longer capped by the seed.
        vxcg_kwargs: dict[str, Any] = {}
        if rhog_flag and use_vxcg:
            vxcg_kwargs = {"vxc_flag": False, "vxcg_flag": True, "vxc_fname": "VXC"}
        self.pw2bgwtask = Qe2BgwTask(
            dirname=self.wfntask.dirname,
            structure=structure,
            variables=variables,
            nbnd=seed_nbnd,  # vxc_diag_nmax
            symkpt=symkpt,
            rhog_flag=rhog_flag,
            vscg_flag=True,
            vkbg_flag=True,
            **vxcg_kwargs,
            **qe_settings,
            **grid,
            **(dict(pw2bgw_mpi_settings) if pw2bgw_mpi_settings else {}),
        )
        self.pw2bgwtask.runscript.fname = "pw2bgw.run.sh"
        self.add_task(self.pw2bgwtask, merge=False)

        # Stochastic pseudobands: compress the conduction states above the protection
        # window into stochastic vectors, so Epsilon/Sigma converge the band sum with
        # far fewer effective bands. nbnd_cond_prot (the deterministic window) is
        # not a convergence parameter -- it just has to contain every band Sigma/BSE
        # correct -- so we require it explicitly rather than fall back to ParaBands'
        # default of 10. accumulation_window / num_bands_per_slice keep ParaBands'
        # well-tested defaults unless overridden.
        pb_lines = list(parabands_extra_lines)
        pb_variables = dict(parabands_extra_variables or {})
        if use_pseudobands:
            if nbnd_cond_prot is None:
                msg = (
                    "use_pseudobands=True requires nbnd_cond_prot (the deterministic "
                    "protection window; make it >= the number of conduction bands "
                    "Sigma/BSE correct)."
                )
                raise ValueError(msg)
            if "use_pseudobands" not in pb_lines:
                pb_lines.append("use_pseudobands")
            pb_variables.setdefault("protected_cond_bands", nbnd_cond_prot)
            if pseudobands_accumulation_window is not None:
                pb_variables.setdefault("accumulation_window", pseudobands_accumulation_window)
            if pseudobands_num_bands_per_slice is not None:
                pb_variables.setdefault("num_bands_per_slice", pseudobands_num_bands_per_slice)

        # 3. ParaBands -> WFN.h5 (re-diagonalize to the large nbnd).
        self.parabandstask = ParabandsTask(
            dirname=Path(self.dirname) / "parabands",
            wfn_in_fname=self.pw2bgwtask.wfn_fname,
            vsc_fname=self.pw2bgwtask.vsc_fname,
            vkb_fname=self.pw2bgwtask.vkb_fname,
            nbnd=nbnd,
            wfn_out_fname=wfn_out_fname,
            solver_algorithm=solver_algorithm,
            extra_variables=pb_variables,
            extra_lines=pb_lines,
            **(dict(parabands_mpi_settings) if parabands_mpi_settings else {}),
        )
        self.add_task(self.parabandstask, merge=False)

    @property
    def wfn_fname(self) -> str:
        """The ParaBands ``WFN.h5`` produced (for Epsilon/Sigma)."""
        return self.parabandstask.wfn_out_fname

    # Read-only: pw2bgw's input was written at construction, so a setter would let the
    # guards below pass for files the run never produces.
    @property
    def rhog_flag(self) -> bool:
        """Whether pw2bgw was asked for the density and an XC potential."""
        return self._rhog_flag

    @property
    def use_vxcg(self) -> bool:
        """Whether the XC potential is the G-space ``VXC`` rather than ``vxc.dat``."""
        return self._use_vxcg

    @property
    def _flag_state(self) -> str:
        """This flow's flag combination, for the guard messages below."""
        return f"rhog_flag={self._rhog_flag}, use_vxcg={self._use_vxcg}"

    @property
    def rho_fname(self) -> str:
        """The pw2bgw density file. Requires ``rhog_flag``, else ``ValueError``."""
        if not self._rhog_flag:
            msg = (
                f"rho_fname: pw2bgw only writes the density with rhog_flag=True, but this "
                f"flow has {self._flag_state}. Rebuild it with rhog_flag=True (the GW "
                f"mean-field set needs the density from the unshifted WFN_co grid only)."
            )
            raise ValueError(msg)
        return self.pw2bgwtask.rho_fname

    @property
    def vxc_fname(self) -> str:
        """The G-space ``VXC`` potential, Sigma's default XC source.

        Requires ``rhog_flag`` and ``use_vxcg``, else ``ValueError``.
        """
        if not self._rhog_flag:
            msg = (
                f"vxc_fname: pw2bgw only writes an XC potential with rhog_flag=True, but "
                f"this flow has {self._flag_state}. Rebuild it with rhog_flag=True."
            )
            raise ValueError(msg)
        if not self._use_vxcg:
            msg = (
                f"vxc_fname: this flow ({self._flag_state}) writes the vxc.dat matrix "
                f"elements, not the G-space VXC. Read vxc_dat_fname instead, or rebuild "
                f"with use_vxcg=True."
            )
            raise ValueError(msg)
        return self.pw2bgwtask.vxc_fname

    @property
    def vxc_dat_fname(self) -> str:
        """The ``vxc.dat`` matrix elements, the legacy XC path.

        Requires ``rhog_flag`` and ``use_vxcg=False``, else ``ValueError``.
        """
        if not self._rhog_flag:
            msg = (
                f"vxc_dat_fname: pw2bgw only writes an XC potential with rhog_flag=True, "
                f"but this flow has {self._flag_state}. Rebuild it with rhog_flag=True."
            )
            raise ValueError(msg)
        if self._use_vxcg:
            msg = (
                f"vxc_dat_fname: this flow ({self._flag_state}) writes the G-space VXC, "
                f"not the vxc.dat matrix elements. Read vxc_fname instead (preferred: it "
                f"does not cap Sigma's QP band range), or rebuild with use_vxcg=False."
            )
            raise ValueError(msg)
        return self.pw2bgwtask.vxc_dat_fname
