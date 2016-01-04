#!/bin/bash



cd density
bash run.sh
cd ..
cd wfn
bash run.sh
cd ..
cd wfn
bash run-pw2bgw.sh
cd ..
cd wfnq
bash run.sh
cd ..
cd wfnq
bash run-pw2bgw.sh
cd ..
cd wfn_co
bash run.sh
cd ..
cd wfn_co
bash run-pw2bgw.sh
cd ..
cd epsilon
bash run.sh
cd ..
cd sigma
bash run.sh
cd ..

