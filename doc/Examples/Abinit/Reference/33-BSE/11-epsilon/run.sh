#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
EPSILON='epsilon.cplx.x'

ln -nfs ../02-Wfn/wfn.cplx WFN
ln -nfs ../03-Wfnq/wfn.cplx WFNq

$MPIRUN $EPSILON &> epsilon.out

