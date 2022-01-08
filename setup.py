from __future__ import print_function
import sys
import os
from glob import glob
import shutil

try:
    import setuptools
except ImportError:
    sys.stderr.write(
    "Please install setuptools before running this script. Exiting.")
    sys.exit(1)

from setuptools import setup, find_packages


# --------------------------------------------------------------------------- #
# Basic project information
# --------------------------------------------------------------------------- #

name = 'BGWpy'
description = 'Interface BerkeleyGW flows in python.'
license = 'BSD'
url = 'https://github.com/BerkeleyGW/BGWpy'
__version__ = '3.2.3'

# author and author_email should be a single string, not a list, but we can put
# multiple authors / emails by separating them by commas inside the string.
# If you contributed to this package, add your name and email. Don't be shy!
author = 'Gabriel Antonius'
author_email = 'gabriel.antonius@gmail.com'


# Requirements
install_requires = [
    'numpy >=1.6',
    'pymatgen >=2021',
    ]

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def find_package_data():
    package_data={'BGWpy': ['data/structures/*', 'data/pseudos/*']}
    return package_data

def find_data_files():
    return [('config', ['config/BGWpyrc'])]

def find_scripts():
    scripts = []
    for fname in glob(os.path.join('BGWpy', 'scripts', "*.py")):
        if os.path.basename(fname) != '__init__.py':
            scripts.append(fname)
    return scripts

def cleanup():
    print('Cleaning up')
    shutil.rmtree('BGWpy.egg-info', ignore_errors=True)
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('__pycache__', ignore_errors=True)

# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #

setup_args = dict(
      name              = name,
      version           = __version__,
      description       = description,
      author            = author,
      author_email      = author_email,
      license           = license,
      url               = url,
      install_requires  = install_requires,
      packages          = find_packages(),
      package_data      = find_package_data(),
      data_files        = find_data_files(),
      scripts           = find_scripts(), 
      )

if __name__ == "__main__":
    setup(**setup_args)

