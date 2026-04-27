"""Degeneracy check task for BerkeleyGW.

This module provides the DegeneracyCheckTask class, which wraps the
degeneracy_check.x executable from BerkeleyGW to check for degenerate
bands at a given k-point in a wavefunction file.
"""

import re
import subprocess
from pathlib import Path
from typing import Any, TypedDict

from BGWpy.core import Task

__all__ = ["DegeneracyCheckResult", "DegeneracyCheckTask"]


class DegeneracyCheckResult(TypedDict):
    """Result of a degeneracy check calculation.

    Attributes
    ----------
    n_spins : int
        Number of spins in the wavefunction.
    n_bands : int
        Number of bands in the wavefunction.
    n_kpoints : int
        Number of k-points in the wavefunction.
    allowed_bands : list[int]
        Degeneracy-allowed numbers of bands (for epsilon and sigma).
    allowed_valence_bands : list[int]
        Degeneracy-allowed numbers of valence bands (for inteqp, kernel, and absorption).
    allowed_conduction_bands : list[int]
        Degeneracy-allowed numbers of conduction bands (for inteqp, kernel, and absorption).
    """

    n_spins: int
    n_bands: int
    n_kpoints: int
    allowed_bands: list[int]
    allowed_valence_bands: list[int]
    allowed_conduction_bands: list[int]


class DegeneracyCheckTask(Task):
    """Task for running the degeneracy_check.x BerkeleyGW utility.

    This task executes degeneracy_check.x on a given wavefunction file
    and parses the output to determine the allowed numbers of bands
    that respect degeneracy rules.

    Attributes
    ----------
    executable : str
        Path to the degeneracy_check.x executable.

    Properties
    ----------
    out_fname : str
        Absolute path to the output file (degeneracy_check.out).
    wfn_fname : str
        Relative path to the wavefunction file to check.
    """

    _wfn_fname: str
    executable: str

    def __init__(self, dirname: str | Path, **kwargs: Any) -> None:
        """
        Initialize a DegeneracyCheckTask.

        Parameters
        ----------
        dirname : str | Path, default="./"
            Main directory from which the scripts are executed.
        wfn_fname : str, default="WFN"
            Relative path to the wavefunction file to check for degeneracies.
        **kwargs
            Additional keyword arguments. Can include 'executable' to specify
            a custom path to the degeneracy_check.x executable.
        """
        self._wfn_fname = kwargs.get("wfn_fname", "WFN")
        self.executable = kwargs.get("executable", "degeneracy_check.x")
        super().__init__(dirname, **kwargs)

    def write(self) -> None:
        """Write the task files to disk.

        Raises
        ------
        NotImplementedError
            Always raised, as this task does not write any files.
        """
        msg = "DegeneracyCheckTask does not write any files to disk."
        raise NotImplementedError(msg)

    def run(self) -> None:
        """Run the degeneracy check.

        Executes degeneracy_check.x on the specified wavefunction file
        and writes the output to degeneracy_check.out in the task directory.

        Raises
        ------
        FileNotFoundError
            If the specified wavefunction file does not exist.
        OSError
            If the executable cannot be found or execution fails.
        """
        wfn_path = Path(self.dirname) / self.wfn_fname
        if not wfn_path.exists():
            msg = f"Wavefunction file not found: {wfn_path}"
            raise FileNotFoundError(msg)

        try:
            print(f"Running {self.executable} ...")
            with self.exec_from_dirname():
                result = subprocess.run(
                    [self.executable, self.wfn_fname], capture_output=True, check=True
                )
        except OSError as err:
            msg = f"""
            {err!s}

            {self.executable} executable not found.

            Please ensure that either the 'bin' directory of your BerkeleyGW installation is in your PATH environment variable, or that you have loaded the appropriate module on your computing cluster (e.g., 'module load berkeleygw').
            """

            raise OSError(msg) from err

        Path(self.out_fname).write_text(result.stdout.decode())

    def parse_output(self) -> DegeneracyCheckResult:
        """Parse the output of the degeneracy check.

        Returns
        -------
        DegeneracyCheckResult
            A dictionary containing the number of spins, bands, k-points,
            and the degeneracy-allowed numbers of bands for various calculations.
        """
        output_text = Path(self.out_fname).read_text()

        result: DegeneracyCheckResult = {
            "n_spins": 0,
            "n_bands": 0,
            "n_kpoints": 0,
            "allowed_bands": [],
            "allowed_valence_bands": [],
            "allowed_conduction_bands": [],
        }

        error_msg = "Unexpected output format in degeneracy_check.out. Unable to parse results."

        spins_match = re.search(r"Number of spins:\s+(\d+)", output_text)
        if spins_match:
            result["n_spins"] = int(spins_match.group(1))
        else:
            raise ValueError(error_msg)

        bands_match = re.search(r"Number of bands:\s+(\d+)", output_text)
        if bands_match:
            result["n_bands"] = int(bands_match.group(1))
        else:
            raise ValueError(error_msg)

        kpoints_match = re.search(r"Number of k-points:\s+(\d+)", output_text)
        if kpoints_match:
            result["n_kpoints"] = int(kpoints_match.group(1))
        else:
            raise ValueError(error_msg)

        current_section = None
        for raw_line in output_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("== Degeneracy-allowed numbers of bands"):
                current_section = "allowed_bands"
            elif line.startswith("== Degeneracy-allowed numbers of valence bands"):
                current_section = "allowed_valence_bands"
            elif line.startswith("== Degeneracy-allowed numbers of conduction bands"):
                current_section = "allowed_conduction_bands"
            elif (current_section is not None) and line.isdigit():
                result[current_section].append(int(line))

        return result

    @property
    def out_fname(self) -> str:
        """Get the absolute path to the output file."""
        return str(Path(self.dirname) / "degeneracy_check.out")

    @property
    def wfn_fname(self) -> str:
        """Get the relative path to the wavefunction file."""
        return self._wfn_fname
