"""Shared pytest fixtures for BGWpy tests.

This module provides session-scoped fixtures that run expensive calculations
once and share the results across multiple test functions, eliminating redundancy.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from BGWpy import (
    AbsorptionTask,
    BSEFlow,
    EpsilonTask,
    GWFlow,
    KernelTask,
    SigmaTask,
    Structure,
    data,
)
from BGWpy.Abinit import Abi2BgwTask, AbinitBgwFlow, AbinitScfTask, AbinitWfnTask
from BGWpy.QE import Qe2BgwTask, QeScfTask, QeWfnTask

# Test configuration constants
# For 2x2x2 k-grid: 8 k-points total, 7 q-points (excluding Gamma)
NPROC_QE = 8  # QE tasks
NPROC_ABINIT = 8
NPROC_BGW_QPOINT = 4  # BGW tasks that parallelize over q-points (epsilon, kernel)
NPROC_BGW_GENERAL = 8  # BGW tasks with more flexible parallelization (sigma, absorption)


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--tmpdir-base",
        action="store",
        default=None,
        help="Base directory for temporary test files (default: system temp dir). "
        "Use this to run tests on a different filesystem, e.g., --tmpdir-base=$SCRATCH/tmp",
    )


@pytest.fixture(scope="session")
def session_tmpdir(request):
    """Create a temporary directory that persists for the entire test session.

    The directory is preserved only if tests fail, allowing inspection of failures.
    If tests fail, the directory is also copied to ./tmp.Tests for easier access.

    The base directory can be customized with --tmpdir-base option to use a different
    filesystem (e.g., to avoid Lustre HDF5 issues on /tmp).
    """
    tmpdir_base = request.config.getoption("--tmpdir-base")
    if tmpdir_base:
        tmpdir_base = Path(tmpdir_base).expanduser().resolve()
        tmpdir_base.mkdir(parents=True, exist_ok=True)
        tmpdir = tempfile.mkdtemp(prefix="bgwpy_tests_", dir=str(tmpdir_base))
    else:
        tmpdir = tempfile.mkdtemp(prefix="bgwpy_tests_")

    # Store tmpdir and state in config so pytest hooks can access it
    request.config._session_tmpdir = tmpdir
    request.config._session_failed = False

    separator = "=" * 70
    print(f"\n{separator}")
    print(f"Test session directory: {tmpdir}")
    print(f"{separator}\n")
    return tmpdir


def pytest_sessionstart(session):
    """Print information at the start of the test session."""
    separator = "=" * 70
    tmpdir_base = session.config.getoption("--tmpdir-base")

    print(f"\n{separator}")
    print("BGWpy test session starting")
    if tmpdir_base:
        print(f"Using custom temp directory base: {tmpdir_base}")
    else:
        print("Using system default temp directory")
    print("Temporary test directories will be preserved for inspection.")
    print("If tests fail, directories will be copied to ./tmp.Tests/")
    print(f"{separator}\n")


def pytest_sessionfinish(session, exitstatus):
    """Handle cleanup: preserve on failure, clean up on success."""
    # Get the session tmpdir if it was created
    if hasattr(session, "config"):
        tmpdir = getattr(session.config, "_session_tmpdir", None)
        # Check if any tests failed (standard pytest way)
        session_failed = session.testsfailed > 0
        if tmpdir and Path(tmpdir).exists():
            separator = "=" * 70
            if session_failed:
                # Copy to local tmp.Tests for easier access
                local_testdir = Path("tmp.Tests")
                local_tmpdir = local_testdir / Path(tmpdir).name

                if not local_testdir.exists():
                    local_testdir.mkdir(parents=True, exist_ok=True)

                if not local_tmpdir.exists():
                    print(f"\n{separator}")
                    print("Copying test directory for inspection...")
                    print(f"  From: {tmpdir}")
                    print(f"  To:   {local_tmpdir}")
                    try:
                        shutil.copytree(tmpdir, local_tmpdir, symlinks=True)
                        print(f"Test directory copied to: {local_tmpdir}")
                    except Exception as e:
                        print(f"Failed to copy directory: {e}")
                    print(f"{separator}\n")

                print(f"\n{separator}")
                print(f"Test directory preserved at: {tmpdir}")
                print(f"{separator}\n")
            else:
                # Clean up on success
                shutil.rmtree(tmpdir, ignore_errors=True)
                print(f"\n{separator}")
                print("All tests passed - cleaned up test directory")
                print(f"{separator}\n")


@pytest.fixture(scope="session")
def common_structure():
    """Load the common silicon structure used across tests."""
    return Structure.from_file(data.structure_Si)


# ==================== QE Fixtures ====================


@pytest.fixture(scope="session")
def qe_common_kwargs(common_structure):
    """Common kwargs for QE tasks."""
    return {
        "structure": common_structure,
        "prefix": "Si",
        "pseudo_dir": data.pseudo_dir,
        "pseudos": data.pseudos_Si_upf,
        "ngkpt": [2, 2, 2],
        "kshift": [0.5, 0.5, 0.5],
        "ecutwfc": 8.0,
        "nbnd": 9,
        "ecuteps": 8.0,  # Must be <= ecutwfc
        "ibnd_min": 1,
        "ibnd_max": 8,
        "nbnd_val": 4,
        "nbnd_cond": 4,
        "nbnd_val_co": 4,
        "nbnd_cond_co": 4,
        "nbnd_val_fi": 4,
        "nbnd_cond_fi": 4,
    }


@pytest.fixture(scope="session")
def qe_scftask(session_tmpdir, qe_common_kwargs):
    """Run QE SCF calculation once per session."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(nproc=NPROC_QE)
    task = QeScfTask(
        dirname=str(Path(session_tmpdir) / "QE_SCF"),
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_wfntask_ksh(session_tmpdir, qe_scftask, qe_common_kwargs):
    """Run QE wavefunction calculation with kshift=[0.5,0.5,0.5]."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=str(Path(session_tmpdir) / "QE_Wfn_ksh"),
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.0, 0.0, 0.0],
        charge_density_fname=qe_scftask.charge_density_fname,
        data_file_fname=qe_scftask.data_file_fname,
        nproc=NPROC_QE,
    )
    task = QeWfnTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_pw2bgwtask_ksh(session_tmpdir, qe_wfntask_ksh, qe_common_kwargs):
    """Run pw2bgw conversion for ksh wavefunction."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=qe_wfntask_ksh.dirname,
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.0, 0.0, 0.0],
        wfn_fname="wfn.cplx",
        rho_fname="rho.real",
        vxc_fname="vxc.dat",
        wfng_flag=True,
        rhog_flag=True,
        vxcg_flag=True,
        nproc=NPROC_QE,  # pw2bgw can crash if given too many processes
    )
    task = Qe2BgwTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_wfntask_qsh(session_tmpdir, qe_scftask, qe_common_kwargs):
    """Run QE wavefunction calculation with qshift=[0.001,0,0]."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=str(Path(session_tmpdir) / "QE_Wfn_qsh"),
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        charge_density_fname=qe_scftask.charge_density_fname,
        data_file_fname=qe_scftask.data_file_fname,
        nproc=NPROC_QE,
    )
    task = QeWfnTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_pw2bgwtask_qsh(session_tmpdir, qe_wfntask_qsh, qe_common_kwargs):
    """Run pw2bgw conversion for qsh wavefunction."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=qe_wfntask_qsh.dirname,
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        wfn_fname="wfnq.cplx",
        wfng_flag=True,
        nproc=NPROC_QE,
    )
    task = Qe2BgwTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_wfntask_ush(session_tmpdir, qe_scftask, qe_common_kwargs):
    """Run QE wavefunction calculation with unshifted grid."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=str(Path(session_tmpdir) / "QE_wfn_co"),
        kshift=[0.0, 0.0, 0.0],
        qshift=[0.0, 0.0, 0.0],
        charge_density_fname=qe_scftask.charge_density_fname,
        data_file_fname=qe_scftask.data_file_fname,
        nproc=NPROC_QE,
    )
    task = QeWfnTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_pw2bgwtask_ush(session_tmpdir, qe_wfntask_ush, qe_common_kwargs):
    """Run pw2bgw conversion for unshifted wavefunction."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=qe_wfntask_ush.dirname,
        kshift=[0.0, 0.0, 0.0],
        qshift=[0.0, 0.0, 0.0],
        wfn_fname="wfn_co.cplx",
        rho_fname="rho.real",
        vxc_fname="vxc.dat",
        wfng_flag=True,
        rhog_flag=True,
        vxcg_flag=True,
        vxc_diag_nmax=8,
        nproc=NPROC_QE,
    )
    task = Qe2BgwTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_wfntask_fi(session_tmpdir, qe_scftask, qe_common_kwargs):
    """Run QE wavefunction calculation for fine grid."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=str(Path(session_tmpdir) / "QE_Wfn_fi"),
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.0, 0.0, 0.0],
        symkpt=False,
        charge_density_fname=qe_scftask.charge_density_fname,
        data_file_fname=qe_scftask.data_file_fname,
        nproc=NPROC_QE,
    )
    task = QeWfnTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_pw2bgwtask_fi(session_tmpdir, qe_wfntask_fi, qe_common_kwargs):
    """Run pw2bgw conversion for fine grid wavefunction."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=qe_wfntask_fi.dirname,
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.0, 0.0, 0.0],
        wfn_fname="wfn_fi.cplx",
        wfng_flag=True,
        nproc=NPROC_QE,
    )
    task = Qe2BgwTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_wfntask_fiq(session_tmpdir, qe_scftask, qe_common_kwargs):
    """Run QE wavefunction calculation for fine q-shifted grid."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=str(Path(session_tmpdir) / "QE_Wfnq_fi"),
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        symkpt=False,
        charge_density_fname=qe_scftask.charge_density_fname,
        data_file_fname=qe_scftask.data_file_fname,
        nproc=NPROC_QE,
    )
    task = QeWfnTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def qe_pw2bgwtask_fiq(session_tmpdir, qe_wfntask_fiq, qe_common_kwargs):
    """Run pw2bgw conversion for fine q-shifted wavefunction."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dirname=qe_wfntask_fiq.dirname,
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        wfn_fname="wfn_fi.cplx",
        wfng_flag=True,
        nproc=NPROC_QE,
    )
    task = Qe2BgwTask(**kwargs)
    task.write()
    task.run()
    task.report()
    return task


