#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'

cd Wavefunctions
bash run.sh
cd ..
cd Wavefunctions
bash run-pw2bgw.sh
cd ..

