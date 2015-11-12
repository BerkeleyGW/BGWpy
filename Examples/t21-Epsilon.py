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
from BGWpy import Structure, EpsilonTask

task = EpsilonTask(
    dirname='21-Epsilon',
    structure = Structure.from_file('Data/GaAs.json'),

    ngkpt = [2,2,2],        # k-points grid
    qshift = [.001,.0,.0],  # q-shift to treat the Gamma point
    nbnd_occ = 4,           # Number of occupied bands
    nbnd = 8,               # Number of bands
    ecuteps = 10.0,         # Energy cutoff for the epsilon matrix

    # Files to be linked
    wfn_fname='12-Wfn/wfn.cplx',
    wfnq_fname='13-Wfnq/wfnq.cplx',

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

