#!/usr/bin/env bash

MPIRUN='mpirun -n 2 --npernode 2'
EPSILON='epsilon.cplx.x'
EPSILONOUT='epsilon.out'

ln -nfs ../02-wfn/wfn.cplx WFN
ln -nfs ../03-wfnq/wfnq.cplx WFNq

$MPIRUN $EPSILON &> $EPSILONOUT
