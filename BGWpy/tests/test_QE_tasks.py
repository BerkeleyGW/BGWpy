from __future__ import annotations

import pytest

from BGWpy.core.task import TaskStatus

# Tests now use session-scoped fixtures from conftest.py
# This eliminates redundant expensive calculations


@pytest.mark.e2e
class TestQETasks:
    """QE task end-to-end tests using shared session fixtures.

    These tests run complete DFT calculations with real QE executables.
    """

    def test_scftask(self, qe_scftask):
        """Test QE SCF calculation using shared fixture."""
        assert qe_scftask.get_status() == TaskStatus.COMPLETED

    def test_wfntask(self, qe_wfntask_ksh):
        """Test QE wavefunction calculation using shared fixture."""
        assert qe_wfntask_ksh.get_status() == TaskStatus.COMPLETED

    def test_pw2bgwtask(self, qe_pw2bgwtask_ksh):
        """Test pw2bgw conversion using shared fixture."""
        assert qe_pw2bgwtask_ksh.get_status() == TaskStatus.COMPLETED
