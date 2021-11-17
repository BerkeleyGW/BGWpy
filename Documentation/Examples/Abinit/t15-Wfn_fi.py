"""
Compute DFT wavefunctions and eigenvalues
on a 'fine' k-shifted k-point grid,
then adapt them for BGW.

Depends on:
    11-Density

Used by:
    24-Absorption
"""
from BGWpy import Structure, AbinitBgwFlow

task = AbinitBgwFlow(
    dirname = '15-Wfn_fi',

    structure = Structure.from_file('../../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../../Data/Pseudos',
    pseudos = ['31-Ga.pspnc', '33-As.pspnc'],

    ngkpt = [2,2,2],      # k-points grid
    kshift = [.5,.5,.5],  # k-points shift
    ecut = 5.0,           # Wavefunctions cutoff energy
    nband = 9,            # Number of bands
    symkpt = False,       # Do not reduce the k-point grid with symmetries.

    charge_density_fname = '11-Density/out_data/odat_DEN',

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

