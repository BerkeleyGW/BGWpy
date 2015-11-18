"""
Compute the BSE kernel.

Depends on:
    14-Wfn_co
    21-Epsilon

Used by:
    24-Absorption
"""
from BGWpy import Structure, KernelTask

task = KernelTask(
    dirname='23-Kernel',
    structure = Structure.from_file('Data/GaAs.json'),

    ngkpt = [2,2,2],        # k-points grid
    nbnd_val = 4,           # Number of valence bands
    nbnd_cond = 4,          # Number of conduction bands
    ecuteps = 10.0,         # Energy cutoff for the epsilon matrix

    # These extra lines will be added verbatim to the input file.
    extra_lines = [
        'use_symmetries_coarse_grid',
        'screening_semiconductor',
        ],

    # Files to be linked
    wfn_co_fname='14-Wfn_co/wfn_co.cplx',
    eps0mat_fname='21-Epsilon/eps0mat',  # Change to 21-Epsilon/eps0mat.h5 if BGW is compiled with HDF5
    epsmat_fname='21-Epsilon/epsmat',  # Change to 21-Epsilon/epsmat.h5 if BGW is compiled with HDF5

    # Parameters for the MPI runner
    nproc = 2,
    nproc_per_node = 2,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )


# Execution
task.write()
task.run()
task.report()

