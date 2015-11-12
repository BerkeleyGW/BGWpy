
from .inputs import EpsilonInput, SigmaInput, KernelInput, AbsorptionInput

def get_epsilon_input(ecuteps, nbnd, nbnd_occ, q0, qpts, *keywords, **variables):

    return EpsilonInput(ecuteps, nbnd, nbnd_occ, q0, qpts, *keywords, **variables)


def get_sigma_input(ecuteps, ecutsigx, nbnd, nbnd_occ, ibnd_min, ibnd_max, kpts,
                    *keywords, **variables):

    return SigmaInput(ecuteps, ecutsigx, nbnd, nbnd_occ, ibnd_min, ibnd_max, kpts,
                      'screening_semiconductor', *keywords, **variables)


def get_kernel_input(nbnd_val, nbnd_cond, ecuteps, ecutsigx,
                     *keywords, **variables):

    return KernelInput(nbnd_val, nbnd_cond, ecuteps, ecutsigx,
                       'use_symmetries_coarse_grid', 'screening_semiconductor',
                       *keywords, **variables)


def get_absorption_input(nbnd_val_co, nbnd_cond_co, nbnd_val_fi, nbnd_cond_fi,
                         *keywords, **variables):

    return AbsorptionInput(nbnd_val_co, nbnd_cond_co, nbnd_val_fi, nbnd_cond_fi,
                           'diagonalization',
                           'use_symmetries_coarse_grid',
                           'no_symmetries_fine_grid',
                           'no_symmetries_shifted_grid',
                           'screening_semiconductor',
                           'use_velocity',
                           'gaussian_broadening',
                           'eqp_co_corrections',
                           *keywords, **variables)

