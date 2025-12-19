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

__all__ = ["extract_multiple_GW_results", "parse_sigma_output"]


class SigmaBlockResult(TypedDict):
    """Result dictionary from parsing a single sigma output block."""

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
    """Result dictionary from parse_sigma_output."""

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
    """Result dictionary from extract_multiple_GW_results."""

    ndata: int
    variables: list[dict[str, Any]]
    results: list[SigmaResult]


def parse_sigma_output(f: str | TextIO) -> SigmaResult:
    """Extract the GW results of a calculation with BerkeleyGW.

    Parameters
    ----------
    f : str | TextIO
        Path to sigma output file, or an open file handle.

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
    if isinstance(f, str):
        with Path(f).open() as fi:
            return parse_sigma_output(fi)

    # Break the output into large kpoint block.
    large_kpt_blocks = break_output_in_kpt_blocks(f)

    # Count k-points from number of kpt blocks
    nkpt = len(large_kpt_blocks)

    if nkpt == 0:
        msg = "No k-point blocks found in sigma output file"
        raise ValueError(msg)

    # Break the blocks into smaller kpt and spin block
    kpt_spin_blocks: list[str] = []
    subblock: list[str] = []
    for block in large_kpt_blocks:
        subblock = break_kpt_spin_blocks(block)
        kpt_spin_blocks.extend(subblock)

    # Count spins from number of sub-blocks
    nspin = len(subblock)

    # Parse each block
    block_results: list[SigmaBlockResult] = []
    block_result: SigmaBlockResult | None = None
    for block in kpt_spin_blocks:
        block_result = parse_sigma_output_block(block)
        block_results.append(block_result)

    if block_result is None:
        msg = "No valid blocks found in sigma output"
        raise ValueError(msg)

    # Count number of bands from the lines of last block
    nband = len(block_result["n"])

    # Initialize the results dict
    results: dict[str, Any] = {"nspin": nspin, "nkpt": nkpt, "nband": nband}

    keys = ["Emf", "Eo", "Vxc", "X", "Cor", "Eqp0", "Eqp1", "Znk"]

    for key in keys:
        results[key] = np.zeros((nspin, nkpt, nband), dtype=np.float64)

    results["kpt"] = np.zeros((nkpt, 3), dtype=np.float64)
    results["n"] = np.zeros(nband, dtype=np.int64)

    # Merge the blocks
    for block_result in block_results:
        ispin = block_result["spin"] - 1
        ikpt = block_result["ik"] - 1
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
    Exception
        If symmetrized values cannot be found in the block.
    """
    if "Symmetrized values from band-averaging" not in s:
        msg = "Could not find symmetrized values in block:\n" + s
        raise Exception(msg)

    s = s.split("Symmetrized values from band-averaging")[-1]
    s = s.split("======================")[0]

    blocks: list[str] = []
    iterlines = iter(s.splitlines())
    while True:
        try:
            line = next(iterlines)
        except StopIteration:
            break

        if line.startswith("       k ="):
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

    results["k"] = np.array(list(map(float, kpt_line.split()[2:5])))
    results["ik"] = int(kpt_line.split()[7])
    results["spin"] = int(kpt_line.split()[10])

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
    """
    data: dict[str, Any] = {}
    data["variables"] = []
    data["results"] = []
    data["ndata"] = len(dirnames)

    for dname in dirnames:
        dpath = Path(dname)
        with (dpath / "variables.pkl").open("rb") as f:
            variables: dict[str, Any] = pickle.load(f)

        with (dpath / "sigma.out").open() as f:
            out = parse_sigma_output(f)

        data["variables"].append(variables)
        data["results"].append(out)

    return data  # type: ignore[return-value]
