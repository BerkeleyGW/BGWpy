
import os

pseudo_dir = os.path.join(os.path.dirname(__file__), 'pseudos')

# TODO
# Gotta handle the pseudos a bit better.

# GaAs
structure_GaAs = os.path.join(os.path.dirname(__file__), 'structures', 'GaAs.json')
pseudos_GaAs = ['31-Ga.PBE.UPF', '33-As.PBE.UPF']

# Si
structure_Si = os.path.join(os.path.dirname(__file__), 'structures', 'Si.json')
pseudos_Si = ['14-Si.pspnc']

del os

