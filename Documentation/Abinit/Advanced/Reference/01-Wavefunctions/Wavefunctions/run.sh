#!/bin/bash


MPIRUN='mpirun -n 1 --npernode 1'
ABINIT='abinit'

ln -nfs ../../Density/out_data/odat_DEN input_data/idat_DEN

$MPIRUN $ABINIT < GaAs.files &> GaAs.log

