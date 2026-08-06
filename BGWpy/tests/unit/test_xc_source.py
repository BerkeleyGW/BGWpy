"""Unit tests for the choice of exchange-correlation source handed to Sigma.

Sigma can subtract the DFT XC contribution from three different files: the
``vxc.dat`` matrix elements, the G-space ``VXC`` potential, or the ``kih.dat``
matrix elements of the Kinetic + Ionic + Hartree energy. These tests cover which
pw2bgw flags produce each one, and which Sigma keywords go with it.

Pure Python logic -- no QE / BerkeleyGW executables. ``KgridTask`` is mocked (as
in ``test_qe_input_logic``) so the tasks build their inputs without shelling out
to ``kgrid.x``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from BGWpy import GWFlow, Qe2BgwTask, QeBgwFlow, SigmaTask, Structure, data


def _mock_kgrid(target="BGWpy.DFT.dfttask.KgridTask"):
    """Patch a KgridTask import site to return a fixed single k-point."""
    patcher = patch(target)
    mock = patcher.start()
    instance = MagicMock()
    instance.get_kpoints.return_value = ([[0.0, 0.0, 0.0]], [1.0])
    instance.get_kpt_grid_nosym.return_value = ([[0.0, 0.0, 0.0]], [1.0])
    mock.return_value = instance
    return patcher


@pytest.mark.unit
class TestQe2BgwXcFlags:
    """Which XC files pw2bgw is asked for, and the band range that bounds them."""

    @staticmethod
    def _task(tmp_path, **overrides):
        kwargs = {
            "dirname": str(tmp_path / "wfn"),
            "prefix": "Si",
            "pseudo_dir": data.pseudo_dir,
            "pseudos": data.pseudos_Si_upf,
            "structure": Structure.from_file(data.structure_Si),
            "ngkpt": [2, 2, 2],
            "ecutwfc": 8.0,
        }
        kwargs.update(overrides)
        patcher = _mock_kgrid()
        try:
            return Qe2BgwTask(**kwargs)
        finally:
            patcher.stop()

    def test_density_still_implies_vxc_dat(self, tmp_path):
        """Back-compat: rhog_flag alone keeps producing vxc.dat over 1..nbnd."""
        task = self._task(tmp_path, rhog_flag=True, nbnd=9)
        assert task.input["rhog_flag"] is True
        assert task.input["vxc_flag"] is True
        assert task.input["vxc_file"] == "vxc.dat"
        assert task.input["vxc_diag_nmin"] == 1
        assert task.input["vxc_diag_nmax"] == 9

    def test_no_kih_keys_unless_asked(self, tmp_path):
        """Back-compat: input files of existing callers gain no new namelist keys."""
        task = self._task(tmp_path, rhog_flag=True, nbnd=9)
        assert "kih_flag" not in task.input
        assert "kih_file" not in task.input

    def test_kih_flag_replaces_vxc_dat(self, tmp_path):
        """kih.dat and vxc.dat are alternatives, so asking for kih drops the
        vxc.dat that rhog_flag would otherwise have implied."""
        task = self._task(tmp_path, rhog_flag=True, nbnd=9, kih_flag=True)
        assert task.input["kih_flag"] is True
        assert task.input["kih_file"] == "kih.dat"
        assert task.input["vxc_flag"] is False
        assert task.kih_dat_fname.endswith("/kih.dat")

    def test_kih_without_density(self, tmp_path):
        """pw2bgw's XC flags are independent of rhog_flag, and so are BGWpy's:
        Sigma reads RHO only for the Hybertsen-Louie GPP."""
        task = self._task(tmp_path, nbnd=9, kih_flag=True)
        assert "rhog_flag" not in task.input
        assert task.input["kih_flag"] is True
        assert task.input["vxc_diag_nmax"] == 9

    def test_vxc_flag_honoured_without_density(self, tmp_path):
        """vxc_flag used to be silently discarded unless rhog_flag was also set."""
        task = self._task(tmp_path, nbnd=9, vxc_flag=True)
        assert task.input["vxc_flag"] is True
        assert task.input["vxc_file"] == "vxc.dat"
        assert task.input["vxc_diag_nmax"] == 9
        assert "rhog_flag" not in task.input

    def test_kih_dat_fname_implies_the_flag(self, tmp_path):
        """Naming the output file switches the flag on, as rho_fname does."""
        task = self._task(tmp_path, nbnd=9, kih_dat_fname="my_kih.dat")
        assert task.input["kih_flag"] is True
        assert task.input["kih_file"] == "my_kih.dat"
        assert task.kih_dat_fname.endswith("/my_kih.dat")

    def test_kih_requires_a_band_range(self, tmp_path):
        """pw2bgw aliases kih_diag_nmin/nmax onto vxc_diag_nmin/nmax -- without a
        band range the fallback is a single band, so kih.dat would cover one band
        and Sigma would read past the end of it."""
        with pytest.raises(ValueError, match="band range"):
            self._task(tmp_path, kih_flag=True)

    def test_kih_accepts_an_explicit_band_range(self, tmp_path):
        task = self._task(tmp_path, kih_flag=True, vxc_diag_nmax=12)
        assert task.input["vxc_diag_nmax"] == 12

    def test_explicit_gspace_vxc_selection(self, tmp_path):
        """The ParaBands / kph route, which names both flags explicitly."""
        task = self._task(
            tmp_path, rhog_flag=True, nbnd=9, vxc_flag=False, vxcg_flag=True, vxc_fname="VXC"
        )
        assert task.input["vxc_flag"] is False
        assert task.input["vxcg_flag"] is True
        assert task.input["vxcg_file"] == "VXC"

    def test_gspace_vxc_alone_drops_vxc_dat(self, tmp_path):
        """Sigma reads exactly one XC file, so vxcg_flag suppresses the vxc.dat
        that rhog_flag would otherwise imply -- no need to say vxc_flag=False."""
        task = self._task(tmp_path, rhog_flag=True, nbnd=9, vxcg_flag=True)
        assert task.input["vxcg_flag"] is True
        assert task.input["vxc_flag"] is False

    def test_vxc_dat_can_be_forced_alongside(self, tmp_path):
        """The suppression is only a default; asking for both still gives both."""
        task = self._task(tmp_path, rhog_flag=True, nbnd=9, vxcg_flag=True, vxc_flag=True)
        assert task.input["vxcg_flag"] is True
        assert task.input["vxc_flag"] is True


@pytest.mark.unit
class TestSigmaXcSource:
    """The Sigma side: one XC source, with its matching keywords and link."""

    @staticmethod
    def _task(tmp_path, **overrides):
        kwargs = {
            "dirname": str(tmp_path / "sigma"),
            "wfn_co_fname": str(tmp_path / "wfn.cplx"),
            "rho_fname": str(tmp_path / "rho.real"),
            "ibnd_min": 1,
            "ibnd_max": 8,
            "kpts": [[0.0, 0.0, 0.0]],
        }
        kwargs.update(overrides)
        return SigmaTask(**kwargs)

    @staticmethod
    def _link_dests(task):
        return [dest for _target, dest in task.runscript.links]

    def test_vxc_dat_adds_no_keywords(self, tmp_path):
        """Back-compat: the default vxc.dat path stays keyword-free."""
        task = self._task(tmp_path, vxc_dat_fname=str(tmp_path / "vxc.dat"))
        assert task.input.keywords == []
        assert "vxc.dat" in self._link_dests(task)

    def test_gspace_vxc_adds_dont_use_vxcdat(self, tmp_path):
        task = self._task(tmp_path, vxc_fname=str(tmp_path / "VXC"))
        assert task.input.keywords == ["dont_use_vxcdat"]
        assert "VXC" in self._link_dests(task)

    def test_kih_adds_both_keywords(self, tmp_path):
        """Sigma calls die() if use_vxcdat is left on alongside use_kihdat."""
        task = self._task(tmp_path, kih_dat_fname=str(tmp_path / "kih.dat"))
        assert set(task.input.keywords) == {"dont_use_vxcdat", "use_kihdat"}
        # Sigma opens the literal name 'kih.dat'.
        assert "kih.dat" in self._link_dests(task)

    def test_kih_keywords_not_duplicated(self, tmp_path):
        task = self._task(
            tmp_path,
            kih_dat_fname=str(tmp_path / "kih.dat"),
            extra_lines=["dont_use_vxcdat", "screening_semiconductor"],
        )
        assert task.input.keywords.count("dont_use_vxcdat") == 1
        assert "screening_semiconductor" in task.input.keywords

    def test_kih_conflicts_with_vxc(self, tmp_path):
        for conflicting in ("vxc_dat_fname", "vxc_fname"):
            with pytest.raises(ValueError, match="mutually exclusive"):
                self._task(
                    tmp_path,
                    kih_dat_fname=str(tmp_path / "kih.dat"),
                    **{conflicting: str(tmp_path / "vxc")},
                )

    def test_both_vxc_sources_warn_and_keep_precedence(self, tmp_path):
        """Ambiguous but long-standing: vxc_dat_fname wins, as it always has."""
        with pytest.warns(UserWarning, match="vxc_dat_fname"):
            task = self._task(
                tmp_path,
                vxc_dat_fname=str(tmp_path / "vxc.dat"),
                vxc_fname=str(tmp_path / "VXC"),
            )
        assert task.vxc_dat_fname.endswith("vxc.dat")
        assert "vxc.dat" in self._link_dests(task)

    def test_no_xc_source_raises(self, tmp_path):
        with pytest.raises(ValueError, match="kih_dat_fname"):
            self._task(tmp_path)


@pytest.mark.unit
class TestFlowWiring:
    """kih plumbed through the QE wavefunction flow and the GW workflow."""

    @staticmethod
    def _qe_flow(tmp_path, **overrides):
        kwargs = {
            "dirname": str(tmp_path / "wfn"),
            "structure": Structure.from_file(data.structure_Si),
            "prefix": "Si",
            "pseudo_dir": data.pseudo_dir,
            "pseudos": data.pseudos_Si_upf,
            "charge_density_fname": str(tmp_path / "rho"),
            "data_file_fname": str(tmp_path / "data-file.xml"),
            "ecutwfc": 8.0,
            "ngkpt": [2, 2, 2],
            "nbnd": 9,
        }
        kwargs.update(overrides)
        patcher = _mock_kgrid()
        try:
            return QeBgwFlow(**kwargs)
        finally:
            patcher.stop()

    def test_qebgwflow_forwards_kih(self, tmp_path):
        flow = self._qe_flow(tmp_path, rhog_flag=True, kih_flag=True)
        assert flow.wfnbgwntask.input["kih_flag"] is True
        assert flow.kih_dat_fname.endswith("/kih.dat")

    def test_qebgwflow_default_is_vxc_dat(self, tmp_path):
        flow = self._qe_flow(tmp_path, rhog_flag=True)
        assert flow.wfnbgwntask.input["vxc_flag"] is True
        assert flow.vxc_dat_fname.endswith("/vxc.dat")

    def test_explicit_kih_flag_false_emits_nothing(self, tmp_path):
        """GWFlow always forwards kih_flag, so kih_flag=False must be inert."""
        flow = self._qe_flow(tmp_path, rhog_flag=True, kih_flag=False)
        assert "kih_flag" not in flow.wfnbgwntask.input
        assert flow.wfnbgwntask.input["vxc_flag"] is True

    @staticmethod
    def _gw_flow(tmp_path, **overrides):
        kwargs = {
            "dirname": str(tmp_path / "gw"),
            "structure": Structure.from_file(data.structure_Si),
            "prefix": "Si",
            "pseudo_dir": data.pseudo_dir,
            "pseudos": data.pseudos_Si_upf,
            "dft_flavor": "espresso",
            "ecutwfc": 8.0,
            "ecuteps": 4.0,
            "ngkpt": [2, 2, 2],
            "kshift": [0.5, 0.5, 0.5],
            "qshift": [0.0, 0.0, 0.001],
            "nbnd": 9,
            "ibnd_min": 1,
            "ibnd_max": 8,
        }
        kwargs.update(overrides)
        patchers = [
            _mock_kgrid(),
            _mock_kgrid("BGWpy.BGW.sigmatask.KgridTask"),
            _mock_kgrid("BGWpy.BGW.epsilontask.KgridTask"),
        ]
        try:
            return GWFlow(**kwargs)
        finally:
            for patcher in patchers:
                patcher.stop()

    def test_gwflow_default_still_uses_vxc_dat(self, tmp_path):
        """Back-compat: without use_kih the workflow is wired exactly as before."""
        flow = self._gw_flow(tmp_path)
        assert flow.wfntask_ush.wfnbgwntask.input["vxc_flag"] is True
        assert "kih_flag" not in flow.wfntask_ush.wfnbgwntask.input
        assert "use_kihdat" not in flow.sigmatask.input.keywords
        dests = [dest for _target, dest in flow.sigmatask.runscript.links]
        assert "vxc.dat" in dests

    def test_gwflow_use_kih_reaches_sigma(self, tmp_path):
        """The whole chain: pw2bgw writes kih.dat, Sigma reads it with both
        keywords and never asks for a vxc.dat that was not produced."""
        flow = self._gw_flow(tmp_path, use_kih=True)
        assert flow.wfntask_ush.wfnbgwntask.input["kih_flag"] is True
        assert flow.wfntask_ush.wfnbgwntask.input["vxc_flag"] is False
        assert set(flow.sigmatask.input.keywords) >= {"dont_use_vxcdat", "use_kihdat"}
        dests = [dest for _target, dest in flow.sigmatask.runscript.links]
        assert "kih.dat" in dests
        assert "vxc.dat" not in dests

    def test_gwflow_rejects_kih_for_abinit(self, tmp_path):
        """Only pw2bgw writes a kih.dat; Abinit has no equivalent."""
        with pytest.raises(ValueError, match="Quantum Espresso"):
            self._gw_flow(tmp_path, dft_flavor="abinit", use_kih=True)
