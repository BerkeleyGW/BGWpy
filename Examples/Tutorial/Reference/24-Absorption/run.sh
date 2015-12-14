#!/bin/bash


# This is a test
MPIRUN='mpirun -n 2 --npernode 2'
EQP='eqp.py'
ABSORPTION='absorption.cplx.x'
ABSORPTIONOUT='absorption.out'

ln -nfs ../14-Wfn_co/wfn_co.cplx WFN_co
ln -nfs ../15-Wfn_fi/wfn_fi.cplx WFN_fi
ln -nfs ../16-Wfnq_fi/wfnq_fi.cplx WFNq_fi
ln -nfs ../21-Epsilon/eps0mat eps0mat
ln -nfs ../21-Epsilon/epsmat epsmat
ln -nfs ../23-Kernel/bsedmat bsedmat
ln -nfs ../23-Kernel/bsexmat bsexmat
ln -nfs ../22-Sigma/sigma_hp.log sigma_hp.log
ln -nfs ../22-Sigma/eqp1.dat eqp_co.dat

$MPIRUN $ABSORPTION &> $ABSORPTIONOUT

# This is another test
