#!/bin/bash


# This is a test
MPIRUN='mpirun -n 1 --npernode 1'
PW='pw.x'
PWFLAGS=''

ln -nfs ../../density/GaAs.save/charge-density.dat GaAs.save/charge-density.dat

cp -f ../density/GaAs.save/data-file.xml GaAs.save/data-file.xml

$MPIRUN $PW $PWFLAGS -in wfn.in &> wfn.out

# This is another test
