#!/bin/bash


MPIRUN='mpirun -n 8 --npernode 8'
ABINIT='abinit'

$MPIRUN $ABINIT < GaAs.files &> GaAs.log

