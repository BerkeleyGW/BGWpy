"""Unit tests for ParaBands input/task construction and the QE ParaBands flow.

Pure Python logic -- no ParaBands / QE executables. The flow tests mock ``KgridTask``
(as ``test_qe_input_logic`` does) so the QE sub-tasks build their inputs without
shelling out to ``kgrid.x``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from BGWpy import ParabandsTask, QeParabandsFlow, Structure, data
from BGWpy.BGW.inputs import ParabandsInput


@pytest.mark.unit
class TestParabandsInput:
    """The parabands.inp variable/keyword assembly."""

    def test_required_variables_present(self):
        inp = ParabandsInput("WFN_in", "WFN.h5")
        assert inp.variables["input_wfn_file"] == "WFN_in"
        assert inp.variables["output_wfn_file"] == "WFN.h5"
        assert inp.variables["vsc_file"] == "VSC"
        assert inp.variables["vkb_file"] == "VKB"  # default present

    def test_vkb_omitted_when_none(self):
        inp = ParabandsInput("WFN_in", "WFN.h5", vkb_file=None)
        assert "vkb_file" not in inp.variables

    def test_nbnd_and_extra_variables(self):
        """nbnd is emitted under the BerkeleyGW keyword ``number_bands``."""
        inp = ParabandsInput("WFN_in", "WFN.h5", nbnd=200, solver_algorithm=10, block_size=8)
        assert inp.variables["number_bands"] == 200
        assert inp.variables["solver_algorithm"] == 10
        assert inp.variables["block_size"] == 8

    def test_nbnd_omitted_when_none(self):
        inp = ParabandsInput("WFN_in", "WFN.h5")
        assert "number_bands" not in inp.variables

    def test_keywords_render_as_bare_lines(self):
        inp = ParabandsInput("WFN_in", "WFN.h5", "use_pseudobands")
        assert "use_pseudobands" in inp.keywords
        assert "use_pseudobands" in str(inp)


@pytest.mark.unit
class TestParabandsTask:
    """ParaBands task construction (no executable run)."""

    def _task(self, tmp_path, **kwargs):
        defaults = {
            "dirname": str(tmp_path / "parabands"),
            "wfn_in_fname": str(tmp_path / "wfn.cplx"),
            "vsc_fname": str(tmp_path / "VSC"),
            "nbnd": 100,
        }
        defaults.update(kwargs)
        return ParabandsTask(**defaults)

    def test_solver_algorithm_defaults_to_auto(self, tmp_path):
        """The default solver_algorithm is -1 (ParaBands auto-selects the solver)."""
        task = self._task(tmp_path)
        assert task.input.variables["solver_algorithm"] == -1
        assert task.input.variables["number_bands"] == 100

    def test_wfn_out_fname_is_under_dirname(self, tmp_path):
        task = self._task(tmp_path, wfn_out_fname="WFN.h5")
        assert task.wfn_out_fname == str(tmp_path / "parabands" / "WFN.h5")

    def test_non_h5_output_rejected(self, tmp_path):
        """ParaBands always writes HDF5; a non-'.h5' output name is a hard error."""
        with pytest.raises(ValueError, match="HDF5"):
            self._task(tmp_path, wfn_out_fname="WFN")

    def test_vkb_linked_only_when_given(self, tmp_path):
        """VKB is linked into the run dir only when a vkb_fname is supplied."""
        links_without = {d for _, d in self._task(tmp_path).runscript.links}
        assert "VKB" not in links_without

        with_vkb = self._task(tmp_path, vkb_fname=str(tmp_path / "VKB"))
        links_with = {d for _, d in with_vkb.runscript.links}
        assert {"WFN_in", "VSC", "VKB"} <= links_with

    def test_extra_lines_forwarded_to_input(self, tmp_path):
        task = self._task(tmp_path, extra_lines=["use_pseudobands"])
        assert "use_pseudobands" in task.input.keywords

    def test_no_hdf5_config_warns(self, tmp_path, monkeypatch):
        """With BGWpy configured without HDF5, constructing the task warns."""
        monkeypatch.setattr(ParabandsTask, "_use_hdf5", False)
        with pytest.warns(UserWarning, match="HDF5"):
            self._task(tmp_path)


@pytest.mark.unit
class TestQeParabandsFlow:
    """The QE ParaBands flow: output wiring and the rho/vxc file-name properties."""

    @staticmethod
    def _make_flow(tmp_path, **overrides):
        """Build a QeParabandsFlow with kgrid.x mocked away."""
        kwargs = {
            "dirname": str(tmp_path / "WFN"),
            "structure": Structure.from_file(data.structure_Si),
            "prefix": "Si",
            "pseudo_dir": data.pseudo_dir,
            "pseudos": data.pseudos_Si_upf,
            "charge_density_fname": str(tmp_path / "rho"),
            "data_file_fname": str(tmp_path / "data-file.xml"),
            "ecutwfc": 8.0,
            "ngkpt": [2, 2, 2],
            "kshift": [0.0, 0.0, 0.0],
            "seed_nbnd": 8,
            "nbnd": 100,
        }
        kwargs.update(overrides)
        with patch("BGWpy.DFT.dfttask.KgridTask") as mock_kgrid:
            instance = MagicMock()
            instance.get_kpoints.return_value = ([[0.0, 0.0, 0.0]], [1.0])
            instance.get_kpt_grid_nosym.return_value = ([[0.0, 0.0, 0.0]], [1.0])
            mock_kgrid.return_value = instance
            return QeParabandsFlow(**kwargs)

    def test_wfn_fname_points_at_parabands_output(self, tmp_path):
        flow = self._make_flow(tmp_path)
        assert flow.wfn_fname.endswith("parabands/WFN.h5")

    def test_solver_algorithm_default_reaches_task(self, tmp_path):
        flow = self._make_flow(tmp_path)
        assert flow.parabandstask.input.variables["solver_algorithm"] == -1

    def test_vxc_fname_is_gspace_vxc_with_vxcg(self, tmp_path):
        """rhog_flag + use_vxcg (default): pw2bgw is told to write the G-space VXC."""
        flow = self._make_flow(tmp_path, rhog_flag=True)
        assert flow.vxc_fname.endswith("/VXC")
        assert flow.pw2bgwtask.input["vxcg_flag"] is True
        assert flow.pw2bgwtask.input["vxc_flag"] is False

    def test_vxc_dat_fname_used_without_vxcg(self, tmp_path):
        """rhog_flag + use_vxcg=False: pw2bgw writes the legacy vxc.dat instead."""
        flow = self._make_flow(tmp_path, rhog_flag=True, use_vxcg=False)
        assert flow.vxc_dat_fname.endswith("/vxc.dat")
        assert flow.pw2bgwtask.input["vxc_flag"] is True
        assert flow.pw2bgwtask.input["vxcg_flag"] is False

    def test_fnames_unguarded_without_rhog(self, tmp_path):
        """Without rhog_flag nothing XC-ish is written, but the paths still resolve.

        Deliberate: these mirror the ``*_fname`` properties on ``Qe2BgwTask`` (and
        ``Abi2BgwTask`` / ``AbinitBgwFlow``), which name the file a task *would* write
        without checking the flags that decide whether it does. Callers must only read
        these off a flow built with the matching flags.
        """
        flow = self._make_flow(tmp_path)  # rhog_flag=False
        assert flow.rho_fname
        assert flow.vxc_fname
        assert flow.vxc_dat_fname
        assert not flow.pw2bgwtask.input.get("rhog_flag")

    def test_pseudobands_requires_nbnd_cond_prot(self, tmp_path):
        with pytest.raises(ValueError, match="nbnd_cond_prot"):
            self._make_flow(tmp_path, use_pseudobands=True)

    def test_pseudobands_sets_keyword_and_window(self, tmp_path):
        """nbnd_cond_prot is emitted under the ParaBands keyword protected_cond_bands."""
        flow = self._make_flow(tmp_path, use_pseudobands=True, nbnd_cond_prot=24)
        pb_input = flow.parabandstask.input
        assert "use_pseudobands" in pb_input.keywords
        assert pb_input.variables["protected_cond_bands"] == 24
