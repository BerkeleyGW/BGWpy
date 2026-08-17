#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'

bash wfn.run.sh
bash abi2bgw.run.sh

