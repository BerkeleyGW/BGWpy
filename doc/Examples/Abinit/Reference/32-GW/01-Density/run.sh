#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
ABINIT='abinit'

$MPIRUN $ABINIT < GaAs.files &> GaAs.log

