#!/bin/bash
rm -rf 01-Structure
rm -rf 11-Density
rm -rf 12-Wfn
rm -rf 13-Wfnq
rm -rf 14-Wfn_co
rm -rf 15-Wfn_fi
rm -rf 16-Wfnq_fi
rm -rf 21-Epsilon
rm -rf 22-Sigma
rm -rf 23-Kernel
rm -rf 24-Absorption
rm -rf 31-Workflow
rm -rf 32-GW
rm -rf 33-BSE

python t01-Structure.py
python t11-Density.py
python t12-Wfn.py
python t13-Wfnq.py
python t14-Wfn_co.py
python t15-Wfn_fi.py
python t16-Wfnq_fi.py
python t21-Epsilon.py
python t22-Sigma.py
python t23-Kernel.py
python t24-Absorption.py
python t31-Workflow.py
python t32-GW.py
python t33-BSE.py
