
from numpy import array

from ..core import Namelist

class PW2BGWInput(Namelist):

    _ngkpt = array([1,1,1])
    _kshift = array([.0,.0,.0])
    _qshift = array([.0,.0,.0])

    def __init__(self, *args, **kwargs):

        ngkpt = kwargs.pop('ngkpt', 3*[.0])
        kshift = kwargs.pop('kshift', 3*[.0])
        qshift = kwargs.pop('qshift', 3*[.0]) 

        super(PW2BGWInput, self).__init__('input_pw2bgw', *args, **kwargs)

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

