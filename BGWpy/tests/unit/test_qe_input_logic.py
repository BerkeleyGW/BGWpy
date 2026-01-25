"""Unit tests for Quantum ESPRESSO input generation logic.

These tests verify pure Python logic without requiring external executables.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from BGWpy import QeScfTask, Structure, data


@pytest.mark.unit
class TestQEInputConfiguration:
    """Unit tests for QE task input configuration logic.

    These tests mock kgrid.x to test pure Python logic without external dependencies.
    """

    def test_diagonalization_cg_removes_david_param(self):
        """Test that diago_david_ndim is removed when diagonalization='cg'.

        The 'cg' (conjugate gradient) algorithm doesn't use the diago_david_ndim
        parameter, so it should be automatically removed from the input.
        """
        with patch("BGWpy.DFT.dfttask.KgridTask") as mock_kgrid:
            # Mock kgrid to return dummy k-points
            mock_instance = MagicMock()
            mock_instance.get_kpoints.return_value = ([[0.5, 0.5, 0.5]], [1.0])
            mock_kgrid.return_value = mock_instance

            task = QeScfTask(
                dirname="/tmp/test_bgwpy_cg",
                prefix="GaAs",
                pseudo_dir=data.pseudo_dir,
                pseudos=data.pseudos_GaAs,
                structure=Structure.from_file(data.structure_GaAs),
                ngkpt=[2, 2, 2],
                kshift=[0.5, 0.5, 0.5],
                ecutwfc=8.0,
                nbnd=9,
                variables={
                    "electrons": {
                        "diagonalization": "cg",
                    }
                },
            )

            # Verify diagonalization was set to 'cg'
            assert task.input.electrons["diagonalization"] == "cg"

            # Verify diago_david_ndim was removed
            assert "diago_david_ndim" not in task.input.electrons

            # Verify other parameters are still present
            assert task.input.electrons["diago_full_acc"] is True
            assert task.input.electrons["conv_thr"] == 1.0e-10

    def test_diagonalization_david_keeps_param(self):
        """Test that diago_david_ndim is kept when diagonalization='david'.

        The 'david' algorithm uses the diago_david_ndim parameter to control
        the Davidson diagonalization dimension, so it should be preserved.
        """
        with patch("BGWpy.DFT.dfttask.KgridTask") as mock_kgrid:
            # Mock kgrid to return dummy k-points
            mock_instance = MagicMock()
            mock_instance.get_kpoints.return_value = ([[0.5, 0.5, 0.5]], [1.0])
            mock_kgrid.return_value = mock_instance

            task = QeScfTask(
                dirname="/tmp/test_bgwpy_david",
                prefix="GaAs",
                pseudo_dir=data.pseudo_dir,
                pseudos=data.pseudos_GaAs,
                structure=Structure.from_file(data.structure_GaAs),
                ngkpt=[2, 2, 2],
                kshift=[0.5, 0.5, 0.5],
                ecutwfc=8.0,
                nbnd=9,
                variables={
                    "electrons": {
                        "diagonalization": "david",
                        "diago_david_ndim": 8,
                    }
                },
            )

            # Verify diagonalization is 'david'
            assert task.input.electrons["diagonalization"] == "david"

            # Verify diago_david_ndim is present and has correct value
            assert task.input.electrons["diago_david_ndim"] == 8

    def test_default_diagonalization_is_david(self):
        """Test that default diagonalization method is 'david'."""
        with patch("BGWpy.DFT.dfttask.KgridTask") as mock_kgrid:
            mock_instance = MagicMock()
            mock_instance.get_kpoints.return_value = ([[0.5, 0.5, 0.5]], [1.0])
            mock_kgrid.return_value = mock_instance

            task = QeScfTask(
                dirname="/tmp/test_bgwpy_default",
                prefix="Si",
                pseudo_dir=data.pseudo_dir,
                pseudos=data.pseudos_Si,
                structure=Structure.from_file(data.structure_Si),
                ngkpt=[2, 2, 2],
                kshift=[0.5, 0.5, 0.5],
                ecutwfc=8.0,
                nbnd=9,
            )

            # Verify default diagonalization
            assert task.input.electrons["diagonalization"] == "david"
