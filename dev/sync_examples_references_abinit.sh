#!/bin/bash
rsync -avh [0-9]* Reference/ --exclude=README --exclude=Reference --exclude=Data --exclude=Pseudos --exclude=*.py --exclude=gsphere_bgw.out --include=*.sh --include=*.in --include=*.files --include=*.out --include=*.cif --include=*.json --exclude=*.log --exclude=*/out_data/* --exclude=*/*/out_data/* --exclude=*/*/*/out_data/* --include=*/*/ --exclude=*/* --exclude=*/*/*
