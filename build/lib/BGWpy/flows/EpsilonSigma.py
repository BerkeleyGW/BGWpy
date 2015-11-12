
import os
from os.path import join as pjoin
import subprocess
import pickle
from ..core import Workflow
from ..BGW import get_kpt_grid, get_epsilon_input, get_sigma_input

class EpsilonSigmaFlow(Workflow):

    def __init__(self, dirname, nproc, prefix, pseudo_dir, pseudos,
                 structure,
                 ngkpt,
                 kshift,
                 qshift,
                 nbnd_occ,
                 nbnd,
                 nbnd_epsilon,
                 nbnd_sigma,
                 ibnd_min,
                 ibnd_max,
                 ecutwfc,
                 ecuteps,
                 ecutsigx,
                 wfn_fname,
                 wfnq_fname,
                 wfn_co_fname,
                 rho_fname,
                 vxc_fname,
                 epsilon_extra_lines=[],
                 sigma_extra_lines=[],
                 epsilon_variables={},
                 sigma_variables={},
                 **kwargs):
        """The Epsilon and Sigma part of the one-shot GW workflow."""

        self.dirname = dirname

        # Store the input variables in a file
        self.variables = dict(
            structure=structure.as_dict(),
            pseudo_dir=pseudo_dir,
            pseudos=pseudos,
            ngkpt=ngkpt,
            kshift=kshift,
            qshift=qshift,
            nbnd_occ=nbnd_occ,
            nbnd=nbnd,
            nbnd_epsilon=nbnd_epsilon,
            nbnd_sigma=nbnd_sigma,
            ibnd_min=ibnd_min,
            ibnd_max=ibnd_max,
            ecutwfc=ecutwfc,
            ecuteps=ecuteps,
            ecutsigx=ecutsigx,
            epsilon_extra_lines=epsilon_extra_lines,
            sigma_extra_lines=sigma_extra_lines,
            epsilon_variables=epsilon_variables,
            sigma_variables=sigma_variables,
            **kwargs)

        # Compute k-shifted k+q-shifted and unshifted k-points grids
        #kpts_sh, wtks_sh = get_kpt_grid(structure, ngkpt, kshift=kshift, rootname='tmp.wfn.kgrid')
        #kpts_shq, wtks_shq = get_kpt_grid(structure, ngkpt, kshift=kshift, qshift=qshift, rootname='tmp.wfnq.
        kpts_ush, wtks_ush = get_kpt_grid(structure, ngkpt, rootname='tmp.wfn_co.kgrid')

        self.wfn_fname = wfn_fname
        self.wfnq_fname = wfnq_fname
        self.wfn_co_fname = wfn_co_fname
        self.rho_fname = rho_fname
        self.vxc_fname = vxc_fname

        # Make run file
        self.mpirun_n = kwargs.pop('mpirun_n', 'aprun -n')
        self.nproc_per_node = kwargs.pop('nproc_per_node', 24)
        self.nproc = nproc
        self.nproc_kpt = kwargs.get('nproc_kpt')
        self.nproc_bands = kwargs.get('nproc_bands')
        self.nproc_diag = kwargs.get('nproc_diag')

        # epsilon input
        self.epsilon = get_epsilon_input(ecuteps, nbnd_epsilon, nbnd_occ, qshift, kpts_ush[1:],
                                         *epsilon_extra_lines, **epsilon_variables)

        # sigma input
        self.sigma = get_sigma_input(ecuteps, ecutsigx, nbnd_sigma, nbnd_occ, ibnd_min, ibnd_max, kpts_ush,
                                     *sigma_extra_lines, **sigma_variables)


    def write(self):

        # Create main directory
        #os.system('mkdir -p ' + self.dirname)
        subprocess.call(['mkdir', '-p', self.dirname])

        # Write variables
        with open(pjoin(self.dirname, 'variables.pkl'), 'w') as f:
            pickle.dump(self.variables, f)

        # Make run file
        with open(pjoin(self.dirname, 'run.sh'), 'write') as f:
            f.write(self.get_run())

        self.epsilon.write(pjoin(self.dirname, 'epsilon.inp'))
        self.sigma.write(pjoin(self.dirname, 'sigma.inp'))

    def get_run(self):

        return """
#!/usr/bin/env bash

# Executables
MPIRUN="{mpirun_n} {nproc} --pes-per-node {nproc_per_node}"
EPSILON="epsilon.cplx.x"
SIGMA="sigma.cplx.x"

# Links
ln -nfs {wfn} WFN
ln -nfs {wfq} WFNq
ln -nfs {wfn_co} WFN_inner
ln -nfs {rho} RHO
ln -nfs {vxc} vxc.dat

echo `date`
echo 'Computing screening'
$MPIRUN $EPSILON &> ./epsilon.out

echo `date`
echo 'Computing self-energy'
$MPIRUN $SIGMA &> ./sigma.out

echo `date`
echo 'All done'

""".format(nproc=self.nproc, mpirun_n=self.mpirun_n, nproc_per_node=self.nproc_per_node,
           wfn=self.wfn_fname, wfq=self.wfnq_fname, wfn_co=self.wfn_co_fname,
           rho=self.rho_fname, vxc=self.vxc_fname)


