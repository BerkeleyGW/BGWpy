#!/usr/bin/env bash

MPIRUN='mpirun -n 1 --npernode 1'
PW='pw.x'
PW_flags=''

ln -nfs ../../density/GaAs.save/charge-density.dat GaAs.save/charge-density.dat

cp -f ../density/GaAs.save/data-file.xml GaAs.save/data-file.xml
$MPIRUN $PW -in wfn.in &> wfn.out
