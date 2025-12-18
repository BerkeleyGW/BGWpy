from __future__ import annotations

import numpy as np


def extract_inteqp_bandstructure(fname):
    """
    Extract the data in the 'bandstructure.dat' file produced by inteqp.x.

    Returns
    -------
    dict:
        nspin: int
            Number of spin components.
        nkpt: int
            Number of k-points.
        nband: int
            Number of bands.
        kpts: numpy.array(nkpt, 3), float
            k-points in cartesian coordinates.
        ib_min: int
            Index of minimum band (starting at 1 for the first occupied band).
        ib_max
            Index of maximum band.
        eigs_dft_eV: numpy.array(nspin, nkpt, nband), float
            DFT eigenvalues, in eV.
        eigs_gw_eV: numpy.array(nspin, nkpt, nband), float
            GW eigenvalues, in eV.
        delta_eigs_eV: numpy.array(nspin, nkpt, nband), float
            Difference between GW and DFT eigenvalues, in eV.
    """

    data = np.loadtxt(fname, unpack=True)

    spin = np.array(data[0], dtype=np.int64)
    band = np.array(data[1], dtype=np.int64)
    kpt = np.array(data[2:5,], dtype=np.float64).transpose()
    E_DFT = np.array(data[5], dtype=np.float64)
    E_QP = np.array(data[6], dtype=np.float64)
    DE = np.array(data[7], dtype=np.float64)

    # Find the dimensions
    ndata = len(spin)
    nspin = 1 if spin[0] == spin[-1] else 2

    ib_min, ib_max = band[0], band[-1]
    nband = ib_max - ib_min + 1

    for i, b in enumerate(band):
        if b != ib_min:
            nkpt = i
            break
    else:
        nkpt = len(kpt) // nspin

    # Construct data arrays
    eigs_dft_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
    eigs_gw_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
    delta_eigs_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)

    for i in range(ndata):
        ispin = spin[i] - 1
        ikpt = i % nkpt
        iband = band[i] - 1

        eigs_dft_eV[ispin, ikpt, iband] = E_DFT[i]
        eigs_gw_eV[ispin, ikpt, iband] = E_QP[i]
        delta_eigs_eV[ispin, ikpt, iband] = DE[i]

    return {
        "nspin": nspin,
        "nkpt": nkpt,
        "nband": nband,
        "kpts": kpt[:nkpt],
        "ib_min": ib_min,
        "ib_max": ib_max,
        "eigs_dft_eV": eigs_dft_eV,
        "eigs_gw_eV": eigs_gw_eV,
        "delta_eigs_eV": delta_eigs_eV,
    }


def extract_inteqp_eqp(fname):
    """
    Extract the data in the 'eqp.dat' file produced by inteqp.x.

    Returns
    -------
    dict:
        nspin: int
            Number of spin components.
        nkpt: int
            Number of k-points.
        nband: int
            Number of bands.
        kpts: numpy.array(nkpt, 3), float
            k-points in cartesian coordinates.
        ib_min: int
            Index of minimum band (starting at 1 for the first occupied band).
        ib_max
            Index of maximum band.
        eigs_dft_eV: numpy.array(nspin, nkpt, nband), float
            DFT eigenvalues, in eV.
        eigs_gw_eV: numpy.array(nspin, nkpt, nband), float
            GW eigenvalues, in eV.
        delta_eigs_eV: numpy.array(nspin, nkpt, nband), float
            Difference between GW and DFT eigenvalues, in eV.
    """

    with open(fname) as f:
        # Read the first block to compute the dimensions
        line = next(f)
        parts = line.split()
        nstates = int(parts[3])
        spins = []
        bands = []
        for _ in range(nstates):
            line = next(f)
            parts = line.split()
            spins.append(int(parts[0]))
            bands.append(int(parts[1]))

        ib_min = min(bands)
        ib_max = max(bands)
        nspin = max(spins)
        nband = nstates // nspin

        # Count the remaining lines
        nlines = nstates + 1
        while True:
            try:
                line = next(f)
                nlines += 1
            except StopIteration:
                break

        nkpt = nlines // (nstates + 1)

        kpts = np.zeros((nkpt, 3), dtype=np.float64)
        eigs_dft_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)
        eigs_gw_eV = np.zeros((nspin, nkpt, nband), dtype=np.float64)

        # Rewind file to start
        f.seek(0)

        for ikpt in range(nkpt):
            line = next(f)
            parts = line.split()

            kpts[ikpt, :] = list(map(float, parts[:3]))

            for i in range(nstates):
                line = next(f)
                parts = line.split()

                ispin = i // nband
                iband = i % nband

                eigs_dft_eV[ispin, ikpt, iband] = float(parts[2])
                eigs_gw_eV[ispin, ikpt, iband] = float(parts[3])

    delta_eigs_eV = eigs_gw_eV - eigs_dft_eV

    return {
        "nspin": nspin,
        "nkpt": nkpt,
        "nband": nband,
        "kpts": kpts,
        "ib_min": ib_min,
        "ib_max": ib_max,
        "eigs_dft_eV": eigs_dft_eV,
        "eigs_gw_eV": eigs_gw_eV,
        "delta_eigs_eV": delta_eigs_eV,
    }
