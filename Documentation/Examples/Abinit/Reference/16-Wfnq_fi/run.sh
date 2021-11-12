#!/bin/bash


MPIRUN='mpirun -n 1 --npernode 1'

bash wfn.run.sh
bash abi2bgw.run.sh

