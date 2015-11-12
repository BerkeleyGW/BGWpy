#!/usr/bin/env bash

MPIRUN='mpirun -n 2 --npernode 2'
PW='pw.x'
PW_flags=''

ln -nfs ../../01-density/GaAs.save/charge-density.dat GaAs.save/charge-density.dat

cp -f ../01-density/GaAs.save/data-file.xml GaAs.save/data-file.xml
$MPIRUN $PW -in wfn.in &> wfn.out
