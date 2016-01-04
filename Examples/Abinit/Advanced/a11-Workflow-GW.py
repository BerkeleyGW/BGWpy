"""
In this tedious example, a Workflow is constructed from several tasks
to perform a GW calculation.

Of course, the user is not expected to construct such workflow repeatedly.
They should instead use a GWFlow object to setup such calculations
(see next examples). The purpose of this example is to show the general
structure of a Workflow.

"""
from os.path import join as pjoin

from BGWpy import Structure, Workflow, AbinitScfTask, AbinitWfnTask, Abi2BgwTask, EpsilonTask, SigmaTask

workflow = Workflow(dirname='11-Workflow')

# Common arguments for tasks.
kwargs = dict(

    structure = Structure.from_file('../../Data/Structures/GaAs.json'),
    prefix = 'GaAs',
    pseudo_dir = '../../Data/Pseudos',
    pseudos = ['31-Ga.pspnc', '33-As.pspnc'],

    ngkpt = [2,2,2],
    ecut = 5.0,
    nband = 9,

    # Parameters for the MPI runner
    nproc = 8,
    nproc_per_node = 8,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )


# Ground state density calculation (SCF)
scftask = AbinitScfTask(
    dirname = pjoin(workflow.dirname, 'density'),
    kshift = [.5,.5,.5],
    **kwargs)


# Wavefunctions and eigenvalues calculation (NSCF) on a k-shifted grid
wfntask_ksh = AbinitWfnTask(
    dirname = pjoin(workflow.dirname, 'wfn'),
    kshift = [.5,.5,.5],
    charge_density_fname = scftask.charge_density_fname,
    **kwargs)


# Interfacing PW with BerkeleyGW.
abi2bgwtask_ksh = Abi2BgwTask(
    dirname = wfntask_ksh.dirname,
    kshift = [.5,.5,.5],
    wfn_fname = wfntask_ksh.wfn_fname,
    **kwargs)


# Wavefunctions and eigenvalues calculation (NSCF) on a k+q-shifted grid
wfntask_qsh = AbinitWfnTask(
    dirname = pjoin(workflow.dirname, 'wfnq'),
    kshift = [.5,.5,.5],
    qshift = [.001,.0,.0],
    charge_density_fname = scftask.charge_density_fname,
    **kwargs)


# Interfacing PW with BerkeleyGW.
abi2bgwtask_qsh = Abi2BgwTask(
    dirname = wfntask_qsh.dirname,
    kshift = [.5,.5,.5],
    qshift = [.001,.0,.0],
    wfn_fname = wfntask_qsh.wfn_fname,
    **kwargs)


# Wavefunctions and eigenvalues calculation (NSCF) on an unshifted grid
wfntask_ush = AbinitWfnTask(
    dirname = pjoin(workflow.dirname, 'wfn_co'),
    kshift = [.0,.0,.0],
    charge_density_fname = scftask.charge_density_fname,
    **kwargs)


# Interfacing PW with BerkeleyGW.
abi2bgwtask_ush = Abi2BgwTask(
    dirname = wfntask_ush.dirname,
    kshift = [.0,.0,.0],
    wfn_fname = wfntask_ush.wfn_fname,
    rho_fname = scftask.rho_fname,
    vxc_fname = scftask.vxc_fname,
    rhog_flag = True,
    vxcg_flag = True,
    **kwargs)


# Dielectric matrix computation and inversion (epsilon)
epsilontask = EpsilonTask(
    dirname = pjoin(workflow.dirname, 'epsilon'),
    qshift = [.001,.0,.0],
    ecuteps = 10.0,
    wfn_fname = abi2bgwtask_ksh.wfn_fname,
    wfnq_fname = abi2bgwtask_qsh.wfn_fname,
    **kwargs)


# Self-energy calculation (sigma)
sigmatask = SigmaTask(
    dirname = pjoin(workflow.dirname, 'sigma'),
    ibnd_min = 1,
    ibnd_max = 8,
    extra_lines = ['screening_semiconductor'],
    #extra_variables = {'number_of_frequencies' : 10},
    wfn_co_fname = abi2bgwtask_ush.wfn_fname,
    rho_fname = abi2bgwtask_ush.rho_fname,
    vxc_fname = abi2bgwtask_ush.vxc_fname,
    eps0mat_fname = epsilontask.eps0mat_fname,
    epsmat_fname = epsilontask.epsmat_fname,
    **kwargs)


# Add all task without merging (executed from a sub-directory)
workflow.add_tasks([scftask,
                    wfntask_ksh, abi2bgwtask_ksh,
                    wfntask_qsh, abi2bgwtask_qsh,
                    wfntask_ush, abi2bgwtask_ush,
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
