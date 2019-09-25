
import os
import numpy as np

from ..external import xmltodict

def get_eigs_unpol(savedir):
    """
    Read the bandstructure in savedir, relying on the data-file.xml.
    This is for the non spin-polarized case.
    Returns: kpoints, eigenvalues_Ha
    """

    with open(os.path.join(savedir, 'data-file.xml'), 'r') as f:
        datafile = xmltodict.parse(f)

    kpoints = list()
    eigs = list()

    for kdict in datafile['Root']['EIGENVALUES'].values():

        kpt = np.array(map(float, kdict['K-POINT_COORDS']['#text'].split()))

        eigfname = os.path.join(savedir, kdict['DATAFILE']['@iotk_link'])
        with open(eigfname, 'r') as f:
            edict = xmltodict.parse(f)

        eigs_Ha = np.array(map(float, edict['Root'][u'EIGENVALUES']['#text'].split()))

        kpoints.append(kpt)
        eigs.append(eigs_Ha)

    return np.array(kpoints), np.array(eigs)


