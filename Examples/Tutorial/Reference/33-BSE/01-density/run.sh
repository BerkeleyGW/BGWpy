#!/bin/bash


# This is a test
MPIRUN='mpirun -n 2 --npernode 2'
PW='pw.x'
PWFLAGS=''

$MPIRUN $PW $PWFLAGS -in scf.in &> scf.out

# This is another test
