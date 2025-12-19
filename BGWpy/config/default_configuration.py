"""Default configuration for BGWpy.

These are the original defaults.
Do not modify these by hand. Use the user_configuration file instead.
"""

from __future__ import annotations

from typing import TypedDict


class MPIConfig(TypedDict, total=False):
    """Configuration for MPI execution."""

    mpirun: str
    nproc: int
    nproc_flag: str
    nproc_per_node: int
    nproc_per_node_flag: str
    nodes: int | None
    nodes_flag: str | None


class RunscriptConfig(TypedDict, total=False):
    """Configuration for run scripts."""

    first_line: str
    header: list[str]
    footer: list[str]


class FlavorsConfig(TypedDict, total=False):
    """Configuration for code flavors and options."""

    use_hdf5: bool
    use_hdf5_qe: bool
    flavor_complex: bool
    dft_flavor: str


default_mpi: MPIConfig = {
    "mpirun": "mpirun",
    "nproc": 1,
    "nproc_flag": "-n",
    "nproc_per_node": 1,
    "nproc_per_node_flag": "--npernode",
    "nodes": None,
    "nodes_flag": None,
}

default_runscript: RunscriptConfig = {
    "first_line": "#!/bin/bash",
    "header": [],
    "footer": [],
}

flavors: FlavorsConfig = {
    "use_hdf5": True,
    "use_hdf5_qe": False,
    "flavor_complex": True,
    "dft_flavor": "espresso",
}
