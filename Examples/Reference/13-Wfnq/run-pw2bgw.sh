#!/bin/bash


# This is a test
MPIRUN='mpirun -n 1 --npernode 1'
PW='pw.x'
PWFLAGS=''
PW2BGW='pw2bgw.x'

$MPIRUN $PW2BGW -in wfn.pp.in &> wfn.pp.out

# This is another test
