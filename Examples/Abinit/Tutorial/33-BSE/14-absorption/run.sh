#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
ABSORPTION='absorption.cplx.x'
ABSORPTIONOUT='absorption.out'

ln -nfs ../04-Wfn_co/Wavefunctions/wfn.cplx WFN_co
ln -nfs ../05-Wfn_fi/Wavefunctions/wfn.cplx WFN_fi
ln -nfs ../06-Wfnq_fi/Wavefunctions/wfn.cplx WFNq_fi
ln -nfs ../11-epsilon/eps0mat eps0mat
ln -nfs ../11-epsilon/epsmat epsmat
ln -nfs ../13-kernel/bsedmat bsedmat
ln -nfs ../13-kernel/bsexmat bsexmat
ln -nfs ../12-sigma/sigma_hp.log sigma_hp.log
ln -nfs ../12-sigma/eqp1.dat eqp_co.dat

$MPIRUN $ABSORPTION &> $ABSORPTIONOUT

