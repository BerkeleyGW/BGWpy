"""
Perform a complete GW calculation including
the DFT wavefunctions, the inverse dielectric matrix, and the self-energy.
"""
from BGWpy import Structure, GWFlow

flow = GWFlow(
    dirname='32-GW',
    dft_flavor='abinit',

    structure = Structure.from_file('../../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../../Data/Pseudos',
    pseudos = ['31-Ga.pspnc', '33-As.pspnc'],

    ecut = 5.0,
    nbnd = 9,

    ngkpt = [2,2,2],
    kshift = [.5,.5,.5],
    qshift = [.001,.0,.0],
    ibnd_min = 1,
    ibnd_max = 8,
    ecuteps = 10.0,

    # Extra lines and extra variables
    epsilon_extra_lines = [],
    epsilon_extra_variables = {},
    sigma_extra_lines = ['screening_semiconductor'],
    sigma_extra_variables = {},

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
