#!/bin/bash


MPIRUN='mpirun -n 8 --npernode 8'
PW='pw.x'
PWFLAGS=''

$MPIRUN $PW $PWFLAGS -in scf.in &> scf.out

