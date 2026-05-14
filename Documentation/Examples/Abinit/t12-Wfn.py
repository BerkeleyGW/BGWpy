"""
Compute DFT wavefunctions and eigenvalues
on a k-shifted k-point grid,
then adapt them for BGW.

Depends on:
    11-Density

Used by:
    21-Epsilon
"""

from BGWpy import AbinitBgwFlow, Structure


def run_t12_wfn(**kwargs):
    """Run the Wfn calculation task.

    Parameters from kwargs:
        ngkpt: k-points grid
        ecut: Wavefunction cutoff energy
        nproc: Number of MPI processes
        nproc_per_node: Number of MPI processes per node
        mpirun: MPI run command
        nproc_flag: Flag for number of processes
        nproc_per_node_flag: Flag for processes per node
    """
    task = AbinitBgwFlow(
        dirname="12-Wfn",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        prefix="GaAs",
        pseudo_dir="../../Data/Pseudos",
        pseudos=["31-Ga.pspnc", "33-As.pspnc"],
        ngkpt=kwargs["ngkpt"],
        kshift=[0.5, 0.5, 0.5],
        ecut=kwargs["ecut"],
        nband=9,
        input_variables={"autoparal": 1},
        charge_density_fname="11-Density/out_data/o_DEN",
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
    run_t12_wfn(
        ngkpt=[2, 2, 2],
        ecut=5.0,
        nproc=1,
        nproc_per_node=1,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
