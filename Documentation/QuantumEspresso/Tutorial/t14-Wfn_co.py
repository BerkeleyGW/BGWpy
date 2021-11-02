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
from BGWpy import Structure, QeBgwFlow

task = QeBgwFlow(
    dirname = '14-Wfn_co',

    structure = Structure.from_file('../../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../../Data/Pseudos',
    pseudos = ['31-Ga.PBE.UPF', '33-As.PBE.UPF'],

    ngkpt = [2,2,2],      # k-points grid
    kshift = [.0,.0,.0],  # k-points shift
    ecutwfc = 10.0,       # Wavefunctions cutoff energy
    nbnd = 9,             # Number of bands

    rhog_flag = True,     # Also convert the charge density and vxc for BGW.

    charge_density_fname = '11-Density/GaAs.save/charge-density.dat',
    data_file_fname = '11-Density/GaAs.save/data-file.xml',

    # These are the default parameters for the MPI runner.
    # Please adapt them to your needs.
    nproc = 1,
    nproc_per_node = 1,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )

# Execution
task.write()
task.run()
task.report()

