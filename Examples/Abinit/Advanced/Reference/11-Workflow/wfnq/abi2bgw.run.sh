#!/bin/bash


MPIRUN='mpirun -n 8 --npernode 8'
ABINIT='abinit'
ABI2BGW='abi2bgw.x'

$ABI2BGW abi2bgw.in >& abi2bgw.out

