import os
import pickle

import numpy as np


def parse_sigma_output(f):
    """
    Extract the GW results of a calculation with BerkeleyGW.

    Returns
    -------

    dict :
        nspin : int
            Number of spins
        nkpt : int
            Number of k-points
        nband : int
            Number of bands
        kpt : array[nkpt, 3]
            K-points wavevectors (reduced coord)
        n : array[nband]
            band indices
        elda : array[nspin, nkpt, nband]
            energy eigenvalue
        ecor : array[nspin, nkpt, nband]
            corrected energy eigenvalue
        x : array[nkpt, nband]
            bare exchange
        sx-x : array[nspin, nkpt, nband]
            sx = screened exchange at energy ecor
        ch : array[nspin, nkpt, nband]
            coulomb hole at energy ecor
        sig : array[nspin, nkpt, nband]
            sx + ch = self-energy at energy ecor
        vxc : array[nspin, nkpt, nband]
            vxc = exchange-correlation potential
        eqp0 : array[nspin, nkpt, nband]
            elda - vxc + sig(ecor)
        eqp1 : array[nspin, nkpt, nband]
            eqp0 + (dsig/de) / (1 - dsig/de) * (eqp0 - ecor)
        Znk array[nspin, nkpt, nband]
            quasiparticle renormalization factor
    """

    if isinstance(f, str):
        with open(f, 'r') as fi:
            return parse_sigma_output(fi)

    # Break the output into large kpoint block.
    large_kpt_blocks = break_output_in_kpt_blocks(f)

    # Count k-points from number of kpt blocks
    nkpt = len(large_kpt_blocks)


    # Break the blocks into smaller kpt and spin block
    kpt_spin_blocks = list()
    for block in large_kpt_blocks:
        subblock = break_kpt_spin_blocks(block)
        kpt_spin_blocks.extend(subblock)

    # Count spins from number of sub-blocks
    nspin = len(subblock)


    # Parse each block
    block_results = list()
    for block in kpt_spin_blocks:
        block_result = parse_sigma_output_block(block)
        block_results.append(block_result)

    # Count number of bands from the lines of last block
    nband = len(block_result['n'])


    # Initialize the results dict
    results = dict(nspin=nspin, nkpt=nkpt, nband=nband)

#    keys = ['elda','ecor','x','sx-x','ch','sig','vxc','eqp0','eqp1','Znk']
    keys=['Emf','Eo','Vxc','X','Cor','Eqp0','Eqp1','Znk']

    for key in keys:
        results[key] = np.zeros((nspin, nkpt, nband), dtype=np.float)

    results['kpt'] = np.zeros((nkpt,3), dtype=np.float)
    results['n'] = np.zeros(nband, dtype=np.int)


    # Merge the blocks
    for block_result in block_results:
        ispin = block_result['spin'] - 1
        ikpt = block_result['ik'] - 1
        for key in keys:
            for iband, val in enumerate(block_result[key]):
                results[key][ispin,ikpt,iband] = val

        results['kpt'][ikpt] = np.array(block_result['k'])
        results['n'] = np.array(block_result['n'], dtype=np.int)

    return results


def break_output_in_kpt_blocks(f):
    """Break the output into large kpoint block."""
    blocks = list()
    S = ''
    reading_block = False
    for line in f.readlines():

        if 'Dealing with k' in line:
            reading_block = True
            if S:
                blocks.append(S)
            S = ''

        if reading_block:
            S += line

    if S:
        blocks.append(S)

    return blocks


def break_kpt_spin_blocks(S):
    """Break a block into smaller kpt and spin blocks."""

    if not 'Symmetrized values from band-averaging' in S:
        raise Exception('Could not find symmetrized values in block:\n' + S)

    S = S.split('Symmetrized values from band-averaging')[-1]
    S = S.split('======================')[0]

    blocks = list()
    iterlines = iter(S.splitlines())
    while True:

        try:
            line = iterlines.next()
        except StopIteration:
            break

        if line.startswith('       k ='):

            lines = list()
            lines.append(line)       # kpoint line
            line = iterlines.next()  # empty line
            lines.append(line)
            line = iterlines.next()  # labels line
            while line.strip():
                lines.append(line)
                line = iterlines.next()
            blocks.append('\n'.join(lines))

    return blocks


def parse_sigma_output_block(S):
    """
    Extract the GW results of a calculation with BerkeleyGW
    from a block containing a single k-point and spin results.
    The block should be of the form

           k =  0.000000  0.000000  0.000000 ik =   1 spin = 1  
      
       n     elda     ecor        x     sx-x       ch      sig      vxc     eqp0     eqp1      Znk
       8  -13.367  -13.367  -39.235   20.589  -12.126  -30.771  -32.926  -11.213  -11.682    0.782
       9  -13.367  -13.367  -39.235   20.589  -12.126  -30.771  -32.926  -11.213  -11.682    0.782
      10  -13.365  -13.365  -37.756   20.136  -11.844  -29.464  -31.133  -11.696  -12.065    0.779
      11  -12.638  -12.638  -22.446   15.295   -9.207  -16.359  -12.714  -16.283  -15.398    0.757
      12  -12.440  -12.440  -23.654   15.693   -9.512  -17.473  -14.285  -15.627  -14.865    0.761

    with no leading or trailing empty line.

    Returns
    -------

    dict:
        nband: int
            Number of bands
        k: array[3]
            K-points wavevectors (reduced coord)
        ik: int
            index of K-point
        spin: int
            index of spin
        n: array[nband]
            band indices
        elda: array[nband]
            energy eigenvalue
        ecor: array[nband]
            corrected energy eigenvalue
        x: array[nband]
            bare exchange
        sx-x: array[nband]
            sx = screened exchange at energy ecor
        ch: array[nband]
            coulomb hole at energy ecor
        sig: array[nband]
            sx + ch = self-energy at energy ecor
        vxc: array[nband]
            vxc = exchange-correlation potential
        eqp0: array[nband]
            elda - vxc + sig(ecor)
        eqp1: array[nband]
            eqp0 + (dsig/de) / (1 - dsig/de) * (eqp0 - ecor)
        Znk array[nband]
            quasiparticle renormalization factor
    """

    results = dict()

    results_lines = S.splitlines()

    kpt_line = results_lines.pop(0)
    del results_lines[:2]

    results['k'] = np.array(list(map(float, kpt_line.split()[2:5])))
    results['ik'] = int(kpt_line.split()[7])
    results['spin'] = int(kpt_line.split()[10])

#    keys = ['n','elda','ecor','x','sx-x','ch','sig','vxc','eqp0','eqp1','Znk']
#    types = [int] + 10 * [float]

    keys=['n','Emf','Eo','Vxc','X','Cor','Eqp0','Eqp1','Znk']
    types = [int] + 8 * [float]


    for key in keys:
        results[key] = list()

    for line in results_lines:
        tokens = line.split()
        for key, typ, token in zip(keys, types, tokens):
            results[key].append(typ(token))

    return results





def extract_multiple_GW_results(dirnames):
    """Extract GW results from a list of directories."""
    data = dict()
    data['variables'] = list()
    data['results'] = list()
    data['ndata'] = len(dirnames)

    for dname in dirnames:

        with open(os.path.join(dname, 'variables.pkl'), 'r') as f:
            variables = pickle.load(f)

        with open(os.path.join(dname, 'sigma.out'), 'r') as f:
            out = parse_sigma_output(f)

        data['variables'].append(variables)
        data['results'].append(out)

    return data

