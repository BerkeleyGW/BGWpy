"""Workflow to perform GW calculation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

from BGWpy.BGW import EpsilonTask, SigmaTask
from BGWpy.config import check_dft_flavor, flavors, is_dft_flavor_abinit, is_dft_flavor_espresso
from BGWpy.core import Workflow

__all__ = ["GWFlow"]


class GWFlow(Workflow):
    """
    A one-shot GW workflow made of the following tasks:
        - DFT charge density, wavefunctions and eigenvalues
        - Dielectric Matrix (Epsilon and Epsilon^-1)
        - Self-energy (Sigma)
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Keyword arguments
        -----------------
        (All mandatory unless specified otherwise)

        dirname : str | Path
            Directory in which the files are written and the code is executed.
            Will be created if needed.
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        dft_flavor : 'espresso' | 'abinit'
            Choice of DFT code for density and wavefunctions calculations.
        prefix : str
            Prefix required by QE as a rootname.
        pseudo_dir : str
            Directory in which pseudopotential files are found.
        pseudos : list, str
            Pseudopotential files.
        ngkpt : list(3), float
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float
            Q-point used to treat the Gamma point.
        nbnd : int
            Number of bands to be computed.
        ecutwfc : float
            Energy cutoff for the wavefunctions
        ecuteps : float
            Energy cutoff for the dielectric function.
        ibnd_min : int
            Minimum band index for GW corrections.
        ibnd_max : int
            Maximum band index for GW corrections.
        truncation_flag : str, optional
            Which truncation flag to use in BerkeleyGW, e.g. "cell_slab_truncation".
        sigma_kpts : list of list(3), optional
            K-points to evaluate self-energy operator. Defaults to all
            k-points defined by the Monkhorst-Pack grid ngkpt.
        epsilon_extra_lines : list, optional
            Any other lines that should appear in the epsilon input file.
        epsilon_extra_variables : dict, optional
            Any other variables that should be declared in the epsilon input file.
        sigma_extra_lines : list, optional
            Any other lines that should appear in the sigma input file.
        sigma_extra_variables : dict, optional
            Any other variables that should be declared in the sigma input file.

        """
        super().__init__(**kwargs)

        kwargs.pop("dirname", None)

        self.structure = kwargs["structure"]
        self.ngkpt = kwargs.pop("ngkpt")
        self.kshift = kwargs.pop("kshift", [0.0, 0.0, 0.0])
        self.qshift = kwargs.pop("qshift", [0.0, 0.0, 0.0])

        nband_aliases = ("nbnd", "nband")
        for key in nband_aliases:
            if key in kwargs:
                self.nbnd = kwargs.pop(key)
                break
        else:
            msg = f"Number of bands must be specified with one of these keywords: {nband_aliases}."
            raise ValueError(msg)

        self.dft_flavor = check_dft_flavor(kwargs.get("dft_flavor", flavors["dft_flavor"]))

        # ==== DFT calculations ==== #

        # Quantum Espresso flavor
        if is_dft_flavor_espresso(self.dft_flavor):
            fnames = self.make_dft_tasks_espresso(**kwargs)
            kwargs.update(fnames)

        # Abinit flavor
        elif is_dft_flavor_abinit(self.dft_flavor):
            fnames = self.make_dft_tasks_abinit(**kwargs)
            kwargs.update(fnames)

        # ==== GW calculations ==== #

        # some common variables for Epsilon and Sigma
        self.epsilon_extra_lines = kwargs.pop("epsilon_extra_lines", [])
        self.epsilon_extra_variables = kwargs.pop("epsilon_extra_variables", {})

        self.sigma_extra_lines = kwargs.pop("sigma_extra_lines", [])
        self.sigma_extra_variables = kwargs.pop("sigma_extra_variables", {})

        # Dielectric matrix computation and inversion (epsilon)
        self.epsilontask = EpsilonTask(
            dirname=str(Path(self.dirname) / "11-epsilon"),
            ngkpt=self.ngkpt,
            qshift=self.qshift,
            extra_lines=self.epsilon_extra_lines,
            extra_variables=self.epsilon_extra_variables,
            **kwargs,
        )

        # Self-energy calculation (sigma)
        self.sigmatask = SigmaTask(
            dirname=str(Path(self.dirname) / "12-sigma"),
            ngkpt=self.ngkpt,
            extra_lines=self.sigma_extra_lines,
            extra_variables=self.sigma_extra_variables,
            eps0mat_fname=self.epsilontask.eps0mat_fname,
            epsmat_fname=self.epsilontask.epsmat_fname,
            **kwargs,
        )

        self.add_tasks([self.epsilontask, self.sigmatask], merge=False)

        truncation_flag_value = kwargs.get("truncation_flag")
        if truncation_flag_value is not None:
            self.truncation_flag = truncation_flag_value

        sigma_kpts_value = kwargs.get("sigma_kpts")
        if sigma_kpts_value is not None:
            self.sigma_kpts = sigma_kpts_value

    @property
    def has_kshift(self) -> bool:
        return any(i != 0 for i in self.kshift)

    @property
    def sigma_kpts(self) -> list[NDArray[np.float64]]:
        return self.sigmatask.input.kpts

    @sigma_kpts.setter
    def sigma_kpts(self, value: list[NDArray[np.float64]]) -> None:
        if value:
            self.sigmatask.input.kpts = value

    _truncation_flag = ""

    @property
    def truncation_flag(self) -> str:
        return self._truncation_flag

    @truncation_flag.setter
    def truncation_flag(self, value: str) -> None:
        for task in (self.epsilontask, self.sigmatask):
            # Remove old value
            if self._truncation_flag in task.input.keywords:
                i = task.input.keywords.index(self._truncation_flag)
                del task.input.keywords[i]

            # Add new value
            if value:
                task.input.keywords.append(value)

        self._truncation_flag = value

    def make_dft_tasks_espresso(self, **kwargs: Any) -> dict[str, str]:
        """
        Initialize all DFT tasks using Quantum Espresso.
        Return a dictionary of file names.
        """
        from BGWpy.QE import QeBgwFlow, QeScfTask

        if "charge_density_fname" in kwargs:
            if "data_file_fname" not in kwargs:
                msg = "Error, when providing charge_density_fname, data_file_fname is required."
                raise ValueError(msg)

        else:
            self.scftask = QeScfTask(
                dirname=str(Path(self.dirname) / "01-density"),
                ngkpt=self.ngkpt,
                kshift=self.kshift,
                **kwargs,
            )

            self.add_task(self.scftask)

            kwargs.update(
                charge_density_fname=self.scftask.charge_density_fname,
                data_file_fname=self.scftask.data_file_fname,
                spin_polarization_fname=self.scftask.spin_polarization_fname,
                ekin_density_fname=self.scftask.ekin_density_fname,
            )

        # Wavefunction tasks for Epsilon
        self.wfntask_ksh = QeBgwFlow(
            dirname=str(Path(self.dirname) / "02-wfn"),
            ngkpt=self.ngkpt,
            kshift=self.kshift,
            nbnd=self.nbnd,
            rhog_flag=True,
            **kwargs,
        )

        self.wfntask_qsh = QeBgwFlow(
            dirname=str(Path(self.dirname) / "03-wfnq"),
            ngkpt=self.ngkpt,
            kshift=self.kshift,
            qshift=self.qshift,
            nbnd=None,
            **kwargs,
        )

        self.add_tasks([self.wfntask_ksh, self.wfntask_qsh])

        # Unshifted wavefunction tasks for Sigma
        # only if not already computed for Epsilon.
        if self.has_kshift:
            self.wfntask_ush = QeBgwFlow(
                dirname=str(Path(self.dirname) / "04-wfn_co"),
                ngkpt=self.ngkpt,
                nbnd=self.nbnd,
                rhog_flag=True,
                **kwargs,
            )

            self.add_task(self.wfntask_ush)

        else:
            self.wfntask_ush = self.wfntask_ksh

        return {
            "wfn_fname": self.wfntask_ksh.wfn_fname,
            "wfnq_fname": self.wfntask_qsh.wfn_fname,
            "wfn_co_fname": self.wfntask_ush.wfn_fname,
            "rho_fname": self.wfntask_ush.rho_fname,
            "vxc_dat_fname": self.wfntask_ush.vxc_dat_fname,
        }

    def make_dft_tasks_abinit(self, **kwargs: Any) -> dict[str, str]:
        """
        Initialize all DFT tasks using Abinit.
        Return a dictionary of file names.
        """
        from BGWpy.Abinit import AbinitBgwFlow, AbinitScfTask

        # Either charge density is provided or an SCF task is initialized.
        if "charge_density_fname" in kwargs:
            if "vxc_fname" not in kwargs:
                msg = "Error, when providing charge_density_fname, vxc_fname is required"
                raise ValueError(msg)

        else:
            self.scftask = AbinitScfTask(
                dirname=str(Path(self.dirname) / "01-density"),
                ngkpt=self.ngkpt,
                kshift=self.kshift,
                **kwargs,
            )

            self.add_task(self.scftask)

            kwargs.update(
                charge_density_fname=self.scftask.charge_density_fname,
                vxc_fname=self.scftask.vxc_fname,
            )

        # Option to split the wfn calculation in two calculations,
        # where the first one has fewer bands and higher convergence criterion
        self.split_wfn = kwargs.pop("split_wfn", False)

        # Should the WFN be computed, or are they provided?
        self.with_wfn = kwargs.get("with_wfn", True)

        if "wfn_fname" in kwargs:
            self.with_wfn = False
            wfn_fname = kwargs["wfn_fname"]
        elif not self.with_wfn:
            msg = "When with_wfn=False, wfn_fname must be provided"
            raise ValueError(msg)

        if "wfnq_fname" in kwargs:
            wfnq_fname = kwargs["wfnq_fname"]
        elif not self.with_wfn:
            msg = "When with_wfn=False, wfnq_fname is also required"
            raise ValueError(msg)

        if "wfn_co_fname" in kwargs:
            wfn_co_fname = kwargs["wfn_co_fname"]
        elif not self.with_wfn:
            msg = "When with_wfn=False, wfn_co_fname is also required"
            raise ValueError(msg)

        if "rho_fname" in kwargs:
            rho_fname = kwargs["rho_fname"]
        elif not self.with_wfn:
            msg = "When with_wfn=False, rho_fname is required"
            raise ValueError(msg)

        if "vxc_fname" in kwargs:
            vxc_fname = kwargs["vxc_fname"]
        elif not self.with_wfn:
            msg = "When with_wfn=False, vxc_fname is required"
            raise ValueError(msg)

        # In case wavefunctions are already provided
        if not self.with_wfn:
            return {
                "wfn_fname": wfn_fname,
                "wfnq_fname": wfnq_fname,
                "wfn_co_fname": wfn_co_fname,
                "rho_fname": rho_fname,
                "vxc_fname": vxc_fname,
            }

        # number of bands and bands in the buffer,
        # specially for cases in which calculation is split into two parts.
        nbnd = self.nbnd
        if self.split_wfn:
            nbnd = kwargs.pop("nband1")

        # Wavefunction tasks for Epsilon
        self.wfntask_ksh = AbinitBgwFlow(
            dirname=str(Path(self.dirname) / "02-wfn"),
            ngkpt=self.ngkpt,
            kshift=self.kshift,
            nband=nbnd,
            rhog_flag=True,
            **kwargs,
        )

        self.wfntask_qsh = AbinitBgwFlow(
            dirname=str(Path(self.dirname) / "03-wfnq"),
            ngkpt=self.ngkpt,
            kshift=self.kshift,
            qshift=self.qshift,
            nband=None,
            **kwargs,
        )

        self.add_tasks([self.wfntask_ksh, self.wfntask_qsh])

        # Add additional WFN task if required
        if self.split_wfn:
            nbdbuf = int(self.nbnd * 0.2)  # 20% of bands are in buffer
            self.wfntask_large = AbinitBgwFlow(
                dirname=str(Path(self.dirname) / "02-wfn-large"),
                ngkpt=self.ngkpt,
                kshift=self.kshift,
                nband=self.nbnd,
                nbdbuf=nbdbuf,
                tolwfr="1.d-05",
                irdwfk=1,
                input_wavefunction_fname=self.wfntask_ksh.wfn_fname,
                **kwargs,
            )

        # Unshifted wavefunction tasks for Sigma
        # only if not already computed for Epsilon.
        if self.has_kshift:
            self.wfntask_ush = AbinitBgwFlow(
                dirname=str(Path(self.dirname) / "04-wfn_co"),
                ngkpt=self.ngkpt,
                nband=self.nbnd,
                rhog_flag=True,
                vxcg_flag=True,
                **kwargs,
            )

            self.add_task(self.wfntask_ush)

        else:
            self.wfntask_ush = self.wfntask_ksh

        if self.split_wfn:
            if self.has_kshift:
                msg = "Cannot use split_wfn with a k-shift at the moment (to be fixed)"
                raise NotImplementedError(msg)

            fnames = {
                "wfn_fname": self.wfntask_large.wfn_fname,
                "wfnq_fname": self.wfntask_qsh.wfn_fname,
                "wfn_co_fname": self.wfntask_large.wfn_fname,
                "rho_fname": self.wfntask_large.rho_fname,
                "vxc_fname": self.wfntask_large.vxc_fname,
            }
        else:
            fnames = {
                "wfn_fname": self.wfntask_ksh.wfn_fname,
                "wfnq_fname": self.wfntask_qsh.wfn_fname,
                "wfn_co_fname": self.wfntask_ush.wfn_fname,
                "rho_fname": self.wfntask_ush.rho_fname,
                "vxc_fname": self.wfntask_ush.vxc_fname,
            }

        return fnames
