from __future__ import print_function
import os

from .abinittask import AbinitTask

__all__ = ['AbinitScfTask']

class AbinitScfTask(AbinitTask):
    """Charge density calculation."""

    _TASK_NAME = 'SCF'

    _input_fname = 'scf.in'
    _output_fname = 'scf.out'

    def __init__(self, dirname, **kwargs):
        """
        Arguments
        ---------

        dirname : str
            Directory in which the files are written and the code is executed.
            Will be created if needed.


        Keyword arguments
        -----------------

        ecut : float
            Kinetic energy cut-off, in Hartree.
        tolvrs : float (1e-10)
            Tolerance on residual potential used as a convergence criterion
            for the SCF cycle.
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
        input_variables : dict
            Any other input variables for the Abinit input file.

        See also:
            BGWpy.Abinit.abinittask.AbinitTask


        Properties
        ----------

        charge_density_fname : str
            The charge density file produced by Abinit.

        vxc_fname : str
            The xc potential file produced by Abinit.

        """

        kwargs.setdefault('prefix', 'scf')

        super(AbinitScfTask, self).__init__(dirname, **kwargs)

        self.input.set_variables(self.get_scf_variables(**kwargs))

    @staticmethod
    def get_scf_variables(**kwargs):
        """Return a dict of variables required for an SCF calculation."""
        variables = dict(
            prtden = 1,
            prtvxc = 1,
            tolvrs = kwargs.get('tolvrs', 1e-10),
            ecut = kwargs.get('ecut'),
            )
        return variables

    @property
    def charge_density_fname(self):
        #return os.path.join(self.dirname, self.get_odat('DEN'))
        return self.get_odat('DEN')

    rho_fname = charge_density_fname

    @property
    def xc_potential_fname(self):
        #return os.path.join(self.dirname, self.get_odat('DEN'))
        return self.get_odat('VXC')

    vxc_fname = xc_potential_fname

