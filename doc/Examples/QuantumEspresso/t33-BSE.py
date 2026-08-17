"""
Perform a complete BSE calculation including
the DFT wavefunctions, the inverse dielectric matrix, the self-energy,
the kernel, and the absorption spectrum.
"""

from BGWpy import BSEFlow, Structure


def run_t33_bse(**kwargs):
    """Run the complete BSE flow.

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
    flow = BSEFlow(
        dirname="33-BSE",
        dft_flavor="espresso",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        prefix="GaAs",
        pseudo_dir="../../Data/Pseudos",
        pseudos=["31-Ga.PBE.UPF", "33-As.PBE.UPF"],
        ecutwfc=kwargs["ecutwfc"],
        nbnd=12,
        nbnd_fine=9,
        ngkpt=kwargs["ngkpt"],
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        # Fine grids
        ngkpt_fine=[4, 4, 4],
        kshift_fine=[0.0, 0.0, 0.0],
        ibnd_min=1,
        ibnd_max=8,
        ecuteps=kwargs["ecuteps"],
        sigma_extra_lines=["screening_semiconductor"],
        # Kernel variables
        nbnd_val=4,
        nbnd_cond=4,
        kernel_extra_lines=[
            "use_symmetries_coarse_grid",
            "screening_semiconductor",
        ],
        # Absorption variables
        nbnd_val_co=4,
        nbnd_cond_co=4,
        nbnd_val_fi=4,
        nbnd_cond_fi=4,
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
    run_t33_bse(
        ngkpt=[2, 2, 2],
        ecutwfc=10.0,
        ecuteps=10.0,
        nproc=2,
        nproc_per_node=2,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
