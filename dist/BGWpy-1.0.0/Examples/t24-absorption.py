"""
Compute the absorption from the BSE.

Depends on:
    14-Wfn_co
    15-Wfn_fi
    16-Wfnq_fi
    21-Epsilon
    22-Sigma
    23-Kernel
"""
from BGWpy import Structure, AbsorptionTask

task = AbsorptionTask(
    dirname='24-Absorption',
    structure = Structure.from_file('Data/GaAs.cif'),

    ngkpt = [2,2,2],        # k-points grid
    nbnd_val = 4,           # Number of valence bands
    nbnd_cond = 4,          # Number of conduction bands

    nbnd_val_co=4,          # Number of valence bands on the coarse grid
    nbnd_cond_co=4,         # Number of conduction bands on the coarse grid
    nbnd_val_fi=4,          # Number of valence bands on the fine grid
    nbnd_cond_fi=4,         # Number of conduction bands on the fine grid

    # These extra lines will be added verbatim to the input file.
    extra_lines = [
        'use_symmetries_coarse_grid',
        'no_symmetries_fine_grid',
        'no_symmetries_shifted_grid',
        'screening_semiconductor',
        'use_velocity',
        'gaussian_broadening',
        'eqp_co_corrections',
        ],

    # These extra variables will be added to the input file as '{variable} {value}'.
    extra_variables = {
        'energy_resolution' : 0.15,
        },

    # Files to be linked
    wfn_co_fname='14-Wfn_co/wfn_co.cplx',
    wfn_fi_fname='15-Wfn_fi/wfn_fi.cplx',
    wfnq_fi_fname='16-Wfnq_fi/wfnq_fi.cplx',
    eps0mat_fname='21-Epsilon/eps0mat',
    epsmat_fname='21-Epsilon/epsmat',
    bsedmat_fname='23-Kernel/bsedmat',
    bsexmat_fname='23-Kernel/bsexmat',
    sigma_fname='22-Sigma/sigma_hp.log',

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

