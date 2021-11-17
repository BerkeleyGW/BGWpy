#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
PW='pw.x'
PWFLAGS=''

ln -nfs ../../01-Density/GaAs.save/charge-density.dat GaAs.save/charge-density.dat
ln -nfs ../../01-Density/GaAs.save/spin-polarization.dat GaAs.save/spin-polarization.dat

cp -f ../../../../Data/Pseudos/31-Ga.PBE.UPF GaAs.save/31-Ga.PBE.UPF
cp -f ../../../../Data/Pseudos/33-As.PBE.UPF GaAs.save/33-As.PBE.UPF
cp -f ../01-Density/GaAs.save/data-file.xml GaAs.save/data-file.xml

$MPIRUN $PW $PWFLAGS -in wfn.in &> wfn.out

