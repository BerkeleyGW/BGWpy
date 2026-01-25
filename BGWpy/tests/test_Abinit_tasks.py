from __future__ import annotations

import pytest

from BGWpy.core.task import TaskStatus

# Tests now use session-scoped fixtures from conftest.py
# This eliminates redundant expensive calculations


@pytest.mark.e2e
@pytest.mark.abinit
class TestAbinitTasks:
    """Abinit task end-to-end tests using shared session fixtures.

    These tests run complete Abinit DFT calculations with real executables
    and verify that the workflow components work correctly.
    """

    def test_scftask(self, abinit_scftask):
        """Test Abinit SCF density calculation using shared fixture."""
        assert abinit_scftask.get_status() == TaskStatus.COMPLETED

    def test_wfntask(self, abinit_wfntask):
        """Test Abinit density and wavefunction calculation using shared fixture.

        This implicitly tests that the SCF task completed successfully since
        the wfntask fixture depends on abinit_scftask.
        """
        assert abinit_wfntask.get_status() == TaskStatus.COMPLETED

    def test_abi2bgwtask(self, abinit_abi2bgwtask):
        """Test Abinit to BGW conversion using shared fixture.

        This implicitly tests the full chain: SCF -> Wfn -> Abi2Bgw
        since the fixture dependencies ensure all prerequisites are completed.
        """
        assert abinit_abi2bgwtask.get_status() == TaskStatus.COMPLETED
