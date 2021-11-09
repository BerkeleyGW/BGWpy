#!/bin/sh



# Lines before execution
MPIRUN='mpirun -n 1 --npernode 1'
ABINIT='abinit'

$MPIRUN $ABINIT < GaAs.files &> GaAs.log


# Lines after execution
