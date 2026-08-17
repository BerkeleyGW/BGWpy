"""
Compute DFT wavefunctions and eigenvalues
on a 'fine' k-shifted and q-shifted k-point grid,
then adapt them for BGW.

Depends on:
    11-Density

Used by:
    24-Absorption
"""

from BGWpy import QeBgwFlow, Structure


def run_t16_wfnq_fi(**kwargs):
    """Run the Wfnq_fi calculation task.

    Parameters from kwargs:
        ngkpt: k-points grid
        ecutwfc: Wavefunction cutoff energy
        use_hdf5_qe: Whether to use HDF5 format for QE files
        nproc: Number of MPI processes
        nproc_per_node: Number of MPI processes per node
        mpirun: MPI run command
        nproc_flag: Flag for number of processes
        nproc_per_node_flag: Flag for processes per node
    """
    charge_density_ext = "hdf5" if kwargs.get("use_hdf5_qe", True) else "dat"
    task = QeBgwFlow(
        dirname="16-Wfnq_fi",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        prefix="GaAs",
        pseudo_dir="../../Data/Pseudos",
        pseudos=["31-Ga.PBE.UPF", "33-As.PBE.UPF"],
        ngkpt=kwargs["ngkpt"],
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        ecutwfc=kwargs["ecutwfc"],
        nbnd=9,
        symkpt=False,  # Do not reduce the k-point grid with symmetries.
        charge_density_fname=f"11-Density/GaAs.save/charge-density.{charge_density_ext}",
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
    run_t16_wfnq_fi(
        ngkpt=[2, 2, 2],
        ecutwfc=10.0,
        use_hdf5_qe=True,
        nproc=1,
        nproc_per_node=1,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
