"""Abinit to BGW interface."""
import os
import subprocess
from numpy import array
from ..core import fortran_str
from ..core import BasicInputFile
from .abinittask import AbinitTask

__all__ = ['Abi2BgwInput', 'Abi2BgwTask']


# Note
# The implementation of abi2bgw is different from that of pw2bgw.
# Here the kpoint grid is handled by the task rather than the input.

class Abi2BgwInput(BasicInputFile):

    def __init__(self, **kwargs):
        """
        Keyword arguments
        -----------------
        wfng_file_abi : str
            Name of the wfn file produced by Abinit. (_WFK)
        wfng_flag : bool
            Activate the output of the wavefunction for BGW.
        wfng_file : 
            Name of the wfn file for BGW.
        rhog_file_abi : str
            Name of the density file produced by Abinit. (_DEN)
        rhog_flag : bool
            Activate the output of the density for BGW.
        rhog_file : str
            Name of the density file for BGW.
        vxcg_file_abi : str
            Name of the xc potential file produced by Abinit. (_VXC)
        vxcg_flag : bool
            Activate the output of the xc potential for BGW.
        vxcg_file : str
            Name of the xc potential file for BGW.
        wfng_nk1 : int
            Number of k-point division along direction 1.
        wfng_nk2 : int
            Number of k-point division along direction 2.
        wfng_nk3 : int
            Number of k-point division along direction 3.
        wfng_dk1 : float
            k-point shift along direction 1.
        wfng_dk2 : float
            k-point shift along direction 2.
        wfng_dk3 : float
            k-point shift along direction 3.
        cell_symmetry : int
            Cell symmetry. 0 = cubic, 1 = hexagonal.
        symrel_file_flag : bool
            Write symmetry matrices in file.
        """

        super(Abi2BgwInput, self).__init__(fname = kwargs.get('fname', 'abi2bgw.in'))

        #self.fname = kwargs.get('fname', 'abi2bgw.in')

        # Flags and options
        self['wfng_flag']        = kwargs.get('wfng_flag', True)
        self['rhog_flag']        = kwargs.get('rhog_flag', False)
        self['vxcg_flag']        = kwargs.get('vxcg_flag', False)
        self['symrel_file_flag'] = kwargs.get('symrel_file_flag', False)
        self['cell_symmetry']    = kwargs.get('cell_symmetry', 0)

        # Output files
        self._wfn_fname   = kwargs.get('wfng_file', 'wfn.cplx')
        self['wfng_file'] = self._wfn_fname
        self._rho_fname   = kwargs.get('rhog_file', 'rho.cplx')
        self['rhog_file'] = self._rho_fname
        self._vxc_fname   = kwargs.get('vxcg_file', 'vxc.cplx')
        self['vxcg_file'] = self._vxc_fname

        # Input files
        self['wfng_file_abi'] = kwargs.get('wfng_file_abi')
        self['rhog_file_abi'] = kwargs.get('rhog_file_abi')
        self['vxcg_file_abi'] = kwargs.get('vxcg_file_abi')

        # k-points grid
        for key in ('wfng_nk1', 'wfng_nk2', 'wfng_nk3'):
            self[key] = kwargs.get(key)
                    
        for key in ('wfng_dk1', 'wfng_dk2', 'wfng_dk3'):
            self[key] = kwargs.get(key, 0.)

    def __str__(self):

        # The keyword order is rigid for abi2bgw.
        keys = [
            'wfng_file_abi',
            'wfng_flag',
            'wfng_file',
            'wfng_nk1',
            'wfng_nk2',
            'wfng_nk3',
            'wfng_dk1',
            'wfng_dk2',
            'wfng_dk3',
            'rhog_file_abi',
            'rhog_flag',
            'rhog_file',
            'cell_symmetry',
            'symrel_file_flag',
            'vxcg_file_abi',
            'vxcg_flag',
            'vxcg_file',
            ]

        S = ''
        for key in keys:
            S += '{} {}\n'.format(key, fortran_str(self[key]))
        return S


# =========================================================================== #


