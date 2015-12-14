
import numpy as np

__all__ = ['get_kpt_variables', 'get_scf_variables', 'get_wfn_variables']

def get_kpt_variables(**kwargs):
    """Extract the variables to declare the k-points grid."""

    variables = dict()

    if 'kpt' in kwargs:

        kpt = np.array(kwargs['kpt']).reshape((-1,3))
        variables['kptopt'] = 0
        variables['kpt'] = kpt
        variables['nkpt'] = len(kpt)
        variables['wtk'] = kwargs['wtk']

    elif 'ngkpt' in kwargs:

        variables['ngkpt'] = kwargs['ngkpt']
        variables['kptopt'] = kwargs.get('kptopt', 1)

        shiftk = np.array(kwargs.get('shiftk', 3*[0.])).reshape((-1,3))
        variables['shiftk'] = shiftk
        variables['nshiftk'] = len(shiftk)

    return variables


def get_scf_variables(**kwargs):
    """Return a dict of variables required for an SCF calculation."""
    variables = dict(
        prtden = 1,
        prtvxc = 1,
        tolvrs = kwargs.get('tolvrs', 1e-10),
        ecut = kwargs.get('ecut'),
        )
    return variables


def get_wfn_variables(**kwargs):
    """Return a dict of variables required for an SCF calculation."""
    variables = dict(
        irdden = 1,
        nband = kwargs.get('nband'),
        ecut = kwargs.get('ecut'),
        tolwfr = kwargs.get('tolwfr', 1e-14),
        iscf = kwargs.get('iscf', -3),
        istwfk = kwargs.get('istwfk', '*1'),
        )
    return variables

