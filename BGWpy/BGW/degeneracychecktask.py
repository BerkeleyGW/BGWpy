"""Degeneracy check task for BerkeleyGW.

This module provides the DegeneracyCheckTask class, which reports the
degeneracy-allowed numbers of bands in a wavefunction file. A binary WFN is handled
by wrapping BerkeleyGW's ``degeneracy_check.x`` executable; an HDF5 WFN (``.h5``,
e.g. a ParaBands output) is read in Python, since ``degeneracy_check.x`` cannot read
HDF5. Both paths return the same ``DegeneracyCheckResult``.
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


class DegeneracyCheckResult(TypedDict):
    """Result of a degeneracy check calculation.

    Attributes
    ----------
    n_spins : int
        Number of spins in the wavefunction.
    n_bands : int
        Number of bands in the wavefunction.
    n_kpoints : int
        Number of k-points in the wavefunction.
    allowed_bands : list[int]
        Degeneracy-allowed numbers of bands (for epsilon and sigma).
    allowed_valence_bands : list[int]
        Degeneracy-allowed numbers of valence bands (for inteqp, kernel, and absorption).
    allowed_conduction_bands : list[int]
        Degeneracy-allowed numbers of conduction bands (for inteqp, kernel, and absorption).
    """

    n_spins: int
    n_bands: int
    n_kpoints: int
    allowed_bands: list[int]
    allowed_valence_bands: list[int]
    allowed_conduction_bands: list[int]


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
        **kwargs
            Additional keyword arguments. Can include 'executable' to specify
            a custom path to the degeneracy_check.x executable.
        """
        self._wfn_fname = kwargs.get("wfn_fname", "WFN")
        self._tolerance = kwargs.get("tolerance", TOL_DEGENERACY_RY)
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

        return result

    def _parse_wfn_h5(self, wfn_h5: str | Path) -> DegeneracyCheckResult:
        """Compute the degeneracy-allowed band counts directly from a ``WFN.h5``.

        The in-Python equivalent of ``degeneracy_check.x`` for HDF5 WFN files. A band
        count is allowed only where the gap between the two bands it separates is
        *strictly greater* than the tolerance at every k-point and spin -- the
        ``.gt. TOL_Degeneracy`` test of ``degeneracy_check.f90``, so a gap exactly
        equal to the tolerance counts as degenerate. Valence/conduction counts are
        taken relative to the per-(k, spin) Fermi boundary ``ifmax``;
        ``allowed_valence_bands`` includes the full valence count, while
        ``allowed_bands`` and ``allowed_conduction_bands`` omit their (unassessable)
        top entry.

        Raises
        ------
        ValueError
            If the file is a stochastic-pseudobands WFN, whose eigenvalues above the
            protection window are not physical band energies.
        """
        tol_ry = self._tolerance
        with h5py.File(str(wfn_h5), "r") as f:
            self._reject_pseudobands(f, wfn_h5)
            kp = f["mf_header/kpoints"]
            el = np.asarray(kp["el"], dtype=float)  # (nspin, nrk, mnband), Ry
            ifmax = np.asarray(kp["ifmax"], dtype=np.int64)  # (nspin, nrk), 1-based
            ifmin = np.asarray(kp["ifmin"], dtype=np.int64)  # (nspin, nrk), 1-based
            nspin = int(np.asarray(kp["nspin"]))
            nrk = int(np.asarray(kp["nrk"]))
            mnband = int(np.asarray(kp["mnband"]))

        # Valence/conduction window sizes, per BerkeleyGW degeneracy_check.f90:
        #   nvband = min over (k, spin) of (ifmax - ifmin) + 1
        #   ncband = mnband - max over (k, spin) of ifmax
        nvband = int((ifmax - ifmin).min()) + 1
        ncband = mnband - int(ifmax.max())

        # Total: band count ib is allowed iff |el(ib) - el(ib+1)| > tol at all (k, spin).
        # el[..., ib-1] and el[..., ib] are the (1-based) bands ib and ib+1.
        dtotal = np.abs(el[:, :, :-1] - el[:, :, 1:])  # (nspin, nrk, mnband-1)
        ok_total = np.all(dtotal > tol_ry, axis=(0, 1))  # length mnband-1
        allowed_bands = [ib for ib in range(1, mnband) if ok_total[ib - 1]]

        # Valence and conduction: the same test, but taken from the per-(k, spin)
        # Fermi boundary ifmax rather than from band 1, so the band index depends on
        # (k, spin) and the pair is gathered with take_along_axis. ifmax is 1-based,
        # so the el index of the 1-based band b is b - 1.
        ib_v = np.arange(1, nvband)  # valence counts to assess
        top_v = ifmax[:, :, None] - ib_v  # el index of band (ifmax - ib + 1)
        dval = np.abs(
            np.take_along_axis(el, top_v, axis=2) - np.take_along_axis(el, top_v - 1, axis=2)
        )
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

        return DegeneracyCheckResult(
            n_spins=nspin,
            n_bands=mnband,
            n_kpoints=nrk,
            allowed_bands=allowed_bands,
            allowed_valence_bands=allowed_valence_bands,
            allowed_conduction_bands=allowed_conduction_bands,
        )

    @staticmethod
    def _reject_pseudobands(f: h5py.File, wfn_h5: str | Path) -> None:
        """Refuse a stochastic-pseudobands WFN, whose spectrum is not physical.

        ParaBands records its pseudobands settings under ``/parabands/pseudobands``
        (the group exists but is empty when pseudobands is off). Above the protection
        window ``nb_fixed`` the eigenvalues are stochastic combinations rather than
        band energies, so a degeneracy check on them returns plausible-looking but
        meaningless band counts.
        """
        is_on = f.get("parabands/pseudobands/is_on")
        if is_on is None or not bool(np.asarray(is_on)):
            return

        nb_fixed = f.get("parabands/pseudobands/nb_fixed")
        window = "" if nb_fixed is None else f" (only the first {int(np.asarray(nb_fixed))} are)"
        msg = (
            f"{wfn_h5} is a stochastic-pseudobands WFN: its eigenvalues above the "
            f"protection window are not physical band energies{window}, so the "
            f"degeneracy-allowed band counts would be meaningless. Run the degeneracy "
            f"check on the WFN before pseudobands compression; to size Epsilon/Sigma "
            f"from a pseudobands WFN use BGWpy.BGW.parabandstask.read_wfn_h5_mnband."
        )
        raise ValueError(msg)

    @property
    def out_fname(self) -> str:
        """Get the absolute path to the output file."""
        return str(Path(self.dirname) / "degeneracy_check.out")

    @property
    def wfn_fname(self) -> str:
        """Get the relative path to the wavefunction file."""
        return self._wfn_fname
