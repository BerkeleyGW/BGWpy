<a href="url"><img src="https://github.com/BerkeleyGW/BGWpy/blob/master/dev/logo/BGWpy.png" height="300" ></a><br clear="all" />

A python module to operate BerkeleyGW

## Documentation

We recommend learning the basic usage from the examples provided
with the source distribution in ~BGWpy/Examples/. The docstrings
of the various objects also contain information and can be accessed
from a python interpreter with

    help(BGWpy.<object>)

or from ipython with

    In  [1]: BGWpy.<object>?

## Requirements

- Python 3.10+
- numpy 1.24+
- pymatgen 2024+
- BerkeleyGW 4.0+

Note that the binary executables of BerkeleyGW must be found
in your PATH environment variable.

## Installing

Install using pip:

    pip install BGWpy

Or using uv:

    uv pip install BGWpy

For development, clone the repository and install with dev dependencies:

    git clone https://github.com/BerkeleyGW/BGWpy.git
    cd BGWpy
    uv sync --all-extras

After installation, run the configuration script to generate a runtime
configuration file `~/.BGWpyrc`:

    BGWpy_make_config_file.py

You can then modify this file as needed. Most options represent default
values and can be overridden when using the module.

## License

This software is free to use under the BSD license.
See license.txt for more information.
