
import os

pseudo_dir = os.path.join(os.path.dirname(__file__), 'pseudos')
structure_GaAs = os.path.join(os.path.dirname(__file__), 'structures', 'GaAs.json')
pseudos_GaAs = ['31-Ga.PBE.UPF', '33-As.PBE.UPF']

__all__ = ['pseudo_dir', 'structure_GaAs']

