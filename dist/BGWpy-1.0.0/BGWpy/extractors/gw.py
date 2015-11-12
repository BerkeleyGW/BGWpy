import os
import pickle

from .. import parse_sigma_output


def extract_multiple_GW_results(dirnames):
    """Extract GW results from a list of directories."""
    data = dict()
    data['variables'] = list()
    data['results'] = list()
    data['ndata'] = len(dirnames)

    for dname in dirnames:

        with open(os.path.join(dname, 'variables.pkl'), 'read') as f:
            variables = pickle.load(f)

        with open(os.path.join(dname, 'sigma.out'), 'read') as f:
            out = parse_sigma_output(f)

        data['variables'].append(variables)
        data['results'].append(out)

    return data

