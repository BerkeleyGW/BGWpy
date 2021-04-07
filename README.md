
<a href="url"><img src="https://github.com/BerkeleyGW/BGWpy/blob/master/dev/logo/BGWpy.png" height="300" ></a><br clear="all" />

A python module to operate BerkeleyGW


Documentation
-------------

We recommend learning the basic usage from the examples provided
with the source distribution in ~BGWpy/Examples/. The docstrings
of the various objects also contain information and can be accessed
from a python interpreter with

    help(BGWpy.<object>)


or from ipython with

    In  [1]: BGWpy.<object>?


Requirements
------------

The following software and modules are required to use BGWpy.

  * python 3 and python 2 compatible
  * numpy 1.6+      (http://www.scipy.org/)
  * pymatgen 4.0+   (http://pymatgen.org/)
  * BerkeleyGW 1.2+ (http://www.berkeleygw.org/)

Note that the binary executables of BerkeleyGW must be found
in your PATH environment variable.


Installing
----------

Once you have satisfied the requirements, install the package with

  python setup.py install

You may then run the script `BGWpy_make_config_file.py`
to generate a runtime configuration file `~/.BGWpyrc`
which you can modify. Most options in this file
represent default values, and can be overridden when using the module.


License
-------

This software is free to use under the BSD license.
See license.txt for more information.

