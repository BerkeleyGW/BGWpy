"""
Perform a complete GW calculation including
the DFT wavefunctions, the inverse dielectric matrix, and the self-energy.
"""

from BGWpy import GWFlow, Structure


def run_t32_gw(**kwargs):
    """Run the complete GW flow.

    Parameters from kwargs:
        ngkpt: k-points grid
        ecutwfc: Wavefunction cutoff energy
        ecuteps: Energy cutoff for epsilon matrix
        nproc: Number of MPI processes
        nproc_per_node: Number of MPI processes per node
        mpirun: MPI run command
        nproc_flag: Flag for number of processes
        nproc_per_node_flag: Flag for processes per node
    """
    flow = GWFlow(
        dirname="32-GW",
        dft_flavor="espresso",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        prefix="GaAs",
        pseudo_dir="../../Data/Pseudos",
        pseudos=["31-Ga.PBE.UPF", "33-As.PBE.UPF"],
        ecutwfc=kwargs["ecutwfc"],
        nbnd=9,
        ngkpt=kwargs["ngkpt"],
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        ibnd_min=1,
        ibnd_max=8,
        ecuteps=kwargs["ecuteps"],
        # Extra lines and extra variables
        epsilon_extra_lines=[],
        epsilon_extra_variables={},
        sigma_extra_lines=["screening_semiconductor"],
        sigma_extra_variables={},
        # Parameters for the MPI runner
        nproc=kwargs["nproc"],
        nproc_per_node=kwargs["nproc_per_node"],
        mpirun=kwargs["mpirun"],
        nproc_flag=kwargs["nproc_flag"],
        nproc_per_node_flag=kwargs["nproc_per_node_flag"],
    )

    # Execution
    flow.write()
    flow.run()
    flow.report()


if __name__ == "__main__":
    # Default parameters for standalone execution
    run_t32_gw(
        ngkpt=[2, 2, 2],
        ecutwfc=10.0,
        ecuteps=10.0,
        nproc=2,
        nproc_per_node=2,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
