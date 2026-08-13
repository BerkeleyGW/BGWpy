"""Degeneracy check task for BerkeleyGW.

This module provides the DegeneracyCheckTask class, which reports the
degeneracy-allowed numbers of bands in a wavefunction file. A binary WFN is handled
by wrapping BerkeleyGW's ``degeneracy_check.x`` executable; an HDF5 WFN (``.h5``,
e.g. a ParaBands output) is read in Python, since stock ``degeneracy_check.x`` is
binary-only. Both paths return the same ``DegeneracyCheckResult``.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, TypedDict

import h5py
import numpy as np

from BGWpy.core import Task

__all__ = ["TOL_DEGENERACY_RY", "DegeneracyCheckResult", "DegeneracyCheckTask"]

#: Degeneracy tolerance in Rydberg, matching BerkeleyGW ``Common/nrtype.f90``
#: (``TOL_Degeneracy = 1.0d-6``). ``WFN.h5`` eigenvalues are in Ry, so the
#: comparison against this tolerance is done directly with no unit conversion.
TOL_DEGENERACY_RY = 1.0e-6


# Why two total-count lists: `number_bands` (epsilon's Adler-Wiser sum, sigma's CH sum)
# must not split a degenerate subspace, and BGW dies if it does. Sigma's QP window
# (`band_index_min`/`band_index_max`) is never checked, but Sigma/shiftenergy.f90
# symmetrizes Sigma over the degenerate subspaces it finds among the *requested* bands,
# so a window cutting a multiplet averages over only the part it asked for and the QP
# energy of a band silently depends on whether its partner was requested too. The two
# lists coincide except on a pseudobands WFN, where only the QP one is meaningful.
class _DegeneracyCheckOptional(TypedDict, total=False):
    """The keys of :class:`DegeneracyCheckResult` that are not always present."""

    allowed_bands: list[int]
    n_bands_protected: int


class DegeneracyCheckResult(_DegeneracyCheckOptional):
    """Result of a degeneracy check calculation.

    Attributes
    ----------
    n_spins : int
        Number of spins in the wavefunction.
    n_bands : int
        Number of bands in the wavefunction (``mnband``; for a pseudobands WFN the
        compressed total, not the protection window).
    n_kpoints : int
        Number of k-points in the wavefunction.
    allowed_bands : list[int]
        Degeneracy-allowed band counts for epsilon/sigma ``number_bands``. Absent for a
        pseudobands WFN, which must use every band in the file (``n_bands``).
    allowed_qp_bands : list[int]
        Degeneracy-allowed band counts for sigma's QP window (``band_index_max``).
        Equals ``allowed_bands``, except on a pseudobands WFN, where it stops inside
        the protection window.
    allowed_valence_bands : list[int]
        Degeneracy-allowed numbers of valence bands (for inteqp, kernel, and absorption).
    allowed_conduction_bands : list[int]
        Degeneracy-allowed numbers of conduction bands (for inteqp, kernel, and absorption).
    n_bands_protected : int
        ParaBands' ``nb_fixed``: the highest band with an exact energy, counted from
        band 1. Present only for a pseudobands WFN read with ``allow_pseudobands``.
        Not itself a valid QP window -- use ``allowed_qp_bands``.
    """

    n_spins: int
    n_kpoints: int
    n_bands: int
    allowed_qp_bands: list[int]
    allowed_valence_bands: list[int]
    allowed_conduction_bands: list[int]


def _allowed_band_counts(
    el: np.ndarray, ifmax: np.ndarray, ifmin: np.ndarray, tol_ry: float
) -> tuple[list[int], list[int], list[int]]:
    """Apply the degeneracy rule to a spectrum, per BerkeleyGW ``degeneracy_check.f90``.

    ``el`` is ``(nspin, nrk, mnband)`` in Ry; ``ifmax`` / ``ifmin`` are ``(nspin, nrk)``
    and 1-based. A band count is allowed only where the gap between the two bands it
    separates is *strictly greater* than ``tol_ry`` at every k-point and spin -- the
    ``.gt. TOL_Degeneracy`` test, so a gap exactly equal to the tolerance counts as
    degenerate. Returns ``(allowed_bands, allowed_valence_bands,
    allowed_conduction_bands)``: the totals and conduction counts omit their
    unassessable top entry, the valence counts include the full ``nvband``.
    """
    mnband = el.shape[2]

    # Valence/conduction window sizes:
    #   nvband = min over (k, spin) of (ifmax - ifmin) + 1
    #   ncband = mnband - max over (k, spin) of ifmax
    nvband = int((ifmax - ifmin).min()) + 1
    ncband = mnband - int(ifmax.max())

    # Total: band count ib is allowed iff |el(ib) - el(ib+1)| > tol at all (k, spin).
    # el[..., ib-1] and el[..., ib] are the (1-based) bands ib and ib+1.
    dtotal = np.abs(el[:, :, :-1] - el[:, :, 1:])  # (nspin, nrk, mnband-1)
    ok_total = np.all(dtotal > tol_ry, axis=(0, 1))  # length mnband-1
    allowed_bands = [ib for ib in range(1, mnband) if ok_total[ib - 1]]

    # Valence and conduction: the same test, but taken from the per-(k, spin) Fermi
    # boundary ifmax rather than from band 1, so the band index depends on (k, spin)
    # and the pair is gathered with take_along_axis. ifmax is 1-based, so the el index
    # of the 1-based band b is b - 1.
    ib_v = np.arange(1, nvband)  # valence counts to assess
    top_v = ifmax[:, :, None] - ib_v  # el index of band (ifmax - ib + 1)
    dval = np.abs(np.take_along_axis(el, top_v, axis=2) - np.take_along_axis(el, top_v - 1, axis=2))
    ok_val = np.all(dval > tol_ry, axis=(0, 1))
    allowed_valence_bands = [int(ib) for ib in ib_v[ok_val]]
    allowed_valence_bands.append(nvband)  # using all valence bands is always allowed

    ib_c = np.arange(1, ncband)  # conduction counts to assess
    bot_c = ifmax[:, :, None] + ib_c - 1  # el index of band (ifmax + ib)
    dcond = np.abs(
        np.take_along_axis(el, bot_c, axis=2) - np.take_along_axis(el, bot_c + 1, axis=2)
    )
    ok_cond = np.all(dcond > tol_ry, axis=(0, 1))
    allowed_conduction_bands = [int(ib) for ib in ib_c[ok_cond]]

    return allowed_bands, allowed_valence_bands, allowed_conduction_bands


class DegeneracyCheckTask(Task):
    """Task for running the degeneracy_check.x BerkeleyGW utility.

    This task executes degeneracy_check.x on a given wavefunction file
    and parses the output to determine the allowed numbers of bands
    that respect degeneracy rules.

    Attributes
    ----------
    executable : str
        Path to the degeneracy_check.x executable.

    Properties
    ----------
    out_fname : str
        Absolute path to the output file (degeneracy_check.out).
    wfn_fname : str
        Relative path to the wavefunction file to check.
    """

    _wfn_fname: str
    _tolerance: float
    _allow_pseudobands: bool
    _result: DegeneracyCheckResult | None
    executable: str

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """
        Initialize a DegeneracyCheckTask.

        Parameters
        ----------
        dirname : str | Path, default="./"
            Main directory from which the scripts are executed.
        wfn_fname : str, default="WFN"
            Relative path to the wavefunction file to check for degeneracies. A name
            ending in ``.h5`` selects the HDF5 (in-Python) path; anything else is
            treated as a binary WFN and passed to ``degeneracy_check.x``.
        tolerance : float, default=TOL_DEGENERACY_RY
            Degeneracy tolerance in Rydberg. Only used for the HDF5 path (the binary
            ``degeneracy_check.x`` has its own compiled-in tolerance).
        allow_pseudobands : bool, default=False
            Check the protection window of a stochastic-pseudobands WFN rather than
            refusing it. HDF5 only -- ParaBands never writes a binary WFN.
        **kwargs
            Additional keyword arguments. Can include 'executable' to specify
            a custom path to the degeneracy_check.x executable.
        """
        self._wfn_fname = kwargs.get("wfn_fname", "WFN")
        self._tolerance = kwargs.get("tolerance", TOL_DEGENERACY_RY)
        self._allow_pseudobands = bool(kwargs.get("allow_pseudobands", False))
        self._result = None
        self.executable = kwargs.get("executable", "degeneracy_check.x")
        super().__init__(dirname, **kwargs)

    @property
    def _is_hdf5(self) -> bool:
        """Whether the wavefunction file is HDF5 (handled in Python, not by the binary)."""
        return str(self._wfn_fname).endswith(".h5")

    def write(self) -> None:
        """Write the task files to disk.

        Raises
        ------
        NotImplementedError
            Always raised, as this task does not write any files.
        """
        msg = "DegeneracyCheckTask does not write any files to disk."
        raise NotImplementedError(msg)

    def run(self) -> None:
        """Run the degeneracy check.

        Executes degeneracy_check.x on the specified wavefunction file
        and writes the output to degeneracy_check.out in the task directory.

        For an HDF5 WFN (``.h5``) the eigenvalue spectrum is read directly and the
        result is cached in-memory (no external process, no ``degeneracy_check.out``);
        :meth:`parse_output` then returns that cached result.

        Raises
        ------
        FileNotFoundError
            If the specified wavefunction file does not exist.
        OSError
            If the executable cannot be found or execution fails.
        """
        wfn_path = Path(self.dirname) / self.wfn_fname
        if not wfn_path.exists():
            msg = f"Wavefunction file not found: {wfn_path}"
            raise FileNotFoundError(msg)

        if self._is_hdf5:
            self._result = self._parse_wfn_h5(wfn_path)
            return

        try:
            print(f"Running {self.executable} ...")
            with self.exec_from_dirname():
                result = subprocess.run(
                    [self.executable, self.wfn_fname], capture_output=True, check=True
                )
        except OSError as err:
            msg = f"""
            {err!s}

            {self.executable} executable not found.

            Please ensure that either the 'bin' directory of your BerkeleyGW installation is in your PATH environment variable, or that you have loaded the appropriate module on your computing cluster (e.g., 'module load berkeleygw').
            """

            raise OSError(msg) from err

        Path(self.out_fname).write_text(result.stdout.decode())

    def parse_output(self) -> DegeneracyCheckResult:
        """Parse the output of the degeneracy check.

        For an HDF5 WFN this returns the result computed in :meth:`run` (recomputing
        it directly from the file if :meth:`run` has not been called). For a binary
        WFN it parses the ``degeneracy_check.out`` written by the executable.

        Returns
        -------
        DegeneracyCheckResult
            A dictionary containing the number of spins, bands, k-points,
            and the degeneracy-allowed numbers of bands for various calculations.
        """
        if self._is_hdf5:
            if self._result is None:
                self._result = self._parse_wfn_h5(Path(self.dirname) / self.wfn_fname)
            return self._result

        return self._parse_output_text()

    def _parse_output_text(self) -> DegeneracyCheckResult:
        """Parse a binary-WFN ``degeneracy_check.out`` written by the executable."""
        output_text = Path(self.out_fname).read_text()

        result: DegeneracyCheckResult = {
            "n_spins": 0,
            "n_bands": 0,
            "n_kpoints": 0,
            "allowed_bands": [],
            "allowed_qp_bands": [],
            "allowed_valence_bands": [],
            "allowed_conduction_bands": [],
        }

        error_msg = "Unexpected output format in degeneracy_check.out. Unable to parse results."

        spins_match = re.search(r"Number of spins:\s+(\d+)", output_text)
        if spins_match:
            result["n_spins"] = int(spins_match.group(1))
        else:
            raise ValueError(error_msg)

        bands_match = re.search(r"Number of bands:\s+(\d+)", output_text)
        if bands_match:
            result["n_bands"] = int(bands_match.group(1))
        else:
            raise ValueError(error_msg)

        kpoints_match = re.search(r"Number of k-points:\s+(\d+)", output_text)
        if kpoints_match:
            result["n_kpoints"] = int(kpoints_match.group(1))
        else:
            raise ValueError(error_msg)

        current_section = None
        for raw_line in output_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("== Degeneracy-allowed numbers of bands"):
                current_section = "allowed_bands"
            elif line.startswith("== Degeneracy-allowed numbers of valence bands"):
                current_section = "allowed_valence_bands"
            elif line.startswith("== Degeneracy-allowed numbers of conduction bands"):
                current_section = "allowed_conduction_bands"
            elif (current_section is not None) and line.isdigit():
                result[current_section].append(int(line))

        # A binary WFN is never a pseudobands WFN (ParaBands only writes HDF5), so the
        # summation and QP-window counts are the same list.
        result["allowed_qp_bands"] = list(result["allowed_bands"])
        return result

    def _parse_wfn_h5(self, wfn_h5: str | Path) -> DegeneracyCheckResult:
        """Compute the degeneracy-allowed band counts directly from a ``WFN.h5``.

        The in-Python equivalent of ``degeneracy_check.x`` for HDF5 WFN files; the rule
        itself is :func:`_allowed_band_counts`. A stochastic-pseudobands WFN is refused
        unless the task was built with ``allow_pseudobands``, in which case only its
        protection window is checked.

        Raises
        ------
        ValueError
            If the file is a stochastic-pseudobands WFN and ``allow_pseudobands`` is
            unset, or if its recorded protection window is missing or inconsistent
            with the header.
        """
        tol_ry = self._tolerance
        with h5py.File(str(wfn_h5), "r") as f:
            n_bands_protected = self._n_bands_protected(f, wfn_h5)
            kp = f["mf_header/kpoints"]
            el = np.asarray(kp["el"], dtype=float)  # (nspin, nrk, mnband), Ry
            ifmax = np.asarray(kp["ifmax"], dtype=np.int64)  # (nspin, nrk), 1-based
            ifmin = np.asarray(kp["ifmin"], dtype=np.int64)  # (nspin, nrk), 1-based
            nspin = int(np.asarray(kp["nspin"]))
            nrk = int(np.asarray(kp["nrk"]))
            mnband = int(np.asarray(kp["mnband"]))

        if n_bands_protected is None:
            allowed_bands, allowed_valence, allowed_conduction = _allowed_band_counts(
                el, ifmax, ifmin, tol_ry
            )
            return DegeneracyCheckResult(
                n_spins=nspin,
                n_bands=mnband,
                n_kpoints=nrk,
                allowed_bands=allowed_bands,
                allowed_qp_bands=list(allowed_bands),
                allowed_valence_bands=allowed_valence,
                allowed_conduction_bands=allowed_conduction,
            )

        # An out-of-range window would silently drag the check back over the stochastic
        # bands -- the very thing the pseudobands guard exists to prevent.
        n_valence_max = int(ifmax.max())
        if not n_valence_max <= n_bands_protected <= mnband:
            msg = (
                f"{wfn_h5} records a pseudobands protection window of "
                f"{n_bands_protected} bands, outside the {n_valence_max}..{mnband} "
                f"its own header allows."
            )
            raise ValueError(msg)

        # Only bands 1..n_bands_protected keep their exact energies, so the counts stop
        # one short of the window: band n_bands_protected pairs with a stochastic band
        # and cannot be assessed. Withheld here: `allowed_bands`, since epsilon and
        # sigma must take every band of a compressed file.
        allowed_qp, allowed_valence, allowed_conduction = _allowed_band_counts(
            el[:, :, :n_bands_protected], ifmax, ifmin, tol_ry
        )
        return DegeneracyCheckResult(
            n_spins=nspin,
            n_bands=mnband,
            n_kpoints=nrk,
            allowed_qp_bands=allowed_qp,
            allowed_valence_bands=allowed_valence,
            allowed_conduction_bands=allowed_conduction,
            n_bands_protected=n_bands_protected,
        )

    def _n_bands_protected(self, f: h5py.File, wfn_h5: str | Path) -> int | None:
        """Protection-window size, or None if this is not a pseudobands WFN.

        ParaBands records its pseudobands settings under ``/parabands/pseudobands``
        (the group exists but is empty when pseudobands is off); the window size is
        its ``nb_fixed``, counted from band 1. Above it the eigenvalues are stochastic
        combinations, not band energies, so a degeneracy check there would return
        plausible-looking nonsense -- hence the refusal unless the caller opted in.
        """
        is_on = f.get("parabands/pseudobands/is_on")
        if is_on is None or not bool(np.asarray(is_on)):
            return None

        n_protected = f.get("parabands/pseudobands/nb_fixed")
        if not self._allow_pseudobands:
            window = (
                ""
                if n_protected is None
                else f" (only the first {int(np.asarray(n_protected))} are)"
            )
            msg = (
                f"{wfn_h5} is a stochastic-pseudobands WFN: its eigenvalues above the "
                f"protection window are not physical band energies{window}, so the "
                f"degeneracy-allowed band counts would be meaningless. Run the degeneracy "
                f"check on the WFN before pseudobands compression; to size Epsilon/Sigma "
                f"from a pseudobands WFN use BGWpy.BGW.parabandstask.read_wfn_h5_mnband, "
                f"and to pick QP band counts inside the protection window pass "
                f"allow_pseudobands=True."
            )
            raise ValueError(msg)

        if n_protected is None:
            msg = (
                f"{wfn_h5} is a stochastic-pseudobands WFN with no recorded "
                f"parabands/pseudobands/nb_fixed, so the extent of its exact protection "
                f"window is unknown and the check cannot be restricted to it."
            )
            raise ValueError(msg)
        return int(np.asarray(n_protected))

    @property
    def out_fname(self) -> str:
        """Get the absolute path to the output file."""
        return str(Path(self.dirname) / "degeneracy_check.out")

    @property
    def wfn_fname(self) -> str:
        """Get the relative path to the wavefunction file."""
        return self._wfn_fname
