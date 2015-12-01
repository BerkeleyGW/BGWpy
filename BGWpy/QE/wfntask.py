from __future__ import print_function
import os

from .qetask      import QETask
from .constructor import get_bands_input

# Public
__all__ = ['WfnTask']


class WfnTask(QETask):
    """Wavefunctions calculation."""

    _TASK_NAME = 'Wavefunction task'

    _input_fname = 'wfn.in'
    _output_fname = 'wfn.out'

    def __init__(self, dirname, **kwargs):
        """
        Arguments
        ---------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.


        Keyword arguments
        -----------------
        (All mandatory unless specified otherwise)

        prefix : str
            Prefix required by QE as a rootname.
        pseudo_dir : str
            Directory in which pseudopotential files are found.
        pseudos : list, str
            Pseudopotential files.
        structure : pymatgen.Structure
            Structure object containing information on the unit cell.
        ecutwfc : float
            Energy cutoff for the wavefunctions
        nbnd : int, optional
            Number of bands to be computed.
        charge_density_fname : str
            Path to the charge density file produced
            by a density calculation ('charge-density.dat').
        data_file_fname : str
            Path to the xml data file produced 
            by a density calculation ('data-file.xml').
        spin_polarization_fname : str, optional
            Path to the spin polarization file produced
            by a density calculation ('spin-polarization.dat').
        ngkpt : list(3), float, optional
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
            K-points are either specified using ngkpt or using kpts and wtks.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
        symkpt : bool (True), optional
            Use symmetries for the k-point grid generation.
        kpts : 2D list(nkpt,3), float, optional
            List of k-points.
            K-points are either specified using ngkpt or using kpts and wtks.
        wtks : list(nkpt), float, optional
            Weights of each k-point.

        """

        super(WfnTask, self).__init__(dirname, **kwargs)

        kpts, wtks = self.get_kpts(**kwargs)

        self.charge_density_fname = kwargs['charge_density_fname']
        if 'spin_polarization_fname' in kwargs:
            self.spin_polarization_fname = kwargs['spin_polarization_fname']

        self.data_file_fname = kwargs['data_file_fname']

        # Input file
        self.input = get_bands_input(
            self.prefix,
            self.pseudo_dir,
            self.pseudos,
            self.structure,
            kwargs['ecutwfc'],
            kpts,
            wtks,
            nbnd = kwargs.get('nbnd'),
            )

        self.input.fname = self._input_fname

        # Run script
        self.runscript.append('$MPIRUN $PW $PWFLAGS -in {} &> {}'.format(
                              self._input_fname, self._output_fname))

    @property
    def charge_density_fname(self):
        return self._charge_density_fname

    @charge_density_fname.setter
    def charge_density_fname(self, value):
        self._charge_density_fname = value
        dest = os.path.join(self.savedir, 'charge-density.dat')
        self.update_link(value, dest)

    @property
    def spin_polarization_fname(self):
        return self._spin_polarization_fname

    @spin_polarization_fname.setter
    def spin_polarization_fname(self, value):
        self._spin_polarization_fname = value
        dest = os.path.join(self.savedir, 'spin-polarization.dat')
        self.update_link(value, dest)

    @property
    def data_file_fname(self):
        return self._data_file_fname

    @data_file_fname.setter
    def data_file_fname(self, value):
        self._data_file_fname = value
        dest = os.path.join(self.savedir, 'data-file.xml')
        self.update_copy(value, dest)

