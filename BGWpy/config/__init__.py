
from .default_configuration import (
    default_mpi,
    default_runscript,
    flavors,
    )

# The user configuration file is used
# to override the default configuration.
import os
import configparser
config_file = os.path.join(os.environ['HOME'], '.BGWpyrc')
if os.path.exists(config_file):
    config = configparser.ConfigParser(comment_prefixes=(';'))                      
    config.read(config_file)

    sk = 'flavors'
    keys = ('use_hdf5', 'use_hdf5_qe', 'flavor_complex', 'dft_flavor')
    if sk in config:
        for key in keys:
            if key in config[sk]:
                flavors[key] = config[sk][key]

    sk = 'MPI'
    keys = ('mpirun', 'nproc', 'nproc_flag',
            'nproc_per_node', 'nproc_per_node_flag',
            'nodes', 'nodes_flag')
    if sk in config:
        for key in keys:
            if key in config[sk]:
                default_mpi[key] = config[sk][key]

    sk = 'runscript'
    keys = ('first_line', 'header', 'footer')
    if sk in config:
        for key in keys:
            if key in config[sk]:
                default_runscript[key] = config[sk][key]

    del sk, keys

else:
    import warnings
    warnings.warn('Did not find user configuration file ~/.BGWpyrc. '
                  'Try running the script BGWpy_make_config_file.py')
    del warnings


del os

from .dft_flavors import *
