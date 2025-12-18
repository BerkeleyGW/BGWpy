from __future__ import annotations

from copy import copy
from pathlib import Path

from BGWpy import BSEFlow, GWFlow

from .test_BGW_tasks import TestBGWTasksMaker


class TestFlows(TestBGWTasksMaker):
    common_kwargs = copy(TestBGWTasksMaker.common_kwargs)
    common_kwargs.update(
        dft_flavor="espresso",
        nbnd_fine=9,
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        sigma_extra_lines=["screening_semiconductor"],
        kernel_extra_lines=[
            "use_symmetries_coarse_grid",
            "screening_semiconductor",
        ],
        absorption_extra_lines=[
            "use_symmetries_coarse_grid",
            "no_symmetries_fine_grid",
            "no_symmetries_shifted_grid",
            "screening_semiconductor",
            "use_velocity",
            "gaussian_broadening",
            "eqp_co_corrections",
        ],
        absorption_extra_variables={
            "energy_resolution": 0.15,
        },
    )

    def get_gwflow(self):
        kwargs = copy(self.common_kwargs)
        return GWFlow(dirname=Path(self.tmpdir) / "GW", **kwargs)

    def get_bseflow(self):
        kwargs = copy(self.common_kwargs)
        return BSEFlow(dirname=Path(self.tmpdir) / "BSE", **kwargs)

    def test_gwflow(self):
        """Test GWFlow."""
        flow = self.get_gwflow()
        flow.write()
        flow.run()
        flow.report()
        for task in flow.tasks:
            self.assertCompleted(task)

    def test_bseflow(self):
        """Test BSEFlow."""
        flow = self.get_bseflow()
        flow.write()
        flow.run()
        flow.report()
        for task in flow.tasks:
            self.assertCompleted(task)
