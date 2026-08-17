#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
ABSORPTION='absorption.cplx.x'

ln -nfs ../04-Wfn_co/wfn.cplx WFN_co
ln -nfs ../05-Wfn_fi/wfn.cplx WFN_fi
ln -nfs ../06-Wfnq_fi/wfn.cplx WFNq_fi
ln -nfs ../11-epsilon/eps0mat.h5 eps0mat.h5
ln -nfs ../11-epsilon/epsmat.h5 epsmat.h5
ln -nfs ../13-kernel/bsemat.h5 bsemat.h5
ln -nfs ../12-sigma/eqp1.dat eqp_co.dat

$MPIRUN $ABSORPTION &> absorption.out

