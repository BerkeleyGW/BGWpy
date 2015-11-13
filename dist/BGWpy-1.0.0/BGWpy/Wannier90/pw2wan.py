
from ..core import Namelist

__all__ = ['PW2WanInput']

class PW2WanInput(Namelist):

    def __init__(self, prefix, outdir='./', write_amn=True, write_mmn=True, seedname=None, **kwargs):

        super(PW2WanInput, self).__init__('inputpp', [
            ('prefix', prefix),
            ('outdir', outdir),
            ('seedname', seedname if seedname else prefix),
            ('write_amn', write_amn),
            ('write_mmn', write_mmn),],
            **kwargs)
