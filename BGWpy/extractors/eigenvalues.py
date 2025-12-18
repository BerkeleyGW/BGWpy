from __future__ import annotations

from pathlib import Path

import numpy as np

from BGWpy.external import xmltodict


def get_eigs_unpol(savedir):
    """
    Read the bandstructure in savedir, relying on the data-file.xml.
    This is for the non spin-polarized case.
    Returns: kpoints, eigenvalues_Ha
    """

    with (Path(savedir) / "data-file.xml").open() as f:
        datafile = xmltodict.parse(f)

    kpoints = []
    eigs = []

    for kdict in datafile["Root"]["EIGENVALUES"].values():
        kpt = np.array(list(map(float, kdict["K-POINT_COORDS"]["#text"].split())))

        eigfname = Path(savedir) / kdict["DATAFILE"]["@iotk_link"]
        with eigfname.open() as f:
            edict = xmltodict.parse(f)

        eigs_Ha = np.array(list(map(float, edict["Root"]["EIGENVALUES"]["#text"].split())))

        kpoints.append(kpt)
        eigs.append(eigs_Ha)

    return np.array(kpoints), np.array(eigs)
