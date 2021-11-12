#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
KERNEL='kernel.cplx.x'

ln -nfs ../14-Wfn_co/wfn.cplx WFN_co
ln -nfs ../21-Epsilon/eps0mat.h5 eps0mat.h5
ln -nfs ../21-Epsilon/epsmat.h5 epsmat.h5

$MPIRUN $KERNEL &> kernel.out

