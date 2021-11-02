#!/bin/sh



# Lines before execution
MPIRUN='mpirun -n 1 --npernode 1'
ABINIT='abinit'
ABI2BGW='abi2bgw.x'

$ABI2BGW abi2bgw.in >& abi2bgw.out


# Lines after execution
