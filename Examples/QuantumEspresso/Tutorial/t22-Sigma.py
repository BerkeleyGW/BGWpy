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
    structure = Structure.from_file('../../Data/Structures/GaAs.json'),

    ngkpt = [2,2,2],        # k-points grid
    ibnd_min = 1,           # Minimum band for GW corrections
    ibnd_max = 8,           # Maximum band for GW corrections

    # Files to be linked
    wfn_co_fname='14-Wfn_co/wfn.cplx',
    rho_fname='14-Wfn_co/rho.real',
    vxc_dat_fname='14-Wfn_co/vxc.dat',

    eps0mat_fname='21-Epsilon/eps0mat.h5', # With hdf5
    epsmat_fname='21-Epsilon/epsmat.h5',   # With hdf5
    #eps0mat_fname='21-Epsilon/eps0mat',   # Without hdf5
    #epsmat_fname='21-Epsilon/epsmat',     # Without hdf5

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

