#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
SIGMA='sigma.cplx.x'
SIGMAOUT='sigma.out'

ln -nfs ../04-Wfn_co/Wavefunctions/wfn.cplx WFN_inner
ln -nfs ../04-Wfn_co/Wavefunctions/rho.real RHO
ln -nfs ../04-Wfn_co/Wavefunctions/vxc.dat vxc.dat
ln -nfs ../11-epsilon/eps0mat eps0mat
ln -nfs ../11-epsilon/epsmat epsmat

$MPIRUN $SIGMA &> $SIGMAOUT