# ==================== BGW Task Fixtures ====================


@pytest.fixture(scope="session")
def bgw_epsilontask(session_tmpdir, qe_pw2bgwtask_ksh, qe_pw2bgwtask_qsh, qe_common_kwargs):
    """Run BGW Epsilon calculation once per session."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(qshift=[0.001, 0.0, 0.0], nproc=NPROC_BGW_QPOINT)

    task = EpsilonTask(
        dirname=str(Path(session_tmpdir) / "BGW_Epsilon"),
        wfn_fname=qe_pw2bgwtask_ksh.wfn_fname,
        wfnq_fname=qe_pw2bgwtask_qsh.wfn_fname,
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def bgw_sigmatask(session_tmpdir, qe_pw2bgwtask_ush, bgw_epsilontask, qe_common_kwargs):
    """Run BGW Sigma calculation once per session."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(extra_lines=["screening_semiconductor"], nproc=NPROC_BGW_GENERAL)

    task = SigmaTask(
        dirname=str(Path(session_tmpdir) / "BGW_Sigma"),
        wfn_co_fname=qe_pw2bgwtask_ush.wfn_fname,
        rho_fname=qe_pw2bgwtask_ush.rho_fname,
        vxc_dat_fname=qe_pw2bgwtask_ush.vxc_dat_fname,
        eps0mat_fname=bgw_epsilontask.eps0mat_fname,
        epsmat_fname=bgw_epsilontask.epsmat_fname,
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def bgw_sigmatask_hf(session_tmpdir, qe_pw2bgwtask_ush, qe_common_kwargs):
    """Run BGW Hartree-Fock Sigma calculation once per session."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        extra_lines=["screening_semiconductor"],
        extra_variables={"frequency_dependence": -1},
        ngqpt=kwargs["ngkpt"],
        nproc=NPROC_BGW_GENERAL,
    )

    task = SigmaTask(
        dirname=str(Path(session_tmpdir) / "BGW_Sigma_HF"),
        wfn_co_fname=qe_pw2bgwtask_ush.wfn_fname,
        rho_fname=qe_pw2bgwtask_ush.rho_fname,
        vxc_dat_fname=qe_pw2bgwtask_ush.vxc_dat_fname,
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def bgw_kerneltask(session_tmpdir, qe_pw2bgwtask_ush, bgw_epsilontask, qe_common_kwargs):
    """Run BGW Kernel calculation once per session."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        extra_lines=["screening_semiconductor", "use_symmetries_coarse_grid"],
        nproc=NPROC_BGW_QPOINT,
    )

    task = KernelTask(
        dirname=str(Path(session_tmpdir) / "BGW_Kernel"),
        wfn_co_fname=qe_pw2bgwtask_ush.wfn_fname,
        eps0mat_fname=bgw_epsilontask.eps0mat_fname,
        epsmat_fname=bgw_epsilontask.epsmat_fname,
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def bgw_absorptiontask(
    session_tmpdir,
    qe_pw2bgwtask_ush,
    qe_pw2bgwtask_fi,
    qe_pw2bgwtask_fiq,
    bgw_epsilontask,
    bgw_sigmatask,
    bgw_kerneltask,
    qe_common_kwargs,
):
    """Run BGW Absorption calculation once per session."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        extra_lines=[
            "use_symmetries_coarse_grid",
            "no_symmetries_fine_grid",
            "no_symmetries_shifted_grid",
            "screening_semiconductor",
            "use_velocity",
            "gaussian_broadening",
            "eqp_co_corrections",
        ],
        extra_variables={
            "energy_resolution": 0.15,
        },
        nproc=NPROC_BGW_GENERAL,
    )

    if AbsorptionTask._use_hdf5:
        kwargs["bsemat_fname"] = bgw_kerneltask.bsemat_fname
    else:
        kwargs["bsedmat_fname"] = bgw_kerneltask.bsedmat_fname
        kwargs["bsexmat_fname"] = bgw_kerneltask.bsexmat_fname

    task = AbsorptionTask(
        dirname=str(Path(session_tmpdir) / "BGW_Absorption"),
        wfn_co_fname=qe_pw2bgwtask_ush.wfn_fname,
        eps0mat_fname=bgw_epsilontask.eps0mat_fname,
        epsmat_fname=bgw_epsilontask.epsmat_fname,
        wfn_fi_fname=qe_pw2bgwtask_fi.wfn_fname,
        wfnq_fi_fname=qe_pw2bgwtask_fiq.wfn_fname,
        sigma_fname=bgw_sigmatask.sigma_fname,
        eqp_fname=bgw_sigmatask.eqp1_fname,
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


# ==================== Flow Fixtures ====================


@pytest.fixture(scope="session")
def bgw_gwflow(session_tmpdir, qe_common_kwargs):
    """Run GW workflow (Flow) once per session."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dft_flavor="espresso",
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        sigma_extra_lines=["screening_semiconductor"],
        nproc=NPROC_QE,
    )

    flow = GWFlow(
        dirname=str(Path(session_tmpdir) / "GW_Flow"),
        **kwargs,
    )
    flow.write()
    flow.run()
    flow.report()
    return flow


