#!/bin/bash


MPIRUN='mpirun -n 8 --npernode 8'
ABINIT='abinit'

ln -nfs ../../density/out_data/odat_DEN input_data/idat_DEN

$MPIRUN $ABINIT < GaAs.files &> GaAs.log

