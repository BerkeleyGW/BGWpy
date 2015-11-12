#!/usr/bin/env bash

MPIRUN='mpirun -n 2 --npernode 2'
EPSILON='epsilon.cplx.x'
EPSILONOUT='epsilon.out'

ln -nfs ../12-Wfn/wfn.cplx WFN
ln -nfs ../13-Wfnq/wfnq.cplx WFNq

$MPIRUN $EPSILON &> $EPSILONOUT
