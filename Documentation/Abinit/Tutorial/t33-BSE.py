"""
Perform a complete BSE calculation including
the DFT wavefunctions, the inverse dielectric matrix, the self-energy,
the kernel, and the absorption spectrum.
"""
from BGWpy import Structure, BSEFlow

flow = BSEFlow(
    dirname='33-BSE',
    dft_flavor='abinit',

    structure = Structure.from_file('../../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../../Data/Pseudos',
    pseudos = ['31-Ga.pspnc', '33-As.pspnc'],

    ecut = 5.0,
    nbnd = 12,
    nbnd_fine = 9,

    ngkpt = [2,2,2],
    kshift = [.5,.5,.5],
    qshift = [.001,.0,.0],

    # Fine grids
    ngkpt_fine = [4,4,4],
    kshift_fine = [.0,.0,.0],

    ibnd_min = 1,
    ibnd_max = 8,
    ecuteps = 10.0,
    sigma_extra_lines = ['screening_semiconductor'],

    # Kernel variables
    nbnd_val = 4,
    nbnd_cond = 4,

    kernel_extra_lines = [
        'use_symmetries_coarse_grid',
        'screening_semiconductor',
        ],

    # Absorption variables
    nbnd_val_co=4,
    nbnd_cond_co=4,
    nbnd_val_fi=4,
    nbnd_cond_fi=4,
    
    absorption_extra_lines = [
        'use_symmetries_coarse_grid',
        'no_symmetries_fine_grid',
        'no_symmetries_shifted_grid',
        'screening_semiconductor',
        'use_velocity',
        'gaussian_broadening',
        'eqp_co_corrections',
        ],
    
    absorption_extra_variables = {
        'energy_resolution' : 0.15,
        },


    # Parameters for the MPI runner
    nproc = 2,
    nproc_per_node = 2,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )


# Execution
flow.write()
flow.run()
flow.report()
