"""K-point grid generation using BerkeleyGW's kgrid.x.

This module provides the KgridTask class and associated functions for
generating k-point grids using BerkeleyGW's kgrid.x executable.
"""

from __future__ import annotations

import os
import subprocess
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from BGWpy.core import Task, fortran_str

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray
    from pymatgen.core import Structure

__all__ = [
    "KgridTask",
    "apply_qshift",
    "get_kgrid_input",
    "get_kpoints",
    "get_kpt_grid",
    "get_kpt_grid_nosym",
    "get_kqshift",
    "patch_sample_sphere",
]


class KgridTask(Task):
    """Task for generating k-point grids using kgrid.x.

    This task wraps BerkeleyGW's kgrid.x executable to generate symmetry-reduced
    k-point grids for electronic structure calculations.

    Attributes
    ----------
    structure : Structure
        Structure object containing information on the unit cell.
    ngkpt : NDArray[np.int64]
        K-points grid dimensions.
    kshift : NDArray[np.float64]
        Relative shift of the k-points grid.
    qshift : NDArray[np.float64]
        Absolute shift of the k-points grid.
    fft : list[int]
        FFT grid dimensions.
    use_tr : bool
        Whether to use time reversal symmetry.
    executable : str
        Path to kgrid.x executable.
    clean_after : bool
        Whether to clean up temporary files after execution.
    """

    structure: Structure
    ngkpt: NDArray[np.int64]
    kshift: NDArray[np.float64]
    qshift: NDArray[np.float64]
    fft: list[int]
    use_tr: bool
    executable: str
    clean_after: bool
    inputname: str
    outputname: str
    logname: str
    _new_dir: bool

    def __init__(
        self,
        structure: Structure,
        ngkpt: ArrayLike = (1, 1, 1),
        kshift: ArrayLike = (0.0, 0.0, 0.0),
        qshift: ArrayLike = (0.0, 0.0, 0.0),
        fft: list[int] | tuple[int, int, int] = (0, 0, 0),
        use_tr: bool = False,
        executable: str = "kgrid.x",
        rootname: str = "tmp.kgrid",
        clean_after: bool = True,
        dirname: str = "",
        **kwargs: Any,
    ) -> None:
        """Initialize a k-grid task.

        Parameters
        ----------
        structure : Structure
            Structure object containing information on the unit cell.
        ngkpt : list(3), int, default=(1, 1, 1)
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift : list(3), float, default=(0.0, 0.0, 0.0)
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, default=(0.0, 0.0, 0.0)
            Absolute shift of the k-points grid along each direction.
        fft : list[int] | tuple[int, int, int], default=(0, 0, 0)
            Number of points along each direction of the FFT grid.
        use_tr : bool, default=False
            Use time reversal symmetry.
        executable : str, default="kgrid.x"
            Path to kgrid.x executable.
        rootname : str, default="tmp.kgrid"
            Root name for temporary files.
        clean_after : bool, default=True
            Whether to clean up temporary files after execution.
        dirname : str, default=""
            Directory for temporary files.
        **kwargs : Any
            Additional keyword arguments (unused).
        """
        rootname_path = Path(dirname) / rootname
        self.dirname = str(rootname_path.parent)
        self.inputname = str(rootname_path.with_suffix(".in"))
        self.outputname = str(rootname_path.with_suffix(".out"))
        self.logname = str(rootname_path.with_suffix(".log"))
        self.executable = executable
        self.clean_after = clean_after

        self.structure = structure
        self.ngkpt = np.array(ngkpt, dtype=np.int64)
        self.kshift = np.array(kshift, dtype=np.float64)
        self.qshift = np.array(qshift, dtype=np.float64)
        self.fft = list(fft)
        self.use_tr = use_tr

    def read_kpoints(self) -> tuple[list[list[float]], list[float]]:
        """Read a list of k-points and their weights from kgrid.x output file.

        Returns
        -------
        kpoints : list[list[float]]
            List of k-points, each as [kx, ky, kz].
        weights : list[float]
            List of k-point weights.
        """
        with open(self.outputname) as f:
            content = f.read()

        lines = content.splitlines()[2:]
        kpoints: list[list[float]] = []
        weights: list[float] = []
        for line in lines:
            k = [float(ki) for ki in line.split()[:3]]
            w = float(line.split()[-1])
            kpoints.append(k)
            weights.append(w)
        return kpoints, weights

    @property
    def new_dir(self) -> bool:
        """Check if a new directory needs to be created."""
        return bool(self.dirname) and not Path(self.dirname).exists()

    def write(self) -> None:
        """Write the kgrid.x input file."""
        if self.new_dir:
            subprocess.call(["mkdir", "-p", self.dirname])

        with open(self.inputname, "w") as f:
            f.write(self.get_kgrid_input())

    def run(self) -> None:
        """Run kgrid.x.

        Raises
        ------
        OSError
            If kgrid.x executable cannot be found.
        """
        try:
            subprocess.call([self.executable, self.inputname, self.outputname, self.logname])
        except OSError as e:
            message = (
                str(e)
                + "\n\n"
                + 79 * "="
                + "\n\n"
                + "Could not find the executable kgrid.x\n"
                + "Please make sure it is available for execution.\n"
                + "On a computing cluster, you might do this by loading the module:\n"
                + "    module load berkeleygw\n"
                + "If you compiled BerkeleyGW yourself, "
                + "make sure that the 'bin' directory\n"
                + "of BerkeleyGW is listed in your PATH environment variable.\n"
                + "\n"
                + 79 * "="
                + "\n"
            )

            raise OSError(message) from e

    def clean_up(self) -> None:
        """Remove all temporary files (input, output, log)."""
        for fname in (self.inputname, self.outputname, self.logname):
            if Path(fname).exists():
                try:
                    Path(fname).unlink()
                except Exception as e:
                    warnings.warn(f"Error during cleanup: {e}", stacklevel=2)
        if self.new_dir:
            try:
                os.removedirs(self.dirname)
            except Exception as e:
                warnings.warn(f"Error during cleanup: {e}", stacklevel=2)

    def get_kgrid_input(self) -> str:
        """Generate kgrid.x input content.

        Returns
        -------
        str
            The kgrid.x input file content.
        """
        structure = self.structure
        kshift = self.kshift
        qshift = self.qshift
        ngkpt = self.ngkpt
        fft = self.fft
        use_tr = self.use_tr

        abc = np.array(structure.lattice.abc)

        latt_vec_rel = (structure.lattice.matrix.transpose() / abc).transpose().round(12)
        pos_cart_rel = np.dot(structure.frac_coords, latt_vec_rel).round(6)

        result_str = ""

        for arr in (ngkpt, kshift, qshift):
            result_str += fortran_str(arr) + "\n"

        result_str += "\n"

        for arr in [*latt_vec_rel.tolist(), structure.num_sites]:
            result_str += fortran_str(arr) + "\n"

        for z_num, pos in zip(structure.atomic_numbers, pos_cart_rel, strict=False):
            result_str += str(z_num) + " " + fortran_str(pos) + "\n"

        for arr in (fft, use_tr):
            result_str += fortran_str(arr) + "\n"

        return result_str

    @staticmethod
    def get_kqshift(
        ngkpt: ArrayLike,
        kshift: ArrayLike,
        qshift: ArrayLike,
    ) -> list[float]:
        """Add an absolute qshift to a relative kshift.

        Parameters
        ----------
        ngkpt : list(3), int
            K-point grid dimensions.
        kshift : list(3), float
            Relative k-point shift.
        qshift : list(3), float
            Absolute q-point shift.

        Returns
        -------
        list[float]
            Combined shift.
        """
        ngkpt_arr = np.asarray(ngkpt)
        kshift_arr = np.asarray(kshift)
        qshift_arr = np.asarray(qshift)
        return [float(kshift_arr[i] + qshift_arr[i] * ngkpt_arr[i]) for i in range(3)]

    def get_kpt_grid_nosym(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return a list of k-points generated without any symmetry.

        Returns
        -------
        kpoints : NDArray[np.float64]
            Array of shape (nkpt, 3) containing k-point coordinates.
        weights : NDArray[np.float64]
            Array of shape (nkpt,) containing k-point weights.
        """
        ngkpt = self.ngkpt
        kshift = self.kshift
        qshift = self.qshift
        nkx, nky, nkz = ngkpt

        kpoints: list[NDArray[np.float64]] = []
        weights: list[float] = []
        for ikx in range(nkx):
            for iky in range(nky):
                for ikz in range(nkz):
                    k = (np.array([ikx, iky, ikz], dtype=np.float64) + kshift) / ngkpt + qshift
                    kpoints.append(k)
                    weights.append(1.0)

        return np.array(kpoints, dtype=np.float64), np.array(weights, dtype=np.float64)

    def read_symmetries(self) -> tuple[NDArray[np.int64], NDArray[np.float64]]:
        """Read the symmetry matrices and translation vectors.

        Returns
        -------
        syms : NDArray[np.int64]
            Array of shape (nsym, 9) containing symmetry matrices.
        taus : NDArray[np.float64]
            Array of shape (nsym, 3) containing translation vectors.

        Raises
        ------
        Exception
            If the kgrid file cannot be parsed.
        """
        with open(self.logname) as f:
            while True:
                try:
                    line = next(f)

                    if "symmetries of the crystal without FFT grid" in line:
                        line = next(f)
                        nsym = int(line)

                        line = next(f)
                        assert "Space group" in line

                        syms = np.zeros((nsym, 9), dtype=np.int64)
                        taus = np.zeros((nsym, 3), dtype=np.float64)

                        for i in range(nsym):
                            line = next(f)
                            parts = line.split()
                            syms[i, :] = [int(p) for p in parts[2:11]]
                            taus[i, :] = [float(p) for p in parts[11:14]]

                        break

                except StopIteration:
                    break

                except ValueError as e:
                    msg = "Could not parse kgrid file.\n\n" + str(e)
                    raise Exception(msg) from e

        return syms, taus

    def get_kpoints(self) -> tuple[list[list[float]], list[float]]:
        """Write, run and extract k-points.

        Returns
        -------
        kpoints : list[list[float]]
            List of k-points.
        weights : list[float]
            List of k-point weights.
        """
        try:
            self.write()
            self.run()
            return self.read_kpoints()
        finally:
            if self.clean_after:
                self.clean_up()

    def get_symmetries(self) -> tuple[NDArray[np.int64], NDArray[np.float64]]:
        """Write, run and extract symmetries.

        Returns
        -------
        syms : NDArray[np.int64]
            Symmetry matrices.
        taus : NDArray[np.float64]
            Translation vectors.
        """
        try:
            self.write()
            self.run()
            return self.read_symmetries()
        finally:
            if self.clean_after:
                self.clean_up()

    def get_kpoints_and_sym(
        self,
    ) -> tuple[
        tuple[list[list[float]], list[float]],
        tuple[NDArray[np.int64], NDArray[np.float64]],
    ]:
        """Write, run and extract k-points and symmetries.

        Returns
        -------
        kpt_result : tuple[list[list[float]], list[float]]
            K-points and their weights.
        sym_result : tuple[NDArray[np.int64], NDArray[np.float64]]
            Symmetry matrices and translation vectors.
        """
        try:
            self.write()
            self.run()
            outkpt = self.read_kpoints()
            outsym = self.read_symmetries()
            return outkpt, outsym
        finally:
            if self.clean_after:
                self.clean_up()


# =========================================================================== #
# Constructor functions


def get_kpt_grid(
    structure: Structure,
    ngkpt: ArrayLike,
    executable: str = "kgrid.x",
    rootname: str = "tmp.kgrid",
    clean_after: bool = True,
    **kwargs: Any,
) -> tuple[list[list[float]], list[float]]:
    """Use kgrid.x to compute the list of k-points and their weights.

    Parameters
    ----------
    structure : Structure
        The cell definition of the system.
    ngkpt : list(3), int
        The k-point grid dimensions.
    executable : str, default="kgrid.x"
        The path to kgrid.x.
    rootname : str, default="tmp.kgrid"
        For the file names.
    clean_after : bool, default=True
        Remove files afterward.
    **kwargs : Any
        Any other argument to pass to get_kgrid_input, including:
        - kshift: A k-point shift (relative to the grid spacing).
        - qshift: A q-point shift (absolute, in reduced coord.)

    Returns
    -------
    kpts : list[list[float]]
        A list of k-points (as a 2D list).
    wtks : list[float]
        A list of weights.

    Raises
    ------
    OSError
        If kgrid.x executable cannot be found.
    """
    dirname = Path(rootname).parent
    new_dir = bool(str(dirname)) and not Path(dirname).exists()
    inputname = rootname + ".in"
    outputname = rootname + ".out"
    logname = rootname + ".log"

    inputcontent = get_kgrid_input(structure, ngkpt, **kwargs)

    # Write the input
    if new_dir:
        subprocess.call(["mkdir", "-p", str(dirname)])

    with open(inputname, "w") as f:
        f.write(inputcontent)

    # Run kgrid.x
    try:
        subprocess.call([executable, inputname, outputname, logname])
    except OSError as e:
        message = (
            str(e)
            + "\n\n"
            + 79 * "="
            + "\n\n"
            + f"Could not find the executable {executable}.\n"
            + "Please make sure it is available for execution.\n"
            + "On a computing cluster, you might do this by loading the module:\n"
            + "    module load berkeleygw\n"
            + "If you compiled BerkeleyGW yourself, "
            + "make sure that the 'bin' directory\n"
            + "of BerkeleyGW is listed in your PATH environment variable.\n"
            + "\n"
            + 79 * "="
            + "\n"
        )

        raise OSError(message) from None

    # Read the output
    with open(outputname) as f:
        outputcontent = f.read()

    # Clean up
    if clean_after:
        for fname in (inputname, outputname, logname):
            if Path(fname).exists():
                try:
                    Path(fname).unlink()
                except Exception as ex:
                    warnings.warn(f"Error during cleanup: {ex}", stacklevel=2)
        if new_dir:
            try:
                os.removedirs(str(dirname))
            except Exception as ex:
                warnings.warn(f"Error during cleanup: {ex}", stacklevel=2)

    # Parse the output
    return get_kpoints(outputcontent)


def get_kgrid_input(
    structure: Structure,
    ngkpt: ArrayLike,
    kshift: ArrayLike | None = None,
    qshift: ArrayLike | None = None,
    fft: list[int] | None = None,
    use_tr: bool = False,
    **kwargs: Any,
) -> str:
    """Make a kgrid.x input, using pymatgen.Structure object.

    Parameters
    ----------
    structure : Structure
        Structure object containing unit cell information.
    ngkpt : list(3), int
        K-point grid dimensions.
    kshift : list(3), float | None, default=None
        Relative k-point shift. Defaults to [0, 0, 0].
    qshift : list(3), float | None, default=None
        Absolute q-point shift. Defaults to [0, 0, 0].
    fft : list[int] | None, default=None
        FFT grid dimensions. Defaults to [0, 0, 0].
    use_tr : bool, default=False
        Use time reversal symmetry.
    **kwargs : Any
        Additional keyword arguments (unused).

    Returns
    -------
    str
        The kgrid.x input file content.
    """
    if fft is None:
        fft = [0, 0, 0]
    if qshift is None:
        qshift = [0.0, 0.0, 0.0]
    if kshift is None:
        kshift = [0.0, 0.0, 0.0]

    abc = np.array(structure.lattice.abc)

    latt_vec_rel = (structure.lattice.matrix.transpose() / abc).transpose().round(12)
    pos_cart_rel = np.dot(structure.frac_coords, latt_vec_rel).round(6)

    s = ""

    for arr in (ngkpt, kshift, qshift):
        s += fortran_str(arr) + "\n"

    s += "\n"

    for arr in [*latt_vec_rel.tolist(), structure.num_sites]:
        s += fortran_str(arr) + "\n"

    for z_num, pos in zip(structure.atomic_numbers, pos_cart_rel, strict=False):
        s += str(z_num) + " " + fortran_str(pos) + "\n"

    for arr in (fft, use_tr):
        s += fortran_str(arr) + "\n"

    return s


def get_kpoints(content: str) -> tuple[list[list[float]], list[float]]:
    """Read a list of k-points and their weights from kgrid.x output content.

    Parameters
    ----------
    content : str
        The content of a kgrid.x output file.

    Returns
    -------
    kpoints : list[list[float]]
        List of k-points, each as [kx, ky, kz].
    weights : list[float]
        List of k-point weights.
    """
    lines = content.splitlines()[2:]
    kpoints: list[list[float]] = []
    weights: list[float] = []
    for line in lines:
        k = [float(ki) for ki in line.split()[:3]]
        w = float(line.split()[-1])
        kpoints.append(k)
        weights.append(w)
    return kpoints, weights


def get_kqshift(
    ngkpt: ArrayLike,
    kshift: ArrayLike,
    qshift: ArrayLike,
) -> list[float]:
    """Add an absolute qshift to a relative kshift.

    Parameters
    ----------
    ngkpt : list(3), int
        K-point grid dimensions.
    kshift : list(3), float
        Relative k-point shift.
    qshift : list(3), float
        Absolute q-point shift.

    Returns
    -------
    list[float]
        Combined shift.
    """
    ngkpt_arr = np.asarray(ngkpt)
    kshift_arr = np.asarray(kshift)
    qshift_arr = np.asarray(qshift)
    return [float(kshift_arr[i] + qshift_arr[i] * ngkpt_arr[i]) for i in range(3)]


# ============================================================== #


def get_kpt_grid_nosym(
    ngkpt: ArrayLike,
    kshift: ArrayLike | None = None,
    qshift: ArrayLike | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return a list of k-points generated without any symmetry.

    Parameters
    ----------
    ngkpt : list(3), int
        K-point grid dimensions.
    kshift : list(3), float | None, default=None
        Relative k-point shift. Defaults to [0, 0, 0].
    qshift : list(3), float | None, default=None
        Absolute q-point shift. Defaults to [0, 0, 0].

    Returns
    -------
    kpoints : NDArray[np.float64]
        Array of shape (nkpt, 3) containing k-point coordinates.
    weights : NDArray[np.float64]
        Array of shape (nkpt,) containing k-point weights (all 1.0).
    """
    if qshift is None:
        qshift = [0.0, 0.0, 0.0]
    if kshift is None:
        kshift = [0.0, 0.0, 0.0]

    ngkpt_arr = np.array(ngkpt, dtype=np.int64)
    kshift_arr = np.array(kshift, dtype=np.float64)
    qshift_arr = np.array(qshift, dtype=np.float64)
    nkx, nky, nkz = ngkpt_arr

    kpoints: list[NDArray[np.float64]] = []
    weights: list[float] = []

    for ikx in range(nkx):
        for iky in range(nky):
            for ikz in range(nkz):
                k = (
                    np.array([ikx, iky, ikz], dtype=np.float64) + kshift_arr
                ) / ngkpt_arr + qshift_arr
                kpoints.append(k)
                weights.append(1.0)

    return np.array(kpoints, dtype=np.float64), np.array(weights, dtype=np.float64)


def patch_sample_sphere(
    ngkpt: ArrayLike,
    r_patch: float,
    kshift: ArrayLike | None = None,
    qshift: ArrayLike | None = None,
    center: ArrayLike | None = None,
    normalize_weights: bool = True,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate a patch-sampled k-grid within a sphere.

    Creates a dense uniform k-point grid and filters it to include only
    points within a sphere of specified radius. This is useful for BSE
    kernel interpolation with fine grids around specific k-points.

    Parameters
    ----------
    ngkpt : list(3), int
        Dense grid dimensions for sampling (e.g., [100, 100, 100]).
    r_patch : float
        Radius of the sphere in fractional reciprocal space units.
    kshift : list(3), float | None, default=None
        Relative k-point shift. Defaults to [0, 0, 0].
    qshift : list(3), float | None, default=None
        Absolute q-point shift. Defaults to [0, 0, 0].
    center : list(3), float | None, default=None
        Center of the sphere in fractional reciprocal space coordinates.
        Defaults to [0, 0, 0] (Gamma point).
    normalize_weights : bool, default=True
        If True, normalize weights to sum to 1.0.

    Returns
    -------
    kpoints : NDArray[np.float64]
        Array of shape (nkpt_filtered, 3) containing filtered k-point coordinates.
    weights : NDArray[np.float64]
        Array of shape (nkpt_filtered,) containing k-point weights.

    Examples
    --------
    Generate a 100x100x100 grid and filter for points within 0.05 of Gamma:

    >>> kpts, wtks = patch_sample_sphere(
    ...     ngkpt=[100, 100, 100],
    ...     r_patch=0.05,
    ...     center=[0.0, 0.0, 0.0]
    ... )

    """
    if center is None:
        center_arr = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    else:
        center_arr = np.array(center, dtype=np.float64)

    # Generate full dense grid
    kpoints, weights = get_kpt_grid_nosym(ngkpt, kshift=kshift, qshift=qshift)

    # Calculate distances from center
    distances = np.linalg.norm(kpoints - center_arr, axis=1)

    # Filter points within sphere
    mask = distances <= r_patch
    kpoints_filtered = kpoints[mask]
    weights_filtered = weights[mask]

    # Normalize weights if requested
    if normalize_weights:
        weights_sum = np.sum(weights_filtered)
        if weights_sum > 0:
            weights_filtered = weights_filtered / weights_sum

    nkpt_total = len(kpoints)
    nkpt_filtered = len(kpoints_filtered)
    warnings.warn(
        f"Patch sampling: filtered {nkpt_filtered} k-points from "
        f"{nkpt_total} total ({100.0 * nkpt_filtered / nkpt_total:.2f}%)",
        stacklevel=2,
    )

    return kpoints_filtered, weights_filtered


def apply_qshift(
    kpts: ArrayLike,
    qshift: ArrayLike,
    wtks: ArrayLike | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Apply an absolute q-shift to explicit k-points.

    This function is useful when you have explicit k-points (e.g., from patch
    sampling) and need to create a q-shifted grid for WFNq_fi in absorption
    calculations.

    Parameters
    ----------
    kpts : array-like
        Array of shape (nkpt, 3) containing k-point coordinates.
    qshift : array-like
        Array of shape (3,) containing the absolute q-shift to apply.
    wtks : array-like | None, default=None
        Array of shape (nkpt,) containing k-point weights. If None, weights
        are set to uniform values.

    Returns
    -------
    kpts_shifted : NDArray[np.float64]
        Array of shape (nkpt, 3) containing shifted k-point coordinates.
    wtks_out : NDArray[np.float64]
        Array of shape (nkpt,) containing k-point weights (same as input).

    Examples
    --------
    Apply a small q-shift for WFNq_fi generation:

    >>> kpts_patch, wtks_patch = patch_sample_sphere(
    ...     ngkpt=[100, 100, 100],
    ...     r_patch=0.1,
    ... )
    >>> kpts_q, wtks_q = apply_qshift(kpts_patch, [0.001, 0.0, 0.0], wtks_patch)

    """
    kpts_arr = np.array(kpts, dtype=np.float64)
    qshift_arr = np.array(qshift, dtype=np.float64)

    if kpts_arr.ndim != 2 or kpts_arr.shape[1] != 3:
        msg = f"kpts must have shape (nkpt, 3), got {kpts_arr.shape}"
        raise ValueError(msg)

    if qshift_arr.shape != (3,):
        msg = f"qshift must have shape (3,), got {qshift_arr.shape}"
        raise ValueError(msg)

    # Apply the shift
    kpts_shifted = kpts_arr + qshift_arr

    # Handle weights
    if wtks is None:
        wtks_out = np.ones(len(kpts_arr), dtype=np.float64)
    else:
        wtks_out = np.array(wtks, dtype=np.float64)
        if wtks_out.shape != (len(kpts_arr),):
            msg = f"wtks must have shape ({len(kpts_arr)},), got {wtks_out.shape}"
            raise ValueError(msg)

    return kpts_shifted, wtks_out
