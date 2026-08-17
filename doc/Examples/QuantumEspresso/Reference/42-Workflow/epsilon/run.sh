#!/bin/bash


MPIRUN='mpirun -n 8 --npernode 8'
EPSILON='epsilon.cplx.x'
EPSILONOUT='epsilon.out'

ln -nfs ../wfn/wfn.cplx WFN
ln -nfs ../wfnq/wfnq.cplx WFNq

$MPIRUN $EPSILON &> $EPSILONOUT

