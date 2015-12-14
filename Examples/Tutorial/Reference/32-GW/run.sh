#!/bin/bash


# This is a test

cd 01-density
bash run.sh
cd ..
cd 02-wfn
bash run.sh
cd ..
cd 02-wfn
bash run-pw2bgw.sh
cd ..
cd 03-wfnq
bash run.sh
cd ..
cd 03-wfnq
bash run-pw2bgw.sh
cd ..
cd 04-wfn_co
bash run.sh
cd ..
cd 04-wfn_co
bash run-pw2bgw.sh
cd ..
cd 05-epsilon
bash run.sh
cd ..
cd 06-sigma
bash run.sh
cd ..

# This is another test
