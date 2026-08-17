"""
Compute the dielectric matrix and its inverse.

Depends on:
    12-Wfn
    13-Wfnq

Used by:
    22-Sigma
    23-Kernel
    24-Absorption
"""

from BGWpy import EpsilonTask, Structure


def run_t21_epsilon(**kwargs):
    """Run the Epsilon calculation task.

    Parameters from kwargs:
        ngkpt: k-points grid
        ecuteps: Energy cutoff for epsilon matrix
        nproc: Number of MPI processes
        nproc_per_node: Number of MPI processes per node
        mpirun: MPI run command
        nproc_flag: Flag for number of processes
        nproc_per_node_flag: Flag for processes per node
    """
    task = EpsilonTask(
        dirname="21-Epsilon",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        ngkpt=kwargs["ngkpt"],
        qshift=[0.001, 0.0, 0.0],
        ecuteps=kwargs["ecuteps"],
        # Files to be linked
        wfn_fname="12-Wfn/wfn.cplx",
        wfnq_fname="13-Wfnq/wfn.cplx",
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
    run_t21_epsilon(
        ngkpt=[2, 2, 2],
        ecuteps=10.0,
        nproc=2,
        nproc_per_node=2,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
