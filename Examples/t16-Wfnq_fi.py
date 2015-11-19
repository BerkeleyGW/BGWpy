"""
Compute DFT wavefunctions and eigenvalues
on a 'fine' k-shifted and q-shifted k-point grid,
then adapt them for BGW.

Depends on:
    11-Density

Used by:
    24-Absorption
"""
from BGWpy import Structure, WfnTask, PW2BGWTask

# Common arguments for tasks.
kwargs = dict(
    dirname = '16-Wfnq_fi',

    structure = Structure.from_file('Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = 'Pseudos',
    pseudos = ['31-Ga.PBE.UPF', '33-As.PBE.UPF'],

    ngkpt = [2,2,2],      # k-points grid
    kshift = [.5,.5,.5],  # k-points shift
    qshift = [.001,.0,.0],# k-points q-shift
    ecutwfc = 10.0,       # Wavefunctions cutoff energy
    nbnd = 9,             # Number of bands
    symkpt = False,       # Do not reduce the k-point grid with symmetries.

    # These are the default parameters for the MPI runner.
    # Please adapt them to your needs.
    nproc = 1,
    nproc_per_node = 1,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )


# Wavefunctions and eigenvalues calculation (NSCF) on a k-shifted grid
wfntask_fiq = WfnTask(
    charge_density_fname = '11-Density/GaAs.save/charge-density.dat',
    data_file_fname = '11-Density/GaAs.save/data-file.xml',
    **kwargs)


# Interfacing PW with BerkeleyGW.
pw2bgwtask_fiq = PW2BGWTask(
    wfn_fname = 'wfnq_fi.cplx',
    **kwargs)


# Execution
for task in (wfntask_fiq, pw2bgwtask_fiq):
    task.write()
    task.run()
    task.report()

