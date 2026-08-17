#!/bin/bash


MPIRUN='mpirun -n 8 --npernode 8'
PW='pw.x'
PWFLAGS=''
PW2BGW='pw2bgw.x'

$MPIRUN $PW2BGW -in wfn.pp.in &> wfn.pp.out

