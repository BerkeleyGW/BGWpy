#!/usr/bin/env bash

MPIRUN='mpirun -n 2 --npernode 2'
EQP='eqp.py'
ABSORPTION='absorption.cplx.x'
ABSORPTIONOUT='absorption.out'

ln -nfs ../04-wfn_co/wfn_co.cplx WFN_co
ln -nfs ../08-wfn_fi/wfn_fi.cplx WFN_fi
ln -nfs ../09-wfnq_fi/wfnq_fi.cplx WFNq_fi
ln -nfs ../05-epsilon/eps0mat eps0mat
ln -nfs ../05-epsilon/epsmat epsmat
ln -nfs ../07-kernel/bsedmat bsedmat
ln -nfs ../07-kernel/bsexmat bsexmat
ln -nfs ../06-sigma/sigma_hp.log sigma_hp.log

$EQP eqp1 sigma_hp.log eqp_co.dat
$MPIRUN $ABSORPTION &> $ABSORPTIONOUT
