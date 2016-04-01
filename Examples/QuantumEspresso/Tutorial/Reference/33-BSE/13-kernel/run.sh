#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
KERNEL='kernel.cplx.x'
KERNELOUT='kernel.out'

ln -nfs ../04-Wfn_co/wfn.cplx WFN_co
ln -nfs ../11-epsilon/eps0mat eps0mat
ln -nfs ../11-epsilon/epsmat epsmat

$MPIRUN $KERNEL &> $KERNELOUT

