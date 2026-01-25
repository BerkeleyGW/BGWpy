import os
from pathlib import Path

pseudo_dir = str(Path(__file__).parent / "pseudos")

# TODO
# Gotta handle the pseudos a bit better.

# GaAs
structure_GaAs = str(Path(__file__).parent / "structures" / "GaAs.json")
pseudos_GaAs = ["31-Ga.PBE.UPF", "33-As.PBE.UPF"]

# Si
structure_Si = str(Path(__file__).parent / "structures" / "Si.json")
pseudos_Si = ["14-Si.pspnc"]
pseudos_Si_upf = ["Si.UPF"]

del os
