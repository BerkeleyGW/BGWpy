
import os
import subprocess
import numpy as np
from ..core import fortran_str
from ..core import Task

__all__ = ['get_kpt_grid', 'get_kgrid_input', 'get_kpoints', 'get_kqshift',
           'get_kpt_grid_nosym', 'KgridTask']


class KgridTask(Task):

    def __init__(self,
                 structure,
                 ngkpt = 3*[1],
                 kshift = 3*[.0],
                 qshift = 3*[.0],
                 fft = 3*[0],
                 use_tr=False,
                 executable='kgrid.x',  # TODO remove executable and make bindir a global option
                 rootname='tmp.kgrid',
                 clean_after=True,
                 **kwargs):
        """
        Arguments
        ---------

        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ngkpt : list(3), int, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
        fft : list(3), int, optional
            Number of points along each direction of the fft grid.
        use_tr : bool
            Use time reversal symmetry.
        """

        self.dirname = os.path.dirname(rootname)
        self.inputname = rootname + '.in'
        self.outputname = rootname + '.out'
        self.logname = rootname + '.log'
        self.executable = executable
        self.clean_after = clean_after

        self.structure = structure
        self.ngkpt = ngkpt
        self.kshift = kshift
        self.qshift = qshift
        self.fft = fft
        self.use_tr = use_tr

    def read_kpoints(self):
        """Read a list of kpoints and their weights from kgrid.x output file."""
        with open(self.outputname, 'read') as f:
            content = f.read()

        lines = content.splitlines()[2:]
        kpoints = list()
        weights = list()
        for line in lines:
            k = [ float(ki) for ki in line.split()[:3] ]
            w = float(line.split()[-1])
            kpoints.append(k)
            weights.append(w)
        return kpoints, weights

    @property
    def new_dir(self):
        return self.dirname and not os.path.exists(self.dirname)

    def write(self):
        if self.new_dir:
            subprocess.call(['mkdir', '-p', dirname])

        with open(self.inputname, 'write') as f:
            f.write(self.get_kgrid_input())

    def run(self):
        try:
            subprocess.call([self.executable, self.inputname,
                             self.outputname, self.logname])
        except OSError as E:
            raise OSError(str(E) + '\n' +
                'Please make sure that kgrid.x is available for execution.')
    

    def clean_up(self):
        """Remove all temporary files (input, output log)."""
        for fname in (self.inputname, self.outputname, self.logname):
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except Exception as E:
                    print(E)
        if self.new_dir:
            try:
                os.removedirs(dirname)
            except Exception as E:
                print(E)

    def get_kgrid_input(self):
        """Make a kgrid.x input, using pymatgen.Structure object."""

        structure = self.structure
        kshift = self.kshift
        qshift = self.qshift
        ngkpt = self.ngkpt
        fft = self.fft
        use_tr = self.use_tr
    
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

    @staticmethod
    def get_kqshift(self, ngkpt, kshift, qshift):
        """Add an absolute qshift to a relative kshift."""
        kqshiftk = [ kshift[i] + qshift[i] * ngkpt[i] for i in range(3) ]
        return kqshiftk

    @staticmethod
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
        for ikx in range(nkx):
            for iky in range(nky):
                for ikz in range(nkz):
    
                    k = (np.array([ikx, iky, ikz]) + kshift) / ngkpt + qshift
                    kpoints.append(k)
                    weights.append(1.)
    
        return np.array(kpoints), np.array(weights)

    def read_symmetries(self):
        """Read the symmetries matrices and translation vectors."""

        with open(self.logname, 'read') as f:
            while True:
                try:
                    line = f.next()

                    if 'symmetries of the crystal without FFT grid' in line:
                        line = f.next()
                        nsym = int(line)

                        line = f.next()
                        assert 'Space group' in line

                        syms = np.zeros((nsym, 9), dtype=np.int)
                        taus = np.zeros((nsym, 3), dtype=np.float)

                        for i in range(nsym):
                            line = f.next()
                            parts = line.split()
                            syms[i,:] = map(int, parts[2:11])
                            taus[i,:] = map(float, parts[11:14])

                        break

                except StopIteration:
                    break

                except ValueError as e:
                    raise Exception('Could not parse kgrid file.\n\n' + str(e))

        return syms, taus

    def get_kpoints(self):
        """Write, run and extract kpoints."""
        try:
            self.write()
            self.run()
            return self.read_kpoints()
        finally:
            if self.clean_after:
                self.clean_up()

    def get_symmetries(self):
        """Write, run and extract symmetries."""
        try:
            self.write()
            self.run()
            return self.read_symmetries()
        finally:
            if self.clean_after:
                self.clean_up()

    def get_kpoints_and_sym(self):
        """Write, run and extract kpoints and symmetries."""
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
""" Constructor functions                                                   """

def get_kpt_grid(structure, ngkpt,
                 executable='kgrid.x',  # TODO remove executable and make bindir a global option
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
    Return a list of kpoints generated without any symmetry,
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


