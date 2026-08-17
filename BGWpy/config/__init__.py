from __future__ import annotations

import configparser

# The user configuration file is used
# to override the default configuration.
import os
from pathlib import Path

from .default_configuration import (
    default_mpi,
    default_runscript,
    flavors,
)

config_file = Path.home() / ".BGWpyrc"
if Path(config_file).exists():
    config = configparser.ConfigParser(comment_prefixes=(";"))
    config.read(config_file)

    sk = "flavors"
    keys = ("use_hdf5", "use_hdf5_qe", "flavor_complex")
    if sk in config:
        for key in keys:
            if key in config[sk]:
                bool_value = config[sk].getboolean(key)
                flavors[key] = bool_value  # type: ignore[typeddict-item]

    keys = ("dft_flavor",)
    if sk in config:
        for key in keys:
            if key in config[sk]:
                flavors[key] = config[sk][key]

    sk = "MPI"
    keys = (
        "mpirun",
        "nproc",
        "nproc_flag",
        "nproc_per_node",
        "nproc_per_node_flag",
        "nodes",
        "nodes_flag",
    )
    if sk in config:
        for key in keys:
            if key in config[sk]:
                value = config[sk][key]
                # Convert string values to appropriate types
                if key in ("nproc", "nproc_per_node", "nodes"):
                    default_mpi[key] = int(value) if value else None  # type: ignore[assignment]
                else:
                    default_mpi[key] = value  # type: ignore[assignment]

    sk = "runscript"
    keys = ("first_line", "header", "footer", "fix_cpu_affinity")
    if sk in config:
        for key in keys:
            if key in config[sk]:
                value = config[sk][key]
                # Convert string values to appropriate types
                if key in ("header", "footer"):
                    # Split on newlines to convert to list
                    default_runscript[key] = value.split("\n") if value else []  # type: ignore[assignment]
                elif key == "fix_cpu_affinity":
                    default_runscript[key] = config[sk].getboolean(key)  # type: ignore[typeddict-item]
                else:
                    default_runscript[key] = value  # type: ignore[assignment]

    del sk, keys

else:
    import warnings

    warnings.warn(
        "Did not find user configuration file ~/.BGWpyrc. "
        "Try running 'python -m BGWpy' to create one.",
        stacklevel=2,
    )
    del warnings


del os

from .dft_flavors import *
