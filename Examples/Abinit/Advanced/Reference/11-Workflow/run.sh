#!/bin/bash



cd density
bash run.sh
cd ..
cd wfn
bash run.sh
cd ..
cd wfn
bash abi2bgw.run.sh
cd ..
cd wfnq
bash run.sh
cd ..
cd wfnq
bash abi2bgw.run.sh
cd ..
cd wfn_co
bash run.sh
cd ..
cd wfn_co
bash abi2bgw.run.sh
cd ..
cd epsilon
bash run.sh
cd ..
cd sigma
bash run.sh
cd ..

