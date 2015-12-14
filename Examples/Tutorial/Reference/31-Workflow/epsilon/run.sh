#!/bin/bash


# This is a test
MPIRUN='mpirun -n 1 --npernode 1'
EPSILON='epsilon.cplx.x'
EPSILONOUT='epsilon.out'

ln -nfs ../wfn/wfn.cplx WFN
ln -nfs ../wfnq/wfnq.cplx WFNq

$MPIRUN $EPSILON &> $EPSILONOUT

# This is another test
