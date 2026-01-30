"""
Compute DFT wavefunctions and eigenvalues
on an unshifted k-point grid,
then adapt them for BGW.

Depends on:
    11-Density

Used by:
    22-Sigma
    23-Kernel
    24-Absorption
"""

from BGWpy import QeBgwFlow, Structure


def run_t14_wfn_co(**kwargs):
    """Run the Wfn_co calculation task.

    Parameters from kwargs:
        ngkpt: k-points grid
        ecutwfc: Wavefunction cutoff energy
        nproc: Number of MPI processes
        nproc_per_node: Number of MPI processes per node
        mpirun: MPI run command
        nproc_flag: Flag for number of processes
        nproc_per_node_flag: Flag for processes per node
    """
    task = QeBgwFlow(
        dirname="14-Wfn_co",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        prefix="GaAs",
        pseudo_dir="../../Data/Pseudos",
        pseudos=["31-Ga.PBE.UPF", "33-As.PBE.UPF"],
        ngkpt=kwargs["ngkpt"],
        kshift=[0.0, 0.0, 0.0],  # k-points shift
        ecutwfc=kwargs["ecutwfc"],
        nbnd=9,
        rhog_flag=True,  # Also convert the charge density and vxc for BGW.
        charge_density_fname="11-Density/GaAs.save/charge-density.hdf5",
        data_file_fname="11-Density/GaAs.save/data-file-schema.xml",
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
    run_t14_wfn_co(
        ngkpt=[2, 2, 2],
        ecutwfc=10.0,
        nproc=1,
        nproc_per_node=1,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
