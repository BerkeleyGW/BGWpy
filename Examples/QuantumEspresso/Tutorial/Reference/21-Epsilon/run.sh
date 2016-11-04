#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
EPSILON='epsilon.cplx.x'

ln -nfs ../12-Wfn/wfn.cplx WFN
ln -nfs ../13-Wfnq/wfn.cplx WFNq

$MPIRUN $EPSILON &> epsilon.out

