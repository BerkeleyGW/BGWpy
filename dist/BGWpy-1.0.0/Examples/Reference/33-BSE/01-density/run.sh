#!/usr/bin/env bash

MPIRUN='mpirun -n 2 --npernode 2'
PW='pw.x'
PW_flags=''


$MPIRUN $PW -in scf.in &> scf.out
