"""
Compute DFT wavefunctions and eigenvalues
on a k-shifted and q-shifted k-point grid,
then adapt them for BGW.

Depends on:
    11-Density

Used by:
    21-Epsilon
"""

from BGWpy import QeBgwFlow, Structure


def run_t13_wfnq(**kwargs):
    """Run the Wfnq calculation task.

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
        dirname="13-Wfnq",
        structure=Structure.from_file("../../Data/Structures/GaAs.json"),
        prefix="GaAs",
        pseudo_dir="../../Data/Pseudos",
        pseudos=["31-Ga.PBE.UPF", "33-As.PBE.UPF"],
        ngkpt=kwargs["ngkpt"],
        kshift=[0.5, 0.5, 0.5],
        qshift=[0.001, 0.0, 0.0],
        ecutwfc=kwargs["ecutwfc"],
        # Number of bands not specified (occupied only)
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
    run_t13_wfnq(
        ngkpt=[2, 2, 2],
        ecutwfc=10.0,
        use_hdf5_qe=True,
        nproc=1,
        nproc_per_node=1,
        mpirun="mpirun",
        nproc_flag="-n",
        nproc_per_node_flag="--npernode",
    )
