#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
SIGMA='sigma.cplx.x'

ln -nfs ../14-Wfn_co/wfn.cplx WFN_inner
ln -nfs ../14-Wfn_co/rho.real RHO
ln -nfs ../14-Wfn_co/vxc.dat vxc.dat
ln -nfs ../21-Epsilon/eps0mat.h5 eps0mat.h5
ln -nfs ../21-Epsilon/epsmat.h5 epsmat.h5

$MPIRUN $SIGMA &> sigma.out

