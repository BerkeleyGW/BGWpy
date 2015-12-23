"""
Compute DFT wavefunctions and eigenvalues
on a k-shifted and q-shifted k-point grid,
then adapt them for BGW.

Depends on:
    11-Density

Used by:
    21-Epsilon
"""
from BGWpy import Structure, QeWfnTask, Qe2BgwTask

# Common arguments for tasks.
kwargs = dict(
    dirname = '13-Wfnq',

    structure = Structure.from_file('../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../Data/Pseudos',
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

# Wavefunctions and eigenvalues calculation (NSCF) on a k-shifted grid
wfntask_qsh = QeWfnTask(
    charge_density_fname = '11-Density/GaAs.save/charge-density.dat',
    data_file_fname = '11-Density/GaAs.save/data-file.xml',
    **kwargs)


# Interfacing PW with BerkeleyGW.
pw2bgwtask_qsh = Qe2BgwTask(
    wfn_fname = 'wfnq.cplx',
    **kwargs)


# Execution
for task in (wfntask_qsh, pw2bgwtask_qsh):
    task.write()
    task.run()
    task.report()

