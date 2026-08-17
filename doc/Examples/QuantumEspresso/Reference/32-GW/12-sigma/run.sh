#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
SIGMA='sigma.cplx.x'

ln -nfs ../04-Wfn_co/wfn.cplx WFN_inner
ln -nfs ../04-Wfn_co/rho.real RHO
ln -nfs ../04-Wfn_co/vxc.dat vxc.dat
ln -nfs ../11-epsilon/eps0mat.h5 eps0mat.h5
ln -nfs ../11-epsilon/epsmat.h5 epsmat.h5

$MPIRUN $SIGMA &> sigma.out

