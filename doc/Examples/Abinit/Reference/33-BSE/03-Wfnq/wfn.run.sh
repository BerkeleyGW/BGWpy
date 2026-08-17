#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
ABINIT='abinit'

ln -nfs ../../01-Density/out_data/odat_DEN input_data/idat_DEN

$MPIRUN $ABINIT < GaAs.files &> GaAs.log

