import os
from os.path import join as pjoin
import pickle

from .GWFlow import GWFlow

def make_gw_calc(dirname, nproc, prefix, pseudo_dir, pseudos,
                 structure,
                 ngkpt,
                 kshift,
                 qshift,
                 nbnd_occ,
                 nbnd,
                 nbnd_epsilon,
                 nbnd_sigma,
                 ibnd_min,
                 ibnd_max,
                 ecutwfc,
                 ecuteps,
                 ecutsigx,
                 epsilon_extra_lines=[],
                 sigma_extra_lines=[],
                 **kwargs):

    flow = GWFlow(dirname, nproc, prefix, pseudo_dir, pseudos,
                 structure,
                 ngkpt,
                 kshift,
                 qshift,
                 nbnd_occ,
                 nbnd,
                 nbnd_epsilon,
                 nbnd_sigma,
                 ibnd_min,
                 ibnd_max,
                 ecutwfc,
                 ecuteps,
                 ecutsigx,
                 epsilon_extra_lines=epsilon_extra_lines,
                 sigma_extra_lines=sigma_extra_lines,
                 **kwargs)

    flow.write()
    return flow

