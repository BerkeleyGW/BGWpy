from __future__ import print_function
import os

from numpy import array
from ..core import Namelist
from .qetask import QeTask

from ..config import flavors

# Public
__all__ = ['Qe2BgwTask', 'Qe2BgwInput']


class Qe2BgwInput(Namelist):

    _ngkpt = array([1,1,1])
    _kshift = array([.0,.0,.0])
    _qshift = array([.0,.0,.0])

    #_kptgrid_alias =  ['ngkpt']
    #_kshift_alias =  ['kshift', 'shiftk']
    #_qshift_alias =  ['qshift', 'shiftq']

    def __init__(self, *args, **kwargs):

        ngkpt = kwargs.pop('ngkpt', 3*[.0])
        kshift = kwargs.pop('kshift', 3*[.0])
        qshift = kwargs.pop('qshift', 3*[.0]) 

        super(Qe2BgwInput, self).__init__('input_pw2bgw', *args, **kwargs)

        # Sort the variables so that they look nice in the input file.
        prefered_order = [
            'prefix',
            'real_or_complex',
            'wfng_flag',
            'wfng_file',
            'rhog_flag',
            'rhog_file',
            'vxc_flag',
            'vxc_file',
            'vxcg_flag',
            'vxcg_file',
            'vxc_offdiag_nmin',
            'vxc_offdiag_nmax',
            'vxc_diag_nmin',
            'vxc_diag_nmax',
            'wfng_kgrid',
            ]
        for key in prefered_order:
            value = self.pop(key, None)
            if value:
                self[key] = value
        for key in self.keys():
            if key not in prefered_order:
                value = self.pop(key)
                self[key] = value

        # Maybe let these be handled by PW2BGWTask
        self.ngkpt = ngkpt
        self.kshift = kshift
        self.qshift = qshift

    @property
    def ngkpt(self):
        return self._ngkpt

    @ngkpt.setter
    def ngkpt(self, ngkpt):
        self._ngkpt = array(ngkpt)
        self['wfng_nk1'] = ngkpt[0]
        self['wfng_nk2'] = ngkpt[1]
        self['wfng_nk3'] = ngkpt[2]
        self._set_kqshift()

    @property
    def kshift(self):
        return self._kshift

    @kshift.setter
    def kshift(self, kshift):
        self._kshift = array(kshift)
        self._set_kqshift()

    @property
    def qshift(self):
        return self._qshift

    @qshift.setter
    def qshift(self, qshift):
        self._qshift = array(qshift)
        self._set_kqshift()

    @property
    def kqshift(self):
        return self.kshift + self.qshift * self.ngkpt

    def _set_kqshift(self):
        self['wfng_dk1'] = self.kqshift[0]
        self['wfng_dk2'] = self.kqshift[1]
        self['wfng_dk3'] = self.kqshift[2]


class Qe2BgwTask(QeTask):
    """Wavefunctions convertion."""

    _TASK_NAME = 'PW2BGW'

    _input_fname = 'wfn.pp.in'
    _output_fname = 'wfn.pp.out'

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


        Properties
        ----------

        wfn_fname : str
            Path to the wavefunction file produced.
        rho_fname : str
            Path to the density file produced.
        vxc_dat_fname : str
            Path to the vxc.dat file produced.
        """

        kwargs.setdefault('runscript_fname', 'pw2bgw.run.sh')

        super(Qe2BgwTask, self).__init__(dirname, **kwargs)

        self.ngkpt = kwargs.pop('ngkpt')
        self.kshift = kwargs.get('kshift', 3*[.0])
        self.qshift = kwargs.get('qshift', 3*[.0])


        # Maybe let the defaults be handled by PW2BGWInput

        # Input file
        defaults = dict(
            ngkpt       = self.ngkpt,
            kshift      = self.kshift,
            qshift      = self.qshift,
            wfng_file   = kwargs.get('wfn_fname', 'wfn.cplx'),
            real_or_complex = 2 if flavors['flavor_complex'] else 1,
            wfng_flag   = True,
            wfng_kgrid  = True,
            )

        rho_defaults = dict(
            rhog_flag = True,
            rhog_file = 'rho.real',
            vxcg_flag = False,
            vxcg_file = 'vxc.real',
            vxc_flag = True,
            vxc_file = 'vxc.dat',
            vxc_diag_nmin = 1,
            vxc_diag_nmax = kwargs.get('nbnd', 1),
            vxc_offdiag_nmin = 0,
            vxc_offdiag_nmax = 0,
            )

        if kwargs.get('rho_fname') or kwargs.get('rhog_flag'):
            defaults.update(rho_defaults)

        variables = dict()
        for key, value in defaults.items():
            variables[key] = kwargs.get(key, value)

        self.input = Qe2BgwInput(prefix=self.prefix, **variables)

        # Have to make sure the properties are set correctly.
        if 'wfn_fname' in kwargs:
            self.wfn_fname = kwargs['wfn_fname']
        elif 'wfng_file' in kwargs:
            self.wfn_fname = kwargs['wfng_file']
        if 'rho_fname' in kwargs:
            self.rho_fname = kwargs['rho_fname']
        if 'vxc_dat_fname' in kwargs:
            self.vxc_dat_fname = kwargs['vxc_dat_fname']

        self.input.fname = self._input_fname

        # Run script
        self.runscript['PW2BGW'] = 'pw2bgw.x'
        self.runscript.append('$MPIRUN $PW2BGW $PWFLAGS -in {} &> {}'.format(
                              self._input_fname, self._output_fname))

    _wfn_fname = 'wfn.cplx'
    @property
    def wfn_fname(self):
        return os.path.join(self.dirname, self._wfn_fname)
    
    @wfn_fname.setter
    def wfn_fname(self, value):
        self._wfn_fname = value
        self.input['wfng_file'] = value
    
    _rho_fname = 'rho.real'
    @property
    def rho_fname(self):
        return os.path.join(self.dirname, self._rho_fname)
    
    @rho_fname.setter
    def rho_fname(self, value):
        self._rho_fname = value
        self.input['rhog_file'] = value
    
    _vxc_dat_fname = 'vxc.dat'
    @property
    def vxc_dat_fname(self):
        return os.path.join(self.dirname, self._vxc_dat_fname)
    
    @vxc_dat_fname.setter
    def vxc_dat_fname(self, value):
        self._vxc_dat_fname = value
        self.input['vxc_file'] = value

