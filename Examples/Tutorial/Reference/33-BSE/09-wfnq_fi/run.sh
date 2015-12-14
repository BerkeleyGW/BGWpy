#!/bin/bash


# This is a test
MPIRUN='mpirun -n 2 --npernode 2'
PW='pw.x'
PWFLAGS=''

ln -nfs ../../01-density/GaAs.save/charge-density.dat GaAs.save/charge-density.dat

cp -f ../01-density/GaAs.save/data-file.xml GaAs.save/data-file.xml

$MPIRUN $PW $PWFLAGS -in wfn.in &> wfn.out

# This is another test
