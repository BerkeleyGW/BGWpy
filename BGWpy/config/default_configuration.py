
# These are the original defaults.
# Do not modify these by hand. Use the user_configuration file instead.

default_mpi = dict(
            nproc = 1,
            nproc_per_node = 1,
            mpirun = 'mpirun',
            nproc_flag = '-n',
            nproc_per_node_flag = '--npernode',
    )

default_runscript = dict(
    first_line = '#!/bin/bash',
    header = [],
    footer = [],
    )

use_hdf5 = True
flavor_complex = True

dft_flavor = 'espresso'
