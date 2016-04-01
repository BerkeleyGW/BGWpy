#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
KERNEL='kernel.cplx.x'
KERNELOUT='kernel.out'

ln -nfs ../14-Wfn_co/wfn.cplx WFN_co
ln -nfs ../21-Epsilon/eps0mat eps0mat
ln -nfs ../21-Epsilon/epsmat epsmat

$MPIRUN $KERNEL &> $KERNELOUT

