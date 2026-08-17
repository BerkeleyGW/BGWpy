#!/bin/bash


MPIRUN='mpirun -n 8 --npernode 8'
SIGMA='sigma.cplx.x'
SIGMAOUT='sigma.out'

ln -nfs ../wfn_co/wfn_co.cplx WFN_inner
ln -nfs ../wfn_co/rho.real RHO
ln -nfs ../wfn_co/vxc.dat vxc.dat
ln -nfs ../epsilon/eps0mat eps0mat
ln -nfs ../epsilon/epsmat epsmat

$MPIRUN $SIGMA &> $SIGMAOUT

