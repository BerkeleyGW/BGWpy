"""
Compute the GW self-energy.

Depends on:
    14-Wfn_co
    21-Epsilon

Used by:
    23-Kernel
    24-Absorption
"""

from BGWpy import SigmaTask, Structure


def run_t22_sigma(**kwargs):
    """Run the Sigma calculation task.

    Parameters from kwargs:
        ngkpt: k-points grid
        nproc: Number of MPI processes
        nproc_per_node: Number of MPI processes per node
        mpirun: MPI run command
        nproc_flag: Flag for number of processes
        nproc_per_node_flag: Flag for processes per node
    """
    task = SigmaTask(
        dirname="22-Sigma",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        ngkpt=kwargs["ngkpt"],
        ibnd_min=1,
        ibnd_max=8,
        # Files to be linked
        wfn_co_fname="14-Wfn_co/wfn.cplx",
        rho_fname="14-Wfn_co/rho.real",
        vxc_dat_fname="14-Wfn_co/vxc.dat",
        eps0mat_fname="21-Epsilon/eps0mat.h5",  # With hdf5
        epsmat_fname="21-Epsilon/epsmat.h5",  # With hdf5
        # eps0mat_fname='21-Epsilon/eps0mat',   # Without hdf5
        # epsmat_fname='21-Epsilon/epsmat',     # Without hdf5
        # Parameters for the MPI runner
        nproc=kwargs["nproc"],
        nproc_per_node=kwargs["nproc_per_node"],
        mpirun=kwargs["mpirun"],
        nproc_flag=kwargs["nproc_flag"],
        nproc_per_node_flag=kwargs["nproc_per_node_flag"],
    )

    # Execution
    task.write()
    task.run()
    task.report()


if __name__ == "__main__":
    # Default parameters for standalone execution
    run_t22_sigma(
        ngkpt=[2, 2, 2],
        nproc=2,
        nproc_per_node=2,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
