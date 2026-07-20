"""Unit tests for the patch_sample_* k-grid samplers.

These test pure Python/numpy logic without requiring external executables.
"""

from __future__ import annotations

import numpy as np
import pytest

from BGWpy.BGW.kgrid import patch_sample_cube, patch_sample_sphere


@pytest.mark.unit
class TestPatchSampleBoundary:
    """A half_side/r_patch landing exactly on a grid shell must keep that shell.

    Without a tolerance the boundary points are dropped asymmetrically by
    floating-point noise (e.g. a 0.03 cube on a 100^3 grid yielded 216 = 6^3
    instead of 343 = 7^3, keeping +0.03 but not -0.03).
    """

    def test_cube_keeps_on_grid_boundary_shell(self):
        kpts, wtks = patch_sample_cube(ngkpt=[100, 100, 100], half_side=0.03)
        assert len(kpts) == 7**3
        # symmetric about the centre along every axis
        folded = (kpts + 0.5) % 1.0 - 0.5
        for axis in range(3):
            vals = np.unique(np.round(folded[:, axis], 6))
            np.testing.assert_allclose(vals, np.round(-vals[::-1], 6))
        np.testing.assert_allclose(wtks.sum(), 1.0)

    def test_cube_just_below_shell_excludes_it(self):
        # a half_side genuinely inside the shell must not grab it via the tolerance
        kpts, _ = patch_sample_cube(ngkpt=[100, 100, 100], half_side=0.0295)
        assert len(kpts) == 5**3

    def test_sphere_keeps_on_grid_boundary_point(self):
        # r_patch = 0.03 reaches the six face points at distance exactly 0.03
        kpts, _ = patch_sample_sphere(ngkpt=[100, 100, 100], r_patch=0.03)
        folded = (kpts + 0.5) % 1.0 - 0.5
        assert np.any(np.all(np.isclose(folded, [0.03, 0.0, 0.0]), axis=1))
        assert np.any(np.all(np.isclose(folded, [-0.03, 0.0, 0.0]), axis=1))


@pytest.mark.unit
class TestPatchSampleDegenerate:
    """The only two outcomes worth a warning: an empty patch, or one covering the grid.

    An ordinary patch must warn nothing -- the selected count is just ``len(kpts)``.
    The suite runs with ``filterwarnings = ["error", ...]`` (pyproject.toml), so every
    other test in this file fails outright if a stray warning is emitted.
    """

    def test_empty_cube_warns(self):
        # centre between grid points, half_side below the distance to any of them
        with pytest.warns(UserWarning, match="selected no k-points"):
            kpts, _ = patch_sample_cube(
                ngkpt=[10, 10, 10], half_side=0.01, center=[0.05, 0.05, 0.05]
            )
        assert len(kpts) == 0

    def test_empty_sphere_warns(self):
        with pytest.warns(UserWarning, match="selected no k-points"):
            kpts, _ = patch_sample_sphere(
                ngkpt=[10, 10, 10], r_patch=0.01, center=[0.05, 0.05, 0.05]
            )
        assert len(kpts) == 0

    def test_cube_covering_whole_grid_warns(self):
        # folding into [-0.5, 0.5) caps the Chebyshev distance at 0.5
        with pytest.warns(UserWarning, match="kept the whole"):
            kpts, _ = patch_sample_cube(ngkpt=[4, 4, 4], half_side=0.5)
        assert len(kpts) == 4**3

    def test_sphere_covering_whole_grid_warns(self):
        # the folded corner sits at sqrt(3)/2 ~ 0.866
        with pytest.warns(UserWarning, match="kept the whole"):
            kpts, _ = patch_sample_sphere(ngkpt=[4, 4, 4], r_patch=0.9)
        assert len(kpts) == 4**3
