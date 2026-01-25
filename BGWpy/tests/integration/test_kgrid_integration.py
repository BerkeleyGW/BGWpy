"""Integration tests for kgrid.x interaction.

These tests verify that BGWpy can correctly interact with the BerkeleyGW kgrid.x
executable: call it, parse output, and generate k-point grids.
"""

from __future__ import annotations

import pytest

from BGWpy import Structure, data
from BGWpy.BGW.kgrid import KgridTask


@pytest.mark.integration
class TestKgridIntegration:
    """Integration tests for kgrid.x executable interaction.

    These tests require kgrid.x to be installed and available in PATH.
    They verify that BGWpy can successfully call kgrid.x and parse its output.

    These tests will FAIL if kgrid.x is not available - this is intentional.
    Integration tests should not skip missing dependencies.
    """

    def test_kgrid_basic_execution(self, tmp_path):
        """Test that kgrid.x can be called and returns k-points.

        This is a basic smoke test that kgrid.x runs without crashing.
        """
        structure = Structure.from_file(data.structure_Si)

        task = KgridTask(
            structure=structure,
            ngkpt=[2, 2, 2],
            kshift=[0.0, 0.0, 0.0],
            dirname=str(tmp_path / "kgrid_basic"),
        )

        task.write()
        task.run()

        # Verify we got k-points back
        kpts, wtks = task.get_kpoints()
        assert len(kpts) > 0
        assert len(kpts) == len(wtks)
        assert all(len(kpt) == 3 for kpt in kpts)

    def test_kgrid_shifted_grid(self, tmp_path):
        """Test kgrid.x with shifted k-point grid."""
        structure = Structure.from_file(data.structure_Si)

        task = KgridTask(
            structure=structure,
            ngkpt=[2, 2, 2],
            kshift=[0.5, 0.5, 0.5],
            dirname=str(tmp_path / "kgrid_shifted"),
        )

        task.write()
        task.run()

        kpts, _wtks = task.get_kpoints()
        assert len(kpts) > 0
        # Verify k-points are actually shifted (not at Gamma)
        # Shifted grid should not have [0,0,0] k-point
        gamma_found = any(all(abs(k) < 1e-6 for k in kpt) for kpt in kpts)
        assert not gamma_found, "Shifted grid should not contain Gamma point"

    def test_kgrid_weights_positive_and_consistent(self, tmp_path):
        """Test that k-point weights are positive and consistent.

        Note: kgrid.x returns unnormalized weights (multiplicities), not normalized
        weights that sum to 1.0. The weights represent the number of equivalent
        k-points in the full BZ before symmetry reduction.
        """
        structure = Structure.from_file(data.structure_Si)

        task = KgridTask(
            structure=structure,
            ngkpt=[3, 3, 3],
            kshift=[0.0, 0.0, 0.0],
            dirname=str(tmp_path / "kgrid_weights"),
        )

        task.write()
        task.run()

        _kpts, wtks = task.get_kpoints()

        # Verify all weights are positive
        assert all(w > 0 for w in wtks), "All weights should be positive"

        # Verify total weight equals the full grid size (3*3*3 = 27)
        total_weight = sum(wtks)
        full_grid_size = 3 * 3 * 3
        assert abs(total_weight - full_grid_size) < 1e-6, (
            f"Weights sum to {total_weight}, expected {full_grid_size} (full grid size)"
        )

    def test_kgrid_with_symmetry(self, tmp_path):
        """Test kgrid.x with symmetry reduction enabled (default)."""
        structure = Structure.from_file(data.structure_Si)

        task = KgridTask(
            structure=structure,
            ngkpt=[4, 4, 4],
            kshift=[0.0, 0.0, 0.0],
            dirname=str(tmp_path / "kgrid_sym"),
        )

        task.write()
        task.run()

        kpts_with_sym, _ = task.get_kpoints()

        # For a 4x4x4 grid with symmetry, Si should have fewer than 64 k-points
        assert len(kpts_with_sym) < 64, "Symmetry should reduce number of k-points"

    def test_kgrid_output_files_created(self, tmp_path):
        """Test that kgrid.x creates expected output files."""
        structure = Structure.from_file(data.structure_Si)
        dirname = tmp_path / "kgrid_files"

        task = KgridTask(
            structure=structure,
            ngkpt=[2, 2, 2],
            kshift=[0.0, 0.0, 0.0],
            dirname=str(dirname),
        )

        task.write()
        task.run()

        # Check that input file was created
        assert (dirname / task.inputname).exists()

        # Check that output file was created
        assert (dirname / task.outputname).exists()

        # Check that log file was created
        assert (dirname / task.logname).exists()

    def test_kgrid_different_materials(self, tmp_path):
        """Test kgrid.x works with different crystal structures."""
        for structure_file, name in [
            (data.structure_Si, "Si"),
            (data.structure_GaAs, "GaAs"),
        ]:
            structure = Structure.from_file(structure_file)

            task = KgridTask(
                structure=structure,
                ngkpt=[2, 2, 2],
                kshift=[0.0, 0.0, 0.0],
                dirname=str(tmp_path / f"kgrid_{name}"),
            )

            task.write()
            task.run()

            kpts, wtks = task.get_kpoints()
            assert len(kpts) > 0, f"Failed to get k-points for {name}"

            # Verify weights are positive and sum to full grid size (2*2*2 = 8)
            assert all(w > 0 for w in wtks), f"All weights should be positive for {name}"
            full_grid_size = 2 * 2 * 2
            assert abs(sum(wtks) - full_grid_size) < 1e-6, (
                f"Weights sum to {sum(wtks)}, expected {full_grid_size} for {name}"
            )
