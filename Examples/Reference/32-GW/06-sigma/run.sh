#!/usr/bin/env bash

MPIRUN='mpirun -n 2 --npernode 2'
SIGMA='sigma.cplx.x'
SIGMAOUT='sigma.out'

ln -nfs ../04-wfn_co/wfn_co.cplx WFN_inner
ln -nfs ../04-wfn_co/rho.real RHO
ln -nfs ../04-wfn_co/vxc.dat vxc.dat
ln -nfs ../05-epsilon/eps0mat eps0mat
ln -nfs ../05-epsilon/epsmat epsmat

$MPIRUN $SIGMA &> $SIGMAOUT
