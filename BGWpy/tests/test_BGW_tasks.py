from __future__ import annotations

import pytest

from BGWpy.core.task import TaskStatus

# Tests now use session-scoped fixtures from conftest.py
# This eliminates redundant expensive calculations


@pytest.mark.e2e
class TestBGWTasks:
    """BGW task end-to-end tests using shared session fixtures.

    These tests run complete DFT/GW calculations with real executables.
    """

    def test_epsilon(self, bgw_epsilontask):
        """Test Epsilon calculation using shared fixture."""
        assert bgw_epsilontask.get_status() == TaskStatus.COMPLETED

    def test_sigma(self, bgw_sigmatask):
        """Test Sigma calculation using shared fixture."""
        assert bgw_sigmatask.get_status() == TaskStatus.COMPLETED

    def test_kernel(self, bgw_kerneltask):
        """Test Kernel calculation using shared fixture."""
        assert bgw_kerneltask.get_status() == TaskStatus.COMPLETED

    def test_absorption(self, bgw_absorptiontask):
        """Test Absorption calculation using shared fixture.

        Note: This test depends on all previous calculations being complete,
        but pytest fixtures handle the dependency chain automatically.
        """
        assert bgw_absorptiontask.get_status() == TaskStatus.COMPLETED


@pytest.mark.e2e
class TestSigmaVariants:
    """Test specific Sigma calculation variants (end-to-end).

    These tests run complete DFT/GW calculations with real executables
    to verify different Sigma calculation modes.
    """

    def test_HF(self, bgw_sigmatask_hf):
        """Test Hartree-Fock Sigma calculation using shared fixture.

        This tests Sigma with frequency_dependence=-1 (Hartree-Fock mode)
        instead of the default GW approximation.
        """
        assert bgw_sigmatask_hf.get_status() == TaskStatus.COMPLETED
