import os
from BGWpy import Structure, Workflow
from BGWpy import AbinitBgwFlow
from BGWpy import EpsilonTask, SigmaTask


# --------------------------------------------------------------------------- #
""" Common arguments for tasks.                                             """

common = dict(
    structure = Structure.from_file('../Data/Structures/Si.json'),
    prefix = 'Si',
    pseudo_dir = '../Data/Pseudos',
    pseudos = ['14-Si.pspnc'],
    ngkpt = [2,2,2],
    kshift = [.5,.5,.5],
    ecut = 5.0,
    nband = 9,
    input_variables={'prtvxc': 1, 'istwfk' : '*1'},
    ecuteps = 10.0,
    sigma_extra_lines = ['screening_semiconductor'],
    ibnd_min = 1,
    ibnd_max = 8,

    nproc = 1,
    nproc_per_node = 1,
    mpirun = 'mpirun',
    nproc_flag = '-n',
    nproc_per_node_flag = '--npernode',
    )


# --------------------------------------------------------------------------- #
""" Tasks                                                                   """

flow = Workflow(dirname='01-GW')

wfn = AbinitBgwFlow(dirname = os.path.join(flow.dirname, '01-Wfn'),
                    with_density = True, **common)

common.update(qshift = [0.001,0,0])
wfnq = AbinitBgwFlow(dirname = os.path.join(flow.dirname, '02-Wfnq'),
                     charge_density_fname = wfn.charge_density_fname,
                     **common)

common.update(qshift=3*[0], kshift=3*[0])
wfnco = AbinitBgwFlow(dirname = os.path.join(flow.dirname, '03-Wfn_co'),
                      charge_density_fname = wfn.charge_density_fname,
                      **common)


common.update(qshift = [0.001,0,0])
epsilon = EpsilonTask(
    dirname = os.path.join(flow.dirname, '11-Epsilon'),
    wfn_fname = wfn.wfn_fname,
    wfnq_fname = wfnq.wfn_fname,
    **common)

sigma = SigmaTask(
    dirname = os.path.join(flow.dirname, '12-Sigma'),
    eps0mat_fname = epsilon.eps0mat_fname,
    epsmat_fname = epsilon.epsmat_fname,
    wfn_co_fname = wfnco.wfn_fname,
    rho_fname = wfn.rho_fname,
    vxc_fname = wfn.vxc_fname,
    **common)


flow.add_tasks([wfn, wfnq, wfnco, epsilon, sigma], merge=False)


# --------------------------------------------------------------------------- #
""" Execution                                                               """

flow.write()
flow.run()
flow.report()
