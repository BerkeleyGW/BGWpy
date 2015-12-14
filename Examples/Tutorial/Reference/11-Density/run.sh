#!/bin/bash


# This is a test
MPIRUN='mpirun -n 1 --npernode 1'
PW='pw.x'
PWFLAGS=''

$MPIRUN $PW $PWFLAGS -in scf.in &> scf.out

# This is another test
