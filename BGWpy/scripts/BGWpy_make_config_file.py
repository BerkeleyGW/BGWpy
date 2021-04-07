#!/usr/bin/env python
import configparser                                                                                                                                              
config = configparser.ConfigParser()

config['flavors'] = dict(
    use_hdf5 = True,
    use_hdf5_qe = False,
    flavor_complex = True,
    dft_flavor = 'espresso',
    )

config['MPI'] = dict(
    mpirun = 'mpirun',
    nproc = 1,
    nproc_flag = '-n',
    nproc_per_node = 1,
    nproc_per_node_flag = '--npernode',
    nodes = '',
    nodes_flag = '',
    )

config['runscript'] = dict(
    first_line = '#!/bin/sh',
    header = """
# Lines before execution
""",
    footer = """
# Lines after execution
""",
    )

header = """\
; Configuration file for BGWpy
; This file should be saved as ~/.BGWpyrc
;
; Lines starting with "#" will be included in the shell scripts.
; Entries in header and footer should be expanded or removed by the user.

"""

if __name__ == '__main__':
    import sys
    import os
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-f', dest='force', action='store_true',
                        help='Overwrite existing file')
    args = parser.parse_args()

    fname = os.path.join(os.environ['HOME'], '.BGWpyrc')
    if os.path.exists(fname):
        if not args.force:
            import warnings
            warnings.warn('Cannot overwrite existing file ~/.BGWpyrc. Use -f to overwrite')
            sys.exit(1)

    print('Writing ~/.BGWpyrc')
    with open(fname, 'w') as cf:
      cf.write(header)
      config.write(cf)
