#!/usr/bin/env python
from __future__ import annotations

import configparser
from pathlib import Path


def get_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()

    config["flavors"] = {  # type: ignore[assignment]
        "use_hdf5": True,
        "use_hdf5_qe": False,
        "flavor_complex": True,
        "dft_flavor": "espresso",
    }

    config["MPI"] = {  # type: ignore[assignment]
        "mpirun": "mpirun",
        "nproc": 1,
        "nproc_flag": "-n",
        "nproc_per_node": 1,
        "nproc_per_node_flag": "--npernode",
        "nodes": "",
        "nodes_flag": "",
    }

    config["runscript"] = {  # type: ignore[assignment]
        "first_line": "#!/bin/sh",
        "header": """
# Lines before execution
""",
        "footer": """
# Lines after execution
""",
    }

    return config


def get_header() -> str:
    return """\
; Configuration file for BGWpy
; This file should be saved as ~/.BGWpyrc
;
; Lines starting with "#" will be included in the shell scripts.
; Entries in header and footer should be expanded or removed by the user.

"""


def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Create a default BGWpy user configuration file (~/.BGWpyrc)."
    )
    parser.add_argument("-f", dest="force", action="store_true", help="Overwrite existing file")
    args = parser.parse_args()

    fname = str(Path.home() / ".BGWpyrc")
    if Path(fname).exists() and not args.force:
        import warnings

        warnings.warn(
            "Cannot overwrite existing file ~/.BGWpyrc. Use -f to overwrite", stacklevel=2
        )
        sys.exit(1)

    print("Writing ~/.BGWpyrc")
    with open(fname, "w") as cf:
        cf.write(get_header())
        get_config().write(cf)


if __name__ == "__main__":
    main()
