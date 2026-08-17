#!/bin/bash


MPIRUN='mpirun -n 8 --npernode 8'
SIGMA='sigma.cplx.x'
SIGMAOUT='sigma.out'

ln -nfs ../wfn_co/wfn.cplx WFN_inner
ln -nfs ../wfn_co/rho.cplx RHO
ln -nfs ../wfn_co/vxc.cplx VXC
ln -nfs ../epsilon/eps0mat eps0mat
ln -nfs ../epsilon/epsmat epsmat

$MPIRUN $SIGMA &> $SIGMAOUT

