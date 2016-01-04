"""
Compute ground state charge density.

Used by:
    12-Wfn
    13-Wfnq
    14-Wfn_co
    15-Wfn_fi
    16-Wfnq_fi
"""
from BGWpy import Structure, QeScfTask

task = QeScfTask(
    dirname = '11-Density',

    structure = Structure.from_file('../../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../../Data/Pseudos',
    pseudos = ['31-Ga.PBE.UPF', '33-As.PBE.UPF'],

    ngkpt = [2,2,2],      # k-points grid
    kshift = [.5,.5,.5],  # k-points shift
    ecutwfc = 10.0,       # Wavefunctions cutoff energy

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
