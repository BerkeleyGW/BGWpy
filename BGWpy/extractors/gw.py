"""GW data extraction from BerkeleyGW sigma output files.

This module provides functions for reading and parsing output files from
the sigma.x program in BerkeleyGW.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO, TypedDict

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = [
    "MultipleGWResult",
    "SigmaBlockResult",
    "SigmaResult",
    "extract_multiple_GW_results",
    "parse_sigma_output",
]


class SigmaBlockResult(TypedDict):
    """Result dictionary from parsing a single sigma output block. Energies are in eV.

    Attributes
    ----------
    k : NDArray[np.float64]
        K-point wavevector (reduced coordinates), shape (3,).
    ik : int
        Index of k-point.
    spin : int
        Index of spin (1-based).
    n : list[int]
        Band indices.
    Emf : list[float]
        Mean-field energy eigenvalues.
    Eo : list[float]
        Corrected energy eigenvalues.
    Vxc : list[float]
        Exchange-correlation potential.
    X : list[float]
        Bare exchange.
    Cor : list[float]
        Correlation self-energy (sx-x + ch = self-energy at energy ecor).
    Eqp0 : list[float]
        Quasiparticle energy: elda - vxc + sig(ecor).
    Eqp1 : list[float]
        Linearized quasiparticle energy: eqp0 + (dsig/de) / (1 - dsig/de) * (eqp0 - ecor).
    Znk : list[float]
        Quasiparticle renormalization factor.
    """

    k: NDArray[np.float64]
    ik: int
    spin: int
    n: list[int]
    Emf: list[float]
    Eo: list[float]
    Vxc: list[float]
    X: list[float]
    Cor: list[float]
    Eqp0: list[float]
    Eqp1: list[float]
    Znk: list[float]


class SigmaResult(TypedDict):
    """Result dictionary from parse_sigma_output. Energies are in eV.

    Attributes
    ----------
    nspin : int
        Number of spins.
    nkpt : int
        Number of k-points.
    nband : int
        Number of bands.
    kpt : NDArray[np.float64]
        K-point wavevectors (reduced coordinates), shape (nkpt, 3).
    n : NDArray[np.int64]
        Band indices, shape (nband,).
    Emf : NDArray[np.float64]
        Mean-field energy eigenvalues, shape (nspin, nkpt, nband).
    Eo : NDArray[np.float64]
        Corrected energy eigenvalues, shape (nspin, nkpt, nband).
    Vxc : NDArray[np.float64]
        Exchange-correlation potential, shape (nspin, nkpt, nband).
    X : NDArray[np.float64]
        Bare exchange, shape (nspin, nkpt, nband).
    Cor : NDArray[np.float64]
        Correlation self-energy (sx-x + ch = self-energy at energy ecor), shape (nspin, nkpt, nband).
    Eqp0 : NDArray[np.float64]
        Quasiparticle energy: elda - vxc + sig(ecor), shape (nspin, nkpt, nband).
    Eqp1 : NDArray[np.float64]
        Linearized quasiparticle energy: eqp0 + (dsig/de) / (1 - dsig/de) * (eqp0 - ecor), shape (nspin, nkpt, nband).
    Znk : NDArray[np.float64]
        Quasiparticle renormalization factor, shape (nspin, nkpt, nband).
    """

    nspin: int
    nkpt: int
    nband: int
    kpt: NDArray[np.float64]
    n: NDArray[np.int64]
    Emf: NDArray[np.float64]
    Eo: NDArray[np.float64]
    Vxc: NDArray[np.float64]
    X: NDArray[np.float64]
    Cor: NDArray[np.float64]
    Eqp0: NDArray[np.float64]
    Eqp1: NDArray[np.float64]
    Znk: NDArray[np.float64]


class MultipleGWResult(TypedDict):
    """Result dictionary from extract_multiple_GW_results.

    Attributes
    ----------
    ndata : int
        Number of directories processed.
    variables : list[dict[str, Any]]
        List of variable dictionaries loaded from variables.pkl files.
    results : list[SigmaResult]
        List of parsed sigma results from each directory.
    """

    ndata: int
    variables: list[dict[str, Any]]
    results: list[SigmaResult]


def parse_sigma_output(f: str | Path | TextIO) -> SigmaResult:
    """Extract the GW results of a calculation with BerkeleyGW.

    Parameters
    ----------
    f : str | TextIO
        Path to sigma output file (str or Path), or an open file handle.

    Returns
    -------
    SigmaResult
        Dictionary containing:
        - nspin : int
            Number of spins.
        - nkpt : int
            Number of k-points.
        - nband : int
            Number of bands.
        - kpt : NDArray[np.float64], shape (nkpt, 3)
            K-points wavevectors (reduced coord).
        - n : NDArray[np.int64], shape (nband,)
            Band indices.
        - Emf : NDArray[np.float64], shape (nspin, nkpt, nband)
            Mean-field energy eigenvalue.
        - Eo : NDArray[np.float64], shape (nspin, nkpt, nband)
            Corrected energy eigenvalue.
        - Vxc : NDArray[np.float64], shape (nspin, nkpt, nband)
            Exchange-correlation potential.
        - X : NDArray[np.float64], shape (nspin, nkpt, nband)
            Bare exchange.
        - Cor : NDArray[np.float64], shape (nspin, nkpt, nband)
            Correlation (sx-x + ch = self-energy at energy ecor).
        - Eqp0 : NDArray[np.float64], shape (nspin, nkpt, nband)
            elda - vxc + sig(ecor).
        - Eqp1 : NDArray[np.float64], shape (nspin, nkpt, nband)
            eqp0 + (dsig/de) / (1 - dsig/de) * (eqp0 - ecor).
        - Znk : NDArray[np.float64], shape (nspin, nkpt, nband)
            Quasiparticle renormalization factor.

    Raises
    ------
    ValueError
        If no k-point blocks are found in the output file.
    """
    if isinstance(f, (str, Path)):
        with Path(f).open() as fi:
            return parse_sigma_output(fi)

    # Break the output into large kpoint block.
    large_kpt_blocks = break_output_in_kpt_blocks(f)

    if not large_kpt_blocks:
        msg = "No k-point blocks found in sigma output file"
        raise ValueError(msg)

    # Break the blocks into smaller kpt and spin block
    kpt_spin_blocks: list[str] = []
    for block in large_kpt_blocks:
        kpt_spin_blocks.extend(break_kpt_spin_blocks(block))

    # Parse each block
    block_results: list[SigmaBlockResult] = [
        parse_sigma_output_block(block) for block in kpt_spin_blocks
    ]

    if not block_results:
        msg = "No valid blocks found in sigma output"
        raise ValueError(msg)

    # Create mapping from ik values to array indices
    # (ik values may not be consecutive, e.g., 1, 2, 4)
    ik_values = sorted({br["ik"] for br in block_results})
    ik_to_index = {ik: idx for idx, ik in enumerate(ik_values)}
    nkpt = len(ik_values)

    spin_values = sorted({br["spin"] for br in block_results})
    spin_to_index = {spin: idx for idx, spin in enumerate(spin_values)}
    nspin = len(spin_values)

    # Count number of bands from the maximum lines of blocks
    nband = max(len(br["n"]) for br in block_results)

    # Initialize the results dict
    results: dict[str, Any] = {"nspin": nspin, "nkpt": nkpt, "nband": nband}

    keys = ["Emf", "Eo", "Vxc", "X", "Cor", "Eqp0", "Eqp1", "Znk"]

    for key in keys:
        results[key] = np.zeros((nspin, nkpt, nband), dtype=np.float64)

    results["kpt"] = np.zeros((nkpt, 3), dtype=np.float64)
    results["n"] = np.zeros(nband, dtype=np.int64)

    # Merge the blocks
    for block_result in block_results:
        ispin = spin_to_index[block_result["spin"]]
        ikpt = ik_to_index[block_result["ik"]]
        for key in keys:
            for iband, val in enumerate(block_result[key]):  # type: ignore[literal-required]
                results[key][ispin, ikpt, iband] = val

        results["kpt"][ikpt] = np.array(block_result["k"])
        results["n"] = np.array(block_result["n"], dtype=np.int64)

    return results  # type: ignore[return-value]


def break_output_in_kpt_blocks(f: TextIO) -> list[str]:
    """Break the sigma output into large k-point blocks.

    Parameters
    ----------
    f : TextIO
        Open file handle to sigma output.

    Returns
    -------
    list[str]
        List of text blocks, each containing data for one k-point.
    """
    blocks: list[str] = []
    result_str = ""
    reading_block = False
    for line in f.readlines():
        if "Dealing with k" in line:
            reading_block = True
            if result_str:
                blocks.append(result_str)
            result_str = ""

        if reading_block:
            result_str += line

    if result_str:
        blocks.append(result_str)

    return blocks


def break_kpt_spin_blocks(s: str) -> list[str]:
    """Break a k-point block into smaller k-point and spin blocks.

    Parameters
    ----------
    s : str
        Text block containing k-point data.

    Returns
    -------
    list[str]
        List of text blocks, each containing data for one k-point/spin pair.

    Raises
    ------
    ValueError
        If symmetrized values cannot be found in the block.
    """
    if "Symmetrized values from band-averaging" not in s:
        msg = "Could not find symmetrized values in block:\n" + s
        raise ValueError(msg)

    s = s.rsplit("Symmetrized values from band-averaging", maxsplit=1)[-1]
    s = s.split("======================")[0]

    blocks: list[str] = []
    iterlines = iter(s.splitlines())
    while True:
        try:
            line = next(iterlines)
        except StopIteration:
            break

        if line.strip().startswith("k ="):
            lines: list[str] = []
            lines.append(line)  # kpoint line
            try:
                line = next(iterlines)  # empty line
                lines.append(line)
                line = next(iterlines)  # labels line
                while line.strip():
                    lines.append(line)
                    line = next(iterlines)
            except StopIteration:
                # File ended mid-block, skip this incomplete block
                break
            blocks.append("\n".join(lines))

    return blocks


def parse_sigma_output_block(s: str) -> SigmaBlockResult:
    """Extract the GW results from a single k-point/spin block.

    The block should be of the form::

           k =  0.000000  0.000000  0.000000 ik =   1 spin = 1

           n     Emf       Eo      Vxc        X      Cor     Eqp0     Eqp1      Znk
           8  -13.367  -13.367  -32.926  -39.235  -30.771  -11.213  -11.682    0.782
           9  -13.367  -13.367  -32.926  -39.235  -30.771  -11.213  -11.682    0.782

    with no leading or trailing empty line.

    Parameters
    ----------
    s : str
        Text block containing data for one k-point and spin.

    Returns
    -------
    SigmaBlockResult
        Dictionary containing:
        - k : NDArray[np.float64], shape (3,)
            K-point wavevector (reduced coord).
        - ik : int
            Index of k-point.
        - spin : int
            Index of spin.
        - n : list[int]
            Band indices.
        - Emf : list[float]
            Mean-field energy eigenvalue.
        - Eo : list[float]
            Corrected energy eigenvalue.
        - Vxc : list[float]
            Exchange-correlation potential.
        - X : list[float]
            Bare exchange.
        - Cor : list[float]
            Correlation self-energy.
        - Eqp0 : list[float]
            elda - vxc + sig(ecor).
        - Eqp1 : list[float]
            eqp0 + (dsig/de) / (1 - dsig/de) * (eqp0 - ecor).
        - Znk : list[float]
            Quasiparticle renormalization factor.
    """
    results: dict[str, Any] = {}

    results_lines = s.splitlines()

    kpt_line = results_lines.pop(0)
    del results_lines[:2]

    tokens = kpt_line.split()
    results["k"] = np.array(list(map(float, tokens[2:5])))
    results["ik"] = int(tokens[tokens.index("ik") + 2])
    if "spin" in tokens:
        results["spin"] = int(tokens[tokens.index("spin") + 2])
    else:
        results["spin"] = 1

    keys = ["n", "Emf", "Eo", "Vxc", "X", "Cor", "Eqp0", "Eqp1", "Znk"]
    types: list[type[int] | type[float]] = [int, *([float] * 8)]

    for key in keys:
        results[key] = []

    for line in results_lines:
        tokens = line.split()
        for key, typ, token in zip(keys, types, tokens, strict=False):
            results[key].append(typ(token))

    return results  # type: ignore[return-value]


def extract_multiple_GW_results(dirnames: list[str]) -> MultipleGWResult:
    """Extract GW results from a list of directories.

    Parameters
    ----------
    dirnames : list[str]
        List of directory paths containing sigma.out and variables.pkl files.

    Returns
    -------
    MultipleGWResult
        Dictionary containing:
        - ndata : int
            Number of directories processed.
        - variables : list[dict[str, Any]]
            List of variable dictionaries from each directory.
        - results : list[SigmaResult]
            List of parsed sigma results from each directory.

    Notes
    -----
    This function deserializes ``variables.pkl`` using :mod:`pickle`.
    Pickle data is not secure against untrusted input and can execute
    arbitrary code during loading. Only use this function with files from
    trusted sources.
    """
    data: dict[str, Any] = {}
    data["variables"] = []
    data["results"] = []
    data["ndata"] = len(dirnames)

    for dname in dirnames:
        dpath = Path(dname)
        try:
            variables_bytes = (dpath / "variables.pkl").read_bytes()
            variables: dict[str, Any] = pickle.loads(variables_bytes)
            sigma_text = (dpath / "sigma.out").read_text()
            out = parse_sigma_output(sigma_text)
        except OSError as exc:
            msg = f"Failed to read files from directory {dname!r}: {exc}"
            raise OSError(msg) from exc

        data["variables"].append(variables)
        data["results"].append(out)

    return data  # type: ignore[return-value]
