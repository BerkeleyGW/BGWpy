#!/bin/bash


# This is a test
MPIRUN='mpirun -n 2 --npernode 2'
KERNEL='kernel.cplx.x'
KERNELOUT='kernel.out'

ln -nfs ../04-wfn_co/wfn_co.cplx WFN_co
ln -nfs ../05-epsilon/eps0mat eps0mat
ln -nfs ../05-epsilon/epsmat epsmat

$MPIRUN $KERNEL &> $KERNELOUT

# This is another test
