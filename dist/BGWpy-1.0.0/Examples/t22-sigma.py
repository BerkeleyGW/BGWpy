"""
Compute the GW self-energy.

Depends on:
    14-Wfn_co
    21-Epsilon

Used by:
    22-Sigma
    23-Kernel
    24-Absorption
"""
from BGWpy import Structure, SigmaTask

task = SigmaTask(
    dirname='22-Sigma',
    structure = Structure.from_file('Data/GaAs.json'),

    ngkpt = [2,2,2],        # k-points grid
    nbnd_occ = 4,           # Number of occupied bands
    nbnd = 8,               # Number of bands
    ibnd_min = 1,           # Minimum band for GW corrections
    ibnd_max = 8,           # Maximum band for GW corrections
    ecuteps = 10.0,         # Energy cutoff for the epsilon matrix
    ecutsigx = 15.0,        # Energy cutoff for the bare exchange

    # Files to be linked
    wfn_co_fname='14-Wfn_co/wfn_co.cplx',
    rho_fname='14-Wfn_co/rho.real',
    vxc_fname='14-Wfn_co/vxc.dat',
    eps0mat_fname='21-Epsilon/eps0mat',
    epsmat_fname='21-Epsilon/epsmat',

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

