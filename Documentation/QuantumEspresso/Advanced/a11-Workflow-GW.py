"""
In this tedious example, a Workflow is constructed from several tasks
to perform a GW calculation.

Of course, the user is not expected to construct such workflow repeatedly.
They should instead use a GWFlow object to setup such calculations
(see next examples). The purpose of this example is to show the general
structure of a Workflow.

"""
from os.path import join as pjoin

from BGWpy import Structure, Workflow, QeScfTask, QeWfnTask, Qe2BgwTask, EpsilonTask, SigmaTask

workflow = Workflow(dirname='11-Workflow')

# Common arguments for tasks.
kwargs = dict(

    structure = Structure.from_file('../../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../../Data/Pseudos',
    pseudos = ['31-Ga.PBE.UPF', '33-As.PBE.UPF'],

    ngkpt = [2,2,2],
    ecutwfc = 10.0,
    nbnd = 9,

    # Parameters for the MPI runner
    nproc = 8,
    nproc_per_node = 8,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )


# Ground state density calculation (SCF)
scftask = QeScfTask(
    dirname = pjoin(workflow.dirname, 'density'),
    kshift = [.5,.5,.5],
    **kwargs)


# Wavefunctions and eigenvalues calculation (NSCF) on a k-shifted grid
wfntask_ksh = QeWfnTask(
    dirname = pjoin(workflow.dirname, 'wfn'),
    kshift = [.5,.5,.5],
    charge_density_fname = scftask.charge_density_fname,
    data_file_fname = scftask.data_file_fname,
    **kwargs)


# Interfacing PW with BerkeleyGW.
pw2bgwtask_ksh = Qe2BgwTask(
    dirname = wfntask_ksh.dirname,
    kshift = [.5,.5,.5],
    wfn_fname = 'wfn.cplx',
    **kwargs)


# Wavefunctions and eigenvalues calculation (NSCF) on a k+q-shifted grid
wfntask_qsh = QeWfnTask(
    dirname = pjoin(workflow.dirname, 'wfnq'),
    kshift = [.5,.5,.5],
    qshift = [.001,.0,.0],
    charge_density_fname = scftask.charge_density_fname,
    data_file_fname = scftask.data_file_fname,
    **kwargs)


# Interfacing PW with BerkeleyGW.
pw2bgwtask_qsh = Qe2BgwTask(
    dirname = wfntask_qsh.dirname,
    kshift = [.5,.5,.5],
    qshift = [.001,.0,.0],
    wfn_fname = 'wfnq.cplx',
    **kwargs)


# Wavefunctions and eigenvalues calculation (NSCF) on an unshifted grid
wfntask_ush = QeWfnTask(
    dirname = pjoin(workflow.dirname, 'wfn_co'),
    kshift = [.0,.0,.0],
    charge_density_fname = scftask.charge_density_fname,
    data_file_fname = scftask.data_file_fname,
    **kwargs)


# Interfacing PW with BerkeleyGW.
pw2bgwtask_ush = Qe2BgwTask(
    dirname = wfntask_ush.dirname,
    kshift = [.0,.0,.0],
    wfn_fname = 'wfn_co.cplx',
    rho_fname = 'rho.real',
    vxc_diag_nmax = 8,
    **kwargs)


# Dielectric matrix computation and inversion (epsilon)
epsilontask = EpsilonTask(
    dirname = pjoin(workflow.dirname, 'epsilon'),
    qshift = [.001,.0,.0],
    ecuteps = 10.0,
    wfn_fname = pw2bgwtask_ksh.wfn_fname,
    wfnq_fname = pw2bgwtask_qsh.wfn_fname,
    **kwargs)


# Self-energy calculation (sigma)
sigmatask = SigmaTask(
    dirname = pjoin(workflow.dirname, 'sigma'),
    ibnd_min = 1,
    ibnd_max = 8,
    extra_lines = ['screening_semiconductor'],
    #extra_variables = {'number_of_frequencies' : 10},
    wfn_co_fname = pw2bgwtask_ush.wfn_fname,
    rho_fname = pw2bgwtask_ush.rho_fname,
    vxc_dat_fname = pw2bgwtask_ush.vxc_dat_fname,
    eps0mat_fname = epsilontask.eps0mat_fname,
    epsmat_fname = epsilontask.epsmat_fname,
    **kwargs)


# Add all task without merging (executed from a sub-directory)
workflow.add_tasks([scftask,
                    wfntask_ksh, pw2bgwtask_ksh,
                    wfntask_qsh, pw2bgwtask_qsh,
                    wfntask_ush, pw2bgwtask_ush,
                    epsilontask, sigmatask,
                   ], merge=False)

# Execution
workflow.write()

for task in workflow.tasks:
    task.run()
    task.report()

# The previous iteration also could have been performed as
#workflow.run()
#workflow.report()