@pytest.fixture(scope="session")
def bgw_bseflow(session_tmpdir, qe_common_kwargs):
    """Run BSE workflow (Flow) once per session."""
    kwargs = qe_common_kwargs.copy()
    kwargs.update(
        dft_flavor="espresso",
        nbnd_fine=9,
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        sigma_extra_lines=["screening_semiconductor"],
        nproc=NPROC_QE,
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

    flow = BSEFlow(
        dirname=str(Path(session_tmpdir) / "BSE_Flow"),
        **kwargs,
    )
    flow.write()
    flow.run()
    flow.report()
    return flow


# ==================== Abinit Fixtures ====================


@pytest.fixture(scope="session")
def abinit_common_kwargs(common_structure):
    """Common kwargs for Abinit tasks."""
    return {
        "structure": common_structure,
        "prefix": "Si",
        "pseudo_dir": data.pseudo_dir,
        "pseudos": data.pseudos_Si,
        "ngkpt": [2, 2, 2],
        "kshift": [0.5, 0.5, 0.5],
        "ecut": 10.0,
        "nband": 9,
        "ecuteps": 10.0,
        "with_density": True,
    }


@pytest.fixture(scope="session")
def abinit_scftask(session_tmpdir, abinit_common_kwargs):
    """Run Abinit SCF calculation once per session."""
    kwargs = abinit_common_kwargs.copy()
    kwargs.update(nproc=NPROC_ABINIT)  # Limit processes for small calculation
    task = AbinitScfTask(
        dirname=str(Path(session_tmpdir) / "Abinit_SCF"),
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def abinit_wfntask(session_tmpdir, abinit_scftask, abinit_common_kwargs):
    """Run Abinit wavefunction calculation once per session."""
    kwargs = abinit_common_kwargs.copy()
    kwargs.update(
        charge_density_fname=abinit_scftask.charge_density_fname,
        nproc=NPROC_ABINIT,  # Limit processes for small calculation
    )

    task = AbinitWfnTask(
        dirname=str(Path(session_tmpdir) / "Abinit_Wfn"),
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def abinit_abi2bgwtask(session_tmpdir, abinit_scftask, abinit_wfntask, abinit_common_kwargs):
    """Run Abinit to BGW conversion once per session."""
    kwargs = abinit_common_kwargs.copy()
    kwargs.update(
        wfng_flag=True,
        rhog_flag=True,
        vxcg_flag=True,
        wfn_fname=abinit_wfntask.wfn_fname,
        rho_fname=abinit_scftask.rho_fname,
        vxc_fname=abinit_scftask.vxc_fname,
        nproc=NPROC_ABINIT,  # Limit processes for small calculation
    )

    task = Abi2BgwTask(
        dirname=abinit_wfntask.dirname,
        **kwargs,
    )
    task.write()
    task.run()
    task.report()
    return task


@pytest.fixture(scope="session")
def abinit_bgwflow(session_tmpdir, abinit_scftask, abinit_common_kwargs):
    """Run Abinit BGW flow once per session."""
    kwargs = abinit_common_kwargs.copy()
    kwargs.update(
        charge_density_fname=abinit_scftask.charge_density_fname,
        nproc=NPROC_ABINIT,  # Limit processes for small calculation
    )

    flow = AbinitBgwFlow(
        dirname=str(Path(session_tmpdir) / "Abinit_BGW_Flow"),
        **kwargs,
    )
    flow.write()
    flow.run()
    flow.report()
    return flow
