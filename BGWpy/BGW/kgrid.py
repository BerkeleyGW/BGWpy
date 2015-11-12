
import os
import subprocess
import numpy as np
from ..core import fortran_str

def get_kpt_grid(structure, ngkpt, executable='kgrid.x',
                 rootname='tmp.kgrid', clean_after=True, **kwargs):
    """
    Use kgrid.x to compute the list of kpoint and their weight.

    Arguments
    ---------

    structure: pymatgen.Structure
        The cell definition of the system.
    ngkpt: array(3)
        The k-point grid.
    executable: str
        The path to kgrid.x
    rootname: str
        For the file names
    exec_dir: str
        Where to write the files.
    clean_after: bool
        Remove files afterward.


    Keyword Arguments
    -----------------

    Any other argument to pass to get_kgrid_input, including:

    kshift:
        A k-point shift (relative to the grid spacing).

    qshift:
        A q-point shift (absolute, in reduced coord.)


    Returns
    -------

    kpts: A list of k-points (as a 2D list).

    wtks: A list of weights.

    """

    dirname = os.path.dirname(rootname)
    new_dir = dirname and not os.path.exists(dirname)
    inputname = rootname + '.in'
    outputname = rootname + '.out'
    logname = rootname + '.log'

    inputcontent = get_kgrid_input(structure, ngkpt, **kwargs)

    # Write the input
    if new_dir:
        #os.system('mkdir -p ' + dirname)
        subprocess.call(['mkdir', '-p', dirname])

    with open(inputname, 'write') as f:
        f.write(inputcontent)

    # Run kgrid.x
    try:
        subprocess.call([executable, inputname, outputname, logname])
    except OSError as E:
        raise OSError(str(E) + '\n' +
                      'Please make sure that {} is available for execution.'
                      .format(executable))
    

    # Read the output
    with open(outputname, 'read') as f:
        outputcontent = f.read()

    # Clean up
    if clean_after:
        for fname in (inputname, outputname, logname):
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except Exception as E:
                    print(E)
        if new_dir:
            try:
                os.removedirs(dirname)
            except Exception as E:
                print(E)

    # Parse the output
    return get_kpoints(outputcontent)


def get_kgrid_input(structure, ngkpt, kshift=[.0,.0,.0], qshift=[.0,.0,.0], fft=[0,0,0], use_tr=False):
    """Make a kgrid.x input, using pymatgen.Structure object."""

    abc = np.array(structure.lattice.abc)

    latt_vec_rel = (structure.lattice_vectors().transpose() / abc).transpose().round(12)
    pos_cart_rel = np.dot(structure.frac_coords, latt_vec_rel).round(6)

    S = ''

    for arr in (ngkpt, kshift, qshift):
        S += fortran_str(arr) + '\n'

    S += '\n'

    for arr in latt_vec_rel.tolist() + [structure.num_sites]:
        S += fortran_str(arr) + '\n'

    for Z, pos in zip(structure.atomic_numbers, pos_cart_rel):
        S += str(Z) + ' ' + fortran_str(pos) + '\n'

    for arr in (fft, use_tr):
        S += fortran_str(arr) + '\n'

    return S


def get_kpoints(content):
    """Read a list of kpoints and their weights from kgrid.x output file."""
    lines = content.splitlines()[2:]
    kpoints = list()
    weights = list()
    for line in lines:
        k = [ float(ki) for ki in line.split()[:3] ]
        w = float(line.split()[-1])
        kpoints.append(k)
        weights.append(w)
    return kpoints, weights


def get_kqshift(ngkpt, kshift, qshift):
    """Add an absolute qshift to a relative kshift."""
    kqshiftk = [ kshift[i] + qshift[i] * ngkpt[i] for i in range(3) ]
    return kqshiftk


# ============================================================== #

def get_kpt_grid_nosym(ngkpt, kshift=[.0,.0,.0], qshift=[.0,.0,.0]):
    """
    Return a list of kpoints generated with out any symmetry,
    along with their weights.
    """
    ngkpt = np.array(ngkpt)
    kshift = np.array(kshift)
    qshift = np.array(qshift)
    nkx, nky, nkz = ngkpt

    kpoints = list()
    weights = list()
    #for ikx in range(-nkx, nkx):
    #    for iky in range(-nky, nky):
    #        for ikz in range(-nkz, nkz):

    #            k = (np.array([ikx, iky, ikz]) + kshift) / ngkpt * .5 + qshift
    #            kpoints.append(k)
    #            weights.append(1.)
    for ikx in range(nkx):
        for iky in range(nky):
            for ikz in range(nkz):

                k = (np.array([ikx, iky, ikz]) + kshift) / ngkpt + qshift
                kpoints.append(k)
                weights.append(1.)

    return np.array(kpoints), np.array(weights)

    




# ============================================================== #
# Why use a class when a function will do?
#class KgridInput(object):
#    """An input for kgrid.x"""
#
#    _structure = None
#
#    def __init__(self, fft=[0,0,0], use_tr=True, **kwargs):
#
#        self.ngkpt = list()
#        self.kshift = list()
#        self.qshift = list()
#
#        self.lattice_vectors = list()
#        self.num_sites = int()
#        self.cartesian_positions = list()
#
#        self.fft = list()
#        self.use_tr = bool()
#
#        for key, val in kwargs.items():
#            setattr(self, key, val)
#
#    @property
#    def structure(self):
#        return self._structure
#
#    @structure.setter
#    def structure(self, structure):
#        self._structure = structure


