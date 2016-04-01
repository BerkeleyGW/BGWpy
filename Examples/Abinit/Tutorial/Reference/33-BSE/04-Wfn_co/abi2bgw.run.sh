#!/bin/bash


MPIRUN='mpirun -n 2 --npernode 2'
ABINIT='abinit'
ABI2BGW='abi2bgw.x'

$ABI2BGW abi2bgw.in >& abi2bgw.out

