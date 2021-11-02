#!/bin/bash


MPIRUN='mpirun -n 1 --npernode 1'
PW='pw.x'
PWFLAGS=''

ln -nfs ../../Density/GaAs.save/charge-density.dat GaAs.save/charge-density.dat

cp -f ../../../../Data/Pseudos/31-Ga.PBE.UPF GaAs.save/31-Ga.PBE.UPF
cp -f ../../../../Data/Pseudos/33-As.PBE.UPF GaAs.save/33-As.PBE.UPF
cp -f ../Density/GaAs.save/data-file.xml GaAs.save/data-file.xml

$MPIRUN $PW $PWFLAGS -in wfn.in &> wfn.out

