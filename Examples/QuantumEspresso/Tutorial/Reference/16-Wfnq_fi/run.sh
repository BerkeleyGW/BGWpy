#!/bin/bash


MPIRUN='mpirun -n 1 --npernode 1'

cd Wavefunctions
bash run.sh
cd ..
cd Wavefunctions
bash run-pw2bgw.sh
cd ..

