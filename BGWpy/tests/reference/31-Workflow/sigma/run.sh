#!/usr/bin/env bash

MPIRUN='mpirun -n 1 --npernode 1'
SIGMA='sigma.cplx.x'
SIGMAOUT='sigma.out'

ln -nfs ../wfn_co/wfn_co.cplx WFN_inner
ln -nfs ../wfn_co/rho.real RHO
ln -nfs ../wfn_co/vxc.dat vxc.dat
ln -nfs ../epsilon/eps0mat eps0mat
ln -nfs ../epsilon/epsmat epsmat

$MPIRUN $SIGMA &> $SIGMAOUT
