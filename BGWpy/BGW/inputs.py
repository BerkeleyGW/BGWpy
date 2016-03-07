from __future__ import print_function
from collections import OrderedDict

import numpy as np

from ..core import BasicInputFile


class EpsilonInput(BasicInputFile):

    def __init__(self, ecuteps, q0, qpts, *keywords, **variables):

        all_variables = OrderedDict([
            ('epsilon_cutoff' , ecuteps),
            ])

        all_variables.update(variables)

        super(EpsilonInput, self).__init__(all_variables, keywords)

        self.q0 = q0
        self.qpts = qpts

    def __str__(self):

        qpt_block = '\nbegin qpoints\n'
        for q0i in self.q0:
            qpt_block += ' {:11.8f}'.format(q0i)
        qpt_block += ' 1.0 1\n'

        for q in self.qpts:
            for qi in q:
                qpt_block += ' {:11.8f}'.format(qi)
            qpt_block += ' 1.0 0\n'
        qpt_block += 'end\n'

        return super(EpsilonInput, self).__str__() + qpt_block


class SigmaInput(BasicInputFile):

    def __init__(self, ibnd_min, ibnd_max, kpts, *keywords, **variables):

        all_variables = OrderedDict([
            ('band_index_min' , ibnd_min),
            ('band_index_max' , ibnd_max),
            ])

        # Handle q-points
        self.qpts = variables.pop('qpts', [])
        for key in ('ngqpt', 'qgrid'):
            if key in variables:
                self.ngqpt = variables.pop(key)
                break
        else:
            if self.qpts:
                raise Exception("When qpts is specified, the qpoint grid must also be specified " +
                                "through 'ngqpt' or 'qgrid'.")

        all_variables.update(variables)

        super(SigmaInput, self).__init__(all_variables, keywords)

        self.kpts = kpts

    def __str__(self):

        S = super(SigmaInput, self).__str__()

        kpt_block = '\nbegin kpoints\n'
        for k in self.kpts:
            for ki in k:
                kpt_block += ' {:11.8f}'.format(ki)
            kpt_block += ' 1.0\n'
        kpt_block += 'end\n'

        S += kpt_block

        if self.qpts:
            qpt_block = '\nbegin qpoints\n'
            for q in self.qpts:
                for qi in q:
                    qpt_block += ' {:11.8f}'.format(qi)

                if all(np.isclose(q, .0)):
                    qpt_block += ' 1.0 1\n'
                else:
                    qpt_block += ' 1.0 0\n'
            qpt_block += 'end\n'
            qpt_block += 'qgrid {} {} {}\n'.format(*self.ngqpt)

            S += qpt_block

        return S


class KernelInput(BasicInputFile):

    def __init__(self, nbnd_val, nbnd_cond, *keywords, **variables):

        all_variables = OrderedDict([
            ('number_val_bands' , nbnd_val),
            ('number_cond_bands' , nbnd_cond),
            ])

        all_variables.update(variables)

        super(KernelInput, self).__init__(all_variables, keywords)


class AbsorptionInput(BasicInputFile):

    def __init__(self, nbnd_val_co, nbnd_cond_co, nbnd_val_fi, nbnd_cond_fi,
                 *keywords, **variables):

        all_variables = OrderedDict([
            ('number_val_bands_coarse' , nbnd_val_co),
            ('number_val_bands_fine' , nbnd_val_fi),
            ('number_cond_bands_coarse' , nbnd_cond_co),
            ('number_cond_bands_fine' , nbnd_cond_fi),
            ('energy_resolution' , 0.1),
            ])

        all_variables.update(variables)

        super(AbsorptionInput, self).__init__(all_variables, keywords)


