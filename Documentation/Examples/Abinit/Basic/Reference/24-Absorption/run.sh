#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
ABSORPTION='absorption.cplx.x'

ln -nfs ../14-Wfn_co/wfn.cplx WFN_co
ln -nfs ../15-Wfn_fi/wfn.cplx WFN_fi
ln -nfs ../16-Wfnq_fi/wfn.cplx WFNq_fi
ln -nfs ../21-Epsilon/eps0mat.h5 eps0mat.h5
ln -nfs ../21-Epsilon/epsmat.h5 epsmat.h5
ln -nfs ../23-Kernel/bsemat.h5 bsemat.h5
ln -nfs ../22-Sigma/eqp1.dat eqp_co.dat

$MPIRUN $ABSORPTION &> absorption.out

