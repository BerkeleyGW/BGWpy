from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

__all__ = ["get_kpt_variables", "get_scf_variables", "get_wfn_variables"]


def get_kpt_variables(**kwargs: Any) -> dict[str, Any]:
    """Extract the variables to declare the k-points grid."""

    variables: dict[str, Any] = {}

    if "kpt" in kwargs:
        kpt: NDArray[np.floating[Any]] = np.array(kwargs["kpt"]).reshape((-1, 3))
        variables["kptopt"] = 0
        variables["kpt"] = kpt
        variables["nkpt"] = len(kpt)
        variables["wtk"] = kwargs["wtk"]

    elif "ngkpt" in kwargs:
        variables["ngkpt"] = kwargs["ngkpt"]
        variables["kptopt"] = kwargs.get("kptopt", 1)

        shiftk: NDArray[np.floating[Any]] = np.array(kwargs.get("shiftk", 3 * [0.0])).reshape(
            (-1, 3)
        )
        variables["shiftk"] = shiftk
        variables["nshiftk"] = len(shiftk)

    return variables


def get_scf_variables(**kwargs: Any) -> dict[str, Any]:
    """Return a dict of variables required for an SCF calculation."""
    return {
        "prtden": 1,
        "prtvxc": 1,
        "tolvrs": kwargs.get("tolvrs", 1e-10),
        "ecut": kwargs.get("ecut"),
    }


def get_wfn_variables(**kwargs: Any) -> dict[str, Any]:
    """Return a dict of variables required for an SCF calculation."""
    return {
        "irdden": 1,
        "nband": kwargs.get("nband"),
        "ecut": kwargs.get("ecut"),
        "tolwfr": kwargs.get("tolwfr", 1e-14),
        "iscf": kwargs.get("iscf", -3),
        "istwfk": kwargs.get("istwfk", "*1"),
    }
