"""
Compute DFT density and wavefunctions 
on a q-shifted k-point grid,
then adapt them for BGW.

"""
from BGWpy import Structure, QeScfTask, QeWfnTask, Qe2BgwTask

# Common arguments for tasks.
common = dict(

    structure = Structure.from_file('../../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../../Data/Pseudos',
    pseudos = ['31-Ga.PBE.UPF', '33-As.PBE.UPF'],

    ngkpt = [2,2,2],      # k-points grid
    kshift = [.5,.5,.5],  # k-points shift
    qshift = [.001,.0,.0],# k-points q-shift
    ecutwfc = 10.0,       # Wavefunctions cutoff energy
                          # Number of bands not specified (occupied only)


    # These are the default parameters for the MPI runner.
    # Please adapt them to your needs.
    nproc = 1,
    nproc_per_node = 1,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )

scftask = QeScfTask(
    dirname = '01-Wavefunctions/Density',
    **common)

# Wavefunctions and eigenvalues calculation (NSCF) on a k-shifted grid
wfntask = QeWfnTask(
    dirname = '01-Wavefunctions/Wavefunctions',
    charge_density_fname = scftask.charge_density_fname,
    data_file_fname = scftask.data_file_fname,
    **common)

# Interfacing PW with BerkeleyGW.
qe2bgwtask = Qe2BgwTask(
    dirname = wfntask.dirname,
    **common)

# Execution
for task in (scftask, wfntask, qe2bgwtask):
    task.write()
    task.run()
    task.report()

