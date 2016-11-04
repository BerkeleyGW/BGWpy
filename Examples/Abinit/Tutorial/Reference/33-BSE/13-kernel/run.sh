#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
KERNEL='kernel.cplx.x'

ln -nfs ../04-Wfn_co/wfn.cplx WFN_co
ln -nfs ../11-epsilon/eps0mat.h5 eps0mat.h5
ln -nfs ../11-epsilon/epsmat.h5 epsmat.h5

$MPIRUN $KERNEL &> kernel.out

