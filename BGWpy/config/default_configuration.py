# These are the original defaults.
# Do not modify these by hand. Use the user_configuration file instead.

default_mpi = dict(
    mpirun = 'mpirun',
    nproc = 1,
    nproc_flag = '-n',
    nproc_per_node = 1,
    nproc_per_node_flag = '--npernode',
    nodes = None,
    nodes_flag = None,
    )

default_runscript = dict(
    first_line = '#!/bin/bash',
    header = [],
    footer = [],
    )

flavors = dict(
    use_hdf5 = True,
    use_hdf5_qe = False,
    flavor_complex = True,
    dft_flavor = 'espresso',
    )
