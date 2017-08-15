from __future__ import print_function
import os

from .abinittask import AbinitTask

__all__ = ['AbinitWfnTask']

class AbinitWfnTask(AbinitTask):
    """Charge density calculation."""

    _TASK_NAME = 'Wfn'

    _input_fname = 'wfn.in'
    _output_fname = 'wfn.out'

    def __init__(self, dirname, **kwargs):
        """
        Arguments
        ---------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.


        Keyword Arguments
        -----------------

        charge_density_fname : str
            Name of the density file produced by a previous SCF run (_DEN).
        ecut : float
            Kinetic energy cut-off, in Hartree.
        nband : int
            Number of bands to be computed.
        nbdbuf : int
            Number of bands in the buffer, useful for NSCF calculations in lots of bands.
        tolwfr : float (1e-16)
            Tolerance on wavefunctions residual used as a convergence criterion
            for the NSCF cycle.
        prefix : str
            Prefix used as a rootname for abinit calculations.
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
        input_wavefunction_fname: str, optional
            Name of previously compute wavefunction file, in case you want
            to restart from there.
        input_variables : dict
            Any other input variables for the Abinit input file.

        See also:
            BGWpy.Abinit.abinittask.AbinitTask

        """

        kwargs.setdefault('prefix', 'wfn')

        super(AbinitWfnTask, self).__init__(dirname, **kwargs)

        self.charge_density_fname = kwargs['charge_density_fname']

        if 'input_wavefunction_fname' in kwargs:
            self.input_wavefunction_fname = kwargs['input_wavefunction_fname']

        self.input.set_variables(self.get_wfn_variables(**kwargs))

    def get_wfn_variables(self, **kwargs):
        """Return a dict of variables required for an SCF calculation."""

        nband = kwargs.get('nband')
        if not nband:
            nband = kwargs.get('nbnd')

        ecut = kwargs.get('ecut')
        if not ecut:
            ecut = kwargs.get('ecutwfc')
            if not ecut:
                raise Exception("Please specify 'ecut' for Abinit.")
            else:
                # Maybe warn the user that ecut is in Hartree?
                pass

        variables = dict(
            ecut = ecut,
            nband = nband,
            irdden = 1,
            nbdbuf = kwargs.get('nbdbuf', 0),
            irdwfk = 1 if self.input_wavefunction_fname else 0,
            tolwfr = kwargs.get('tolwfr', 1e-16),
            iscf = kwargs.get('iscf', -3),
            istwfk = kwargs.get('istwfk', '*1'),
            )
        return variables

    @property
    def wavefunction_fname(self):
        return self.get_odat('WFK')

    wfn_fname = wavefunction_fname
    wfk_fname = wavefunction_fname

    @property
    def charge_density_fname(self):
        return self.get_odat('DEN')

    @charge_density_fname.setter
    def charge_density_fname(self, value):
        self._charge_density_fname = value
        dest = os.path.relpath(self.get_idat('DEN'), self.dirname)
        if value.endswith('.nc'):
            dest += '.nc'
        self.update_link(value, dest)

    rho_fname = charge_density_fname

    _input_wavefunction_fname = ''
    @property
    def input_wavefunction_fname(self):
        return self._input_wavefunction_fname
    
    @input_wavefunction_fname.setter
    def input_wavefunction_fname(self, value):
        self._input_wavefunction_fname = value
        dest = os.path.relpath(self.get_idat('WFK'), self.dirname)
        self.update_link(value, dest)

    @property
    def exchange_correlation_potential_fname(self):
        return self.get_odat('VXC')

    vxc_fname = exchange_correlation_potential_fname

