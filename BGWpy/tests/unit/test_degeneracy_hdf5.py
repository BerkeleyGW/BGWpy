"""Unit tests for the HDF5 path of DegeneracyCheckTask (and read_wfn_h5_mnband).

These exercise pure Python/numpy logic against small synthetic ``WFN.h5`` files -- no
BerkeleyGW executables. ``degeneracy_check.x`` cannot read HDF5, so
:class:`~BGWpy.BGW.degeneracychecktask.DegeneracyCheckTask` reads the eigenvalue
spectrum directly and reproduces the utility's rule: a band count ``n`` is allowed
only if bands ``n`` and ``n+1`` are non-degenerate at *every* k-point and spin.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

h5py = pytest.importorskip("h5py")

from BGWpy.BGW.degeneracychecktask import DegeneracyCheckTask  # noqa: E402
from BGWpy.BGW.parabandstask import read_wfn_h5_mnband  # noqa: E402


def write_wfn_h5(
    path: str | Path,
    el: list | np.ndarray,
    ifmax: list | np.ndarray,
    ifmin: list | np.ndarray,
) -> Path:
    """Write a minimal BerkeleyGW ``WFN.h5`` header with the given spectrum.

    ``el`` has shape ``(nspin, nrk, mnband)`` in Ry; ``ifmax`` / ``ifmin`` have shape
    ``(nspin, nrk)`` and are the 1-based highest-occupied / lowest-occupied band
    indices. Only the ``mf_header/kpoints`` fields the reader touches are written.
    """
    el = np.asarray(el, dtype=float)
    nspin, nrk, mnband = el.shape
    path = Path(path)
    with h5py.File(path, "w") as f:
        kp = f.create_group("mf_header/kpoints")
        kp["el"] = el
        kp["ifmax"] = np.asarray(ifmax, dtype=np.int64).reshape(nspin, nrk)
        kp["ifmin"] = np.asarray(ifmin, dtype=np.int64).reshape(nspin, nrk)
        kp["nspin"] = np.int64(nspin)
        kp["nrk"] = np.int64(nrk)
        kp["mnband"] = np.int64(mnband)
    return path


def degeneracy(tmp_path: Path, el, ifmax, ifmin, **kwargs) -> dict:
    """Write a WFN.h5 under tmp_path and return the parsed DegeneracyCheckResult."""
    write_wfn_h5(tmp_path / "WFN.h5", el, ifmax, ifmin)
    task = DegeneracyCheckTask(dirname=str(tmp_path), wfn_fname="WFN.h5", **kwargs)
    task.run()
    return dict(task.parse_output())


@pytest.mark.unit
class TestDegeneracyHDF5:
    """The HDF5 degeneracy reader on synthetic spectra with known answers."""

    def test_all_nondegenerate(self, tmp_path):
        """No degeneracies: every truncation point is allowed.

        ``allowed_bands`` is 1..mnband-1 (the top band is never assessable),
        ``allowed_valence_bands`` counts down and always includes the full nvband,
        ``allowed_conduction_bands`` counts up and omits its untestable top.
        """
        # 6 bands, 3 valence (ifmin=1, ifmax=3); all gaps 0.1 Ry >> tolerance.
        el = [[[0.0, 0.1, 0.2, 0.3, 0.4, 0.5]]]
        res = degeneracy(tmp_path, el, ifmax=[[3]], ifmin=[[1]])
        assert res["n_spins"] == 1
        assert res["n_bands"] == 6
        assert res["n_kpoints"] == 1
        assert res["allowed_bands"] == [1, 2, 3, 4, 5]
        assert res["allowed_valence_bands"] == [1, 2, 3]
        assert res["allowed_conduction_bands"] == [1, 2]

    def test_conduction_degeneracy_excludes_split_point(self, tmp_path):
        """A degenerate conduction pair removes only the count that splits it.

        Bands 4 and 5 share an energy: truncating at 4 (allowed_bands) or after 1
        conduction band splits the doublet, so those counts drop -- but the clean
        counts on either side remain, i.e. the allowed lists are non-contiguous.
        """
        el = [[[0.0, 0.1, 0.2, 0.3, 0.3, 0.5]]]
        res = degeneracy(tmp_path, el, ifmax=[[3]], ifmin=[[1]])
        assert res["allowed_bands"] == [1, 2, 3, 5]  # 4 dropped, 5 kept
        assert res["allowed_valence_bands"] == [1, 2, 3]  # valence untouched
        assert res["allowed_conduction_bands"] == [2]  # 1 dropped, 2 kept

    def test_valence_degeneracy(self, tmp_path):
        """A degenerate valence pair (bands 2, 3) removes the counts that split it."""
        el = [[[0.0, 0.1, 0.1, 0.3, 0.4, 0.5]]]
        res = degeneracy(tmp_path, el, ifmax=[[3]], ifmin=[[1]])
        assert res["allowed_bands"] == [1, 3, 4, 5]  # 2 dropped
        assert res["allowed_valence_bands"] == [2, 3]  # 1 dropped, full count kept
        assert res["allowed_conduction_bands"] == [1, 2]

    def test_multi_kpoint_reduction(self, tmp_path):
        """A degeneracy at a single k-point excludes that count globally.

        k0 is clean; k1 has a degenerate conduction pair (bands 4, 5). The allowed
        counts are the intersection over k-points, so both the total count 4 and the
        first conduction count drop even though k0 alone would allow them.
        """
        el = [
            [
                [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],  # k0, clean
                [0.0, 0.1, 0.2, 0.3, 0.3, 0.5],  # k1, bands 4,5 degenerate
            ]
        ]
        res = degeneracy(tmp_path, el, ifmax=[[3, 3]], ifmin=[[1, 1]])
        assert res["n_kpoints"] == 2
        assert res["allowed_bands"] == [1, 2, 3, 5]
        assert res["allowed_valence_bands"] == [1, 2, 3]
        assert res["allowed_conduction_bands"] == [2]

    def test_spin_axis_reduction(self, tmp_path):
        """A degeneracy in one spin channel excludes that count globally."""
        el = [
            [[0.0, 0.1, 0.2, 0.3, 0.4, 0.5]],  # spin up, clean
            [[0.0, 0.1, 0.1, 0.3, 0.4, 0.5]],  # spin down, bands 2,3 degenerate
        ]
        res = degeneracy(tmp_path, el, ifmax=[[3], [3]], ifmin=[[1], [1]])
        assert res["n_spins"] == 2
        assert res["allowed_bands"] == [1, 3, 4, 5]
        assert res["allowed_valence_bands"] == [2, 3]
        assert res["allowed_conduction_bands"] == [1, 2]

    def test_tolerance_kwarg(self, tmp_path):
        """A tolerance wider than every gap collapses all allowed counts.

        Only the always-allowed full valence count (nvband) survives.
        """
        el = [[[0.0, 0.1, 0.2, 0.3, 0.4, 0.5]]]  # all gaps 0.1 Ry
        res = degeneracy(tmp_path, el, ifmax=[[3]], ifmin=[[1]], tolerance=0.5)
        assert res["allowed_bands"] == []
        assert res["allowed_valence_bands"] == [3]  # full nvband is always allowed
        assert res["allowed_conduction_bands"] == []

    def test_tolerance_boundary_is_degenerate(self, tmp_path):
        """A gap exactly equal to the tolerance counts as degenerate (not allowed).

        Matches ``degeneracy_check.f90``, which admits a band count only when the gap
        is ``.gt. TOL_Degeneracy``. Uses 0.5 Ry spacings, exactly representable in
        float64, so the gap equals the tolerance with no rounding.
        """
        el = [[[0.0, 0.5, 1.0, 1.5]]]  # every adjacent gap is exactly 0.5 Ry
        res = degeneracy(tmp_path, el, ifmax=[[2]], ifmin=[[1]], tolerance=0.5)
        assert res["allowed_bands"] == []  # gap == tol -> degenerate
        assert res["allowed_valence_bands"] == [2]  # full nvband is always allowed
        assert res["allowed_conduction_bands"] == []

        # A gap just above the tolerance is allowed, so the boundary is the only
        # thing being excluded here.
        el_above = [[[0.0, 0.5, 1.0, 1.5]]]
        res = degeneracy(tmp_path, el_above, ifmax=[[2]], ifmin=[[1]], tolerance=0.5 - 1e-9)
        assert res["allowed_bands"] == [1, 2, 3]

    def test_parse_without_run_matches_run(self, tmp_path):
        """parse_output computes the result on demand if run() was not called."""
        el = [[[0.0, 0.1, 0.2, 0.3, 0.3, 0.5]]]
        write_wfn_h5(tmp_path / "WFN.h5", el, ifmax=[[3]], ifmin=[[1]])

        ran = DegeneracyCheckTask(dirname=str(tmp_path), wfn_fname="WFN.h5")
        ran.run()
        run_result = dict(ran.parse_output())

        fresh = DegeneracyCheckTask(dirname=str(tmp_path), wfn_fname="WFN.h5")
        assert dict(fresh.parse_output()) == run_result

    def test_run_missing_file_raises(self, tmp_path):
        """run() on a nonexistent HDF5 WFN raises FileNotFoundError, not an h5py error."""
        task = DegeneracyCheckTask(dirname=str(tmp_path), wfn_fname="absent.h5")
        with pytest.raises(FileNotFoundError):
            task.run()

    def test_hdf5_suffix_selects_path(self, tmp_path):
        """The '.h5' suffix (not the binary executable) drives the dispatch."""
        assert DegeneracyCheckTask(dirname=str(tmp_path), wfn_fname="WFN.h5")._is_hdf5
        assert not DegeneracyCheckTask(dirname=str(tmp_path), wfn_fname="WFN")._is_hdf5

    def test_pseudobands_wfn_rejected(self, tmp_path):
        """A pseudobands WFN is refused: its spectrum is not physical band energies."""
        el = [[[0.0, 0.1, 0.2, 0.3, 0.4, 0.5]]]
        path = write_wfn_h5(tmp_path / "WFN.h5", el, ifmax=[[3]], ifmin=[[1]])
        with h5py.File(path, "a") as f:
            f["parabands/pseudobands/is_on"] = np.int64(1)
            f["parabands/pseudobands/nb_fixed"] = np.int64(4)

        task = DegeneracyCheckTask(dirname=str(tmp_path), wfn_fname="WFN.h5")
        with pytest.raises(ValueError, match="pseudobands"):
            task.run()

    def test_empty_pseudobands_group_is_not_pseudobands(self, tmp_path):
        """ParaBands writes the group even with pseudobands off; that must not trip."""
        el = [[[0.0, 0.1, 0.2, 0.3, 0.4, 0.5]]]
        path = write_wfn_h5(tmp_path / "WFN.h5", el, ifmax=[[3]], ifmin=[[1]])
        with h5py.File(path, "a") as f:
            f.create_group("parabands/pseudobands")

        task = DegeneracyCheckTask(dirname=str(tmp_path), wfn_fname="WFN.h5")
        task.run()
        assert task.parse_output()["allowed_bands"] == [1, 2, 3, 4, 5]

    def test_read_wfn_h5_mnband(self, tmp_path):
        """read_wfn_h5_mnband returns the total band count from the header."""
        el = [[[0.0, 0.1, 0.2, 0.3, 0.4, 0.5]]]
        path = write_wfn_h5(tmp_path / "WFN.h5", el, ifmax=[[3]], ifmin=[[1]])
        assert read_wfn_h5_mnband(path) == 6
