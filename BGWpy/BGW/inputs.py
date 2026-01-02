from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any

import numpy as np

from BGWpy.core import BasicInputFile

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import ArrayLike, NDArray


class EpsilonInput(BasicInputFile):
    q0: NDArray[np.float64]
    qpts: list[NDArray[np.float64]]

    def __init__(
        self,
        ecuteps: float,
        q0: ArrayLike,
        qpts: Sequence[ArrayLike],
        *keywords: str,
        **variables: Any,
    ) -> None:
        all_variables = OrderedDict(
            [
                ("epsilon_cutoff", ecuteps),
            ]
        )

        all_variables.update(variables)

        super().__init__(all_variables, keywords)

        self.q0 = np.asarray(q0)
        self.qpts = [np.asarray(q) for q in qpts]

    def __str__(self) -> str:
        qpt_block = "\nbegin qpoints\n"
        for q0i in self.q0:
            qpt_block += f" {q0i:11.8f}"
        qpt_block += " 1.0 1\n"

        for q in self.qpts:
            for qi in q:
                qpt_block += f" {qi:11.8f}"
            qpt_block += " 1.0 0\n"
        qpt_block += "end\n"

        return super().__str__() + qpt_block


class SigmaInput(BasicInputFile):
    kpts: list[NDArray[np.float64]]
    qpts: list[NDArray[np.float64]]
    ngqpt: Sequence[int]

    def __init__(
        self,
        ibnd_min: int,
        ibnd_max: int,
        kpts: Sequence[ArrayLike],
        *keywords: str,
        **variables: Any,
    ) -> None:
        all_variables = OrderedDict(
            [
                ("band_index_min", ibnd_min),
                ("band_index_max", ibnd_max),
            ]
        )

        # Handle q-points
        self.qpts = variables.pop("qpts", [])
        for key in ("ngqpt", "qgrid"):
            if key in variables:
                self.ngqpt = variables.pop(key)
                break
        else:
            if self.qpts:
                msg = (
                    "When qpts is specified, the qpoint grid must also be specified "
                    "through 'ngqpt' or 'qgrid'."
                )
                raise Exception(msg)

        all_variables.update(variables)

        super().__init__(all_variables, keywords)

        self.kpts = [np.asarray(k) for k in kpts]

    def __str__(self) -> str:
        S = super().__str__()

        kpt_block = "\nbegin kpoints\n"
        for k in self.kpts:
            for ki in k:
                kpt_block += f" {ki:11.8f}"
            kpt_block += " 1.0\n"
        kpt_block += "end\n"

        S += kpt_block

        if self.qpts:
            qpt_block = "\nbegin qpoints\n"
            for q in self.qpts:
                for qi in q:
                    qpt_block += f" {qi:11.8f}"

                if all(np.isclose(q, 0.0)):
                    qpt_block += " 1.0 1\n"
                else:
                    qpt_block += " 1.0 0\n"
            qpt_block += "end\n"
            qpt_block += "qgrid {} {} {}\n".format(*self.ngqpt)

            S += qpt_block

        return S


class KernelInput(BasicInputFile):
    def __init__(
        self,
        nbnd_val: int,
        nbnd_cond: int,
        *keywords: str,
        **variables: Any,
    ) -> None:
        all_variables = OrderedDict(
            [
                ("number_val_bands", nbnd_val),
                ("number_cond_bands", nbnd_cond),
            ]
        )

        all_variables.update(variables)

        super().__init__(all_variables, keywords)


class AbsorptionInput(BasicInputFile):
    def __init__(
        self,
        nbnd_val_co: int,
        nbnd_cond_co: int,
        nbnd_val_fi: int,
        nbnd_cond_fi: int,
        *keywords: str,
        **variables: Any,
    ) -> None:
        all_variables = OrderedDict(
            [
                ("number_val_bands_coarse", nbnd_val_co),
                ("number_val_bands_fine", nbnd_val_fi),
                ("number_cond_bands_coarse", nbnd_cond_co),
                ("number_cond_bands_fine", nbnd_cond_fi),
                ("energy_resolution", 0.1),
            ]
        )

        all_variables.update(variables)

        super().__init__(all_variables, keywords)