class Abi2BgwTask(AbinitTask):
    """Wavefunctions convertion."""

    _TASK_NAME = 'Abi2BGW'
    _TAG_JOB_COMPLETED = 'Calculation completed'

    _input_fname = 'abi2bgw.in'
    _output_fname = 'abi2bgw.out'

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
        ngkpt : list(3), float
            K-points grid. Number of k-points along each primitive vector
            of the reciprocal lattice.
        kshift : list(3), float, optional
            Relative shift of the k-points grid along each direction,
            as a fraction of the smallest division along that direction.
        qshift : list(3), float, optional
            Absolute shift of the k-points grid along each direction.
        wfn_fname : str ('wfn.cplx'), optional
            Name of the output wavefunction file.
        rhog_flag : bool (False), optional
            If True, will activacte the output of the density and vxc.
        rho_fname : str, optional
            Name of the ouput density file.
            If provided, will activacte the output of the density and vxc.
        nbnd : int, optional
            Number of bands for which vxc should be computed.
            Only if output of the density and vxc is active.

        See also: BGWpy.Abinit.Abi2BgwInput

        Properties
        ----------

        wfn_fname : str
            Path to the wavefunction file produced.
        rho_fname : str
            Path to the density file produced.
        vxc_fname : str
            Path to the vxc file produced.
        """

        kwargs.setdefault('runscript_fname', 'abi2bgw.run.sh')

        super(Abi2BgwTask, self).__init__(dirname, **kwargs)

        self.input = Abi2BgwInput(**kwargs)
        self.input.fname = self._input_fname

        # TODO setter functions
        self.ngkpt = kwargs.pop('ngkpt')
        self.kshift = kwargs.get('kshift', 3*[.0])
        self.qshift = kwargs.get('qshift', 3*[.0])

        if kwargs.get('rhog_fname') or kwargs.get('rhog_file_abi'):
            self.set_rho()

        self.wfn_fname = kwargs.pop('wfn_fname', 'dummy')
        self.rho_fname = kwargs.pop('rho_fname', 'dummy')
        self.vxc_fname = kwargs.pop('vxc_fname', 'dummy')

        # Run script
        self.runscript['ABI2BGW'] = 'abi2bgw.x'
        del self.runscript.main[:]
        self.runscript.append('$ABI2BGW {} >& {}'.format(
                              self._input_fname, self._output_fname))

    def write(self):

        subprocess.call(['mkdir', '-p', self.dirname])
        with self.exec_from_dirname():
            self.runscript.write()

        with self.exec_from_dirname():
            self.input.write()

    _wfn_fname = 'wfn.cplx'
    @property
    def wfn_fname(self):
        return os.path.join(self.dirname, self._wfn_fname)
    
    @wfn_fname.setter
    def wfn_fname(self, value):
        #self._wfn_fname = value
        self.input['wfng_file_abi'] = os.path.relpath(value, self.dirname)
    
    _rho_fname = 'rho.cplx'
    @property
    def rho_fname(self):
        return os.path.join(self.dirname, self._rho_fname)
    
    @rho_fname.setter
    def rho_fname(self, value):
        #self._rho_fname = value
        self.input['rhog_file_abi'] = os.path.relpath(value, self.dirname)
    
    _vxc_fname = 'vxc.cplx'
    @property
    def vxc_fname(self):
        return os.path.join(self.dirname, self._vxc_fname)
    
    @vxc_fname.setter
    def vxc_fname(self, value):
        #self._vxc_fname = value
        self.input['vxcg_file_abi'] = os.path.relpath(value, self.dirname)

    _ngkpt = 3*[1]
    @property
    def ngkpt(self):
        return self._ngkpt

    @ngkpt.setter
    def ngkpt(self, ngkpt):
        self._ngkpt = array(ngkpt)
        self.input['wfng_nk1'] = ngkpt[0]
        self.input['wfng_nk2'] = ngkpt[1]
        self.input['wfng_nk3'] = ngkpt[2]
        self._set_kqshift()

    _kshift = 3*[.0]
    @property
    def kshift(self):
        return self._kshift

    shiftk = kshift  # Alias

    @kshift.setter
    def kshift(self, kshift):
        self._kshift = array(kshift)
        self._set_kqshift()

    _qshift = 3*[.0]
    @property
    def qshift(self):
        return self._qshift

    @qshift.setter
    def qshift(self, qshift):
        self._qshift = array(qshift)
        self._set_kqshift()

    shiftq = qshift  # Alias

    @property
    def kqshift(self):
        return self.kshift + self.qshift * self.ngkpt

    def _set_kqshift(self):
        self.input['wfng_dk1'] = self.kqshift[0]
        self.input['wfng_dk2'] = self.kqshift[1]
        self.input['wfng_dk3'] = self.kqshift[2]

    def set_rho(self):
        self.input['rhog_flag'] = True

    @property
    def output_fname(self):
        return os.path.join(self.dirname, self._output_fname)

