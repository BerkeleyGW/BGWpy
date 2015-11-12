
from numpy import array

from ..util.F90io import Namelist

class PW2BGWInput(Namelist):

    _ngkpt = array([1,1,1])
    _kshift = array([.0,.0,.0])
    _qshift = array([.0,.0,.0])

    def __init__(self, *args, **kwargs):

        super(Namelist, self).__init__(name='input_pw2bgw', *args, **kwargs)

    @property
    def ngkpt(self):
        return self._ngkpt

    @ngkpt.setter
    def ngkpt(self, ngkpt):
        self._ngkpt = array(ngkpt)
        self['wfng_nk1'] = ngkpt[0]
        self['wfng_nk2'] = ngkpt[1]
        self['wfng_nk3'] = ngkpt[3]
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
        self['wfng_dk3'] = self.kqshift[3]

