from __future__ import annotations

import pytest

from BGWpy.core.task import TaskStatus

# Tests now use session-scoped fixtures from conftest.py
# This eliminates redundant expensive calculations


@pytest.mark.e2e
class TestFlows:
    """Test BGW workflow (Flow) classes using shared session fixtures (end-to-end).

    These tests run complete DFT/GW/BSE workflows with real executables.
    """

    @pytest.mark.flow
    def test_gwflow(self, bgw_gwflow):
        """Test GW workflow using shared fixture.

        GWFlow runs the complete GW workflow: DFT → Epsilon → Sigma
        """
        assert bgw_gwflow.get_status() == TaskStatus.COMPLETED
        # Verify all tasks in the flow completed
        for task in bgw_gwflow.tasks:
            assert task.get_status() == TaskStatus.COMPLETED

    @pytest.mark.flow
    def test_bseflow(self, bgw_bseflow):
        """Test BSE workflow using shared fixture.

        BSEFlow runs the complete BSE workflow: DFT → Epsilon → Sigma → Kernel → Absorption
        """
        assert bgw_bseflow.get_status() == TaskStatus.COMPLETED
        # Verify all tasks in the flow completed
        for task in bgw_bseflow.tasks:
            assert task.get_status() == TaskStatus.COMPLETED

    @pytest.mark.flow
    @pytest.mark.abinit
    def test_abinit_bgwflow(self, abinit_bgwflow):
        """Test Abinit BGW flow using shared fixture.

        This tests the AbinitBgwFlow class which combines wavefunction
        generation and BGW conversion in a single flow object.
        This implicitly tests the full chain: SCF -> WfnBgwFlow
        """
        assert abinit_bgwflow.get_status() == TaskStatus.COMPLETED
