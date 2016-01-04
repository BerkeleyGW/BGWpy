#!/bin/bash
rsync -avh [0-9]* Reference/ --exclude=README --exclude=Reference --exclude=Data --exclude=Pseudos --exclude=*.py --include=*.sh --include=*.in --include=*.inp --include=*.out --include=*.cif --include=*.json --exclude=*.save --include=*/*/ --exclude=*/* --exclude=*/*/*
