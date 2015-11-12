#!/usr/bin/env bash

MPIRUN='mpirun -n 1 --npernode 1'
PW='pw.x'
PW_flags=''


$MPIRUN $PW -in scf.in &> scf.out
