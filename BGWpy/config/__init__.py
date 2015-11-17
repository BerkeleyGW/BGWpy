
from .default_configuration import (
    default_mpi,
    default_runscript,
    )

# The user configuration file is used
# to override the default configuration.
import os
try:
    if 'user_configuration.py' in  os.listdir(os.path.dirname(__file__)):
        from . import user_configuration

        if 'default_mpi' in dir(user_configuration):
            default_mpi.update(user_configuration.default_mpi)

        if 'default_runscript' in dir(user_configuration):
            default_runscript.update(user_configuration.default_runscript)

        if 'use_hdf5' in dir(user_configuration):
            use_hdf5 = user_configuration.use_hdf5

except Exception as e:
    import warnings
    warnings.warn('Could not process user_configuration.py:\n' + str(e))
    del warnings

del os
