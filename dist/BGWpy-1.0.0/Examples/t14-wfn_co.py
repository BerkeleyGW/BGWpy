"""
Compute DFT wavefunctions and eigenvalues
on an unshifted k-point grid,
then adapt them for BGW.

Depends on:
    11-Density

Used by:
    22-Sigma
    23-Kernel
    24-Absorption
"""
from BGWpy import Structure, WfnTask, PW2BGWTask

# Common arguments for tasks.
kwargs = dict(
    dirname = '14-Wfn_co',

    structure = Structure.from_file('Data/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = 'Pseudos',
    pseudos = ['31-Ga.PBE.UPF', '33-As.PBE.UPF'],

    ngkpt = [2,2,2],      # k-points grid
    kshift = [.0,.0,.0],  # k-points shift
    ecutwfc = 10.0,       # Wavefunctions cutoff energy
    nbnd = 20,            # Number of bands

    # These are the default parameters for the MPI runner.
    # Please adapt them to your needs.
    nproc = 1,
    nproc_per_node = 1,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )

# Wavefunctions and eigenvalues calculation (NSCF) on a k-shifted grid
wfntask_ush = WfnTask(
    charge_density_fname = '11-Density/GaAs.save/charge-density.dat',
    data_file_fname = '11-Density/GaAs.save/data-file.xml',
    **kwargs)


# Interfacing PW with BerkeleyGW.
pw2bgwtask_ush = PW2BGWTask(
    wfn_fname = 'wfn_co.cplx',
    rho_fname = 'rho.real',
    vxc_diag_nmax = 8,
    **kwargs)


# Execution
for task in (wfntask_ush, pw2bgwtask_ush):
    task.write()
    task.run()

