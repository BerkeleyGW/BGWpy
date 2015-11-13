
BGWpy is a python module to operate BerkeleyGW.


Documentation
=============

We recommend learning the basic usage from the examples provided
with the source distribution in ~BGWpy/Examples/. The docstrings
of the various objects also contain information and can be accessed
from a python interpreter with
    >>> help(BGWpy.<object>)

or from ipython with
    In [1]: BGWpy.<object>?


Requirements
============

The following software and modules are required to use BGWpy.

  * python 2.7 required (Python 3 not supported at the moment) 
  * numpy 1.6+      (http://www.scipy.org/)
  * pymatgen 3.0+   (http://pymatgen.org/)
  * BerkeleyGW      (http://www.berkeleygw.org/)

Note that the binary executables of BerkeleyGW must be found
in your PATH environment variable.


Installing
==========

Once you have satisfied the requirements, install the package with

  python setup.py build
  python setup.py install


License
=======

This software is free to use under the BSD license.
See license.txt for more information.
