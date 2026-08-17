"""
Compute ground state charge density.

Used by:
    12-Wfn
    13-Wfnq
    14-Wfn_co
    15-Wfn_fi
    16-Wfnq_fi
"""

from BGWpy import QeScfTask, Structure


def run_t11_density(**kwargs):
    """Run the density calculation task.

    Parameters from kwargs:
        ngkpt: k-points grid
        ecutwfc: Wavefunction cutoff energy
        nproc: Number of MPI processes
        nproc_per_node: Number of MPI processes per node
        mpirun: MPI run command
        nproc_flag: Flag for number of processes
        nproc_per_node_flag: Flag for processes per node
    """
    task = QeScfTask(
        dirname="11-Density",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        prefix="GaAs",
        pseudo_dir="../../Data/Pseudos",
        pseudos=["31-Ga.PBE.UPF", "33-As.PBE.UPF"],
        ngkpt=kwargs["ngkpt"],
        kshift=[0.5, 0.5, 0.5],
        ecutwfc=kwargs["ecutwfc"],
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
    run_t11_density(
        ngkpt=[2, 2, 2],
        ecutwfc=10.0,
        nproc=1,
        nproc_per_node=1,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
