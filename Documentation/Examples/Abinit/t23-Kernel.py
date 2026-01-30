"""
Compute the BSE kernel.

Depends on:
    14-Wfn_co
    21-Epsilon

Used by:
    24-Absorption
"""

from BGWpy import KernelTask, Structure


def run_t23_kernel(**kwargs):
    """Run the Kernel calculation task.

    Parameters from kwargs:
        ngkpt: k-points grid
        ecuteps: Energy cutoff for epsilon matrix
        nproc: Number of MPI processes
        nproc_per_node: Number of MPI processes per node
        mpirun: MPI run command
        nproc_flag: Flag for number of processes
        nproc_per_node_flag: Flag for processes per node
    """
    task = KernelTask(
        dirname="23-Kernel",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        ngkpt=kwargs["ngkpt"],
        nbnd_val=4,
        nbnd_cond=4,
        ecuteps=kwargs["ecuteps"],
        # These extra lines will be added verbatim to the input file.
        extra_lines=[
            "use_symmetries_coarse_grid",
            "screening_semiconductor",
        ],
        # Files to be linked
        wfn_co_fname="14-Wfn_co/wfn.cplx",
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
    run_t23_kernel(
        ngkpt=[2, 2, 2],
        ecuteps=5.0,
        nproc=2,
        nproc_per_node=2,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
