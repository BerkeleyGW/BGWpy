from __future__ import print_function
import sys
import os
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
__version__ = '3.0.0'

# author and author_email should be a single string, not a list, but we can put
# multiple authors / emails by separating them by commas inside the string.
# If you contributed to this package, add your name and email. Don't be shy!
author = 'Gabriel Antonius'
author_email = 'gabriel.antonius@gmail.com'


# Requirements
install_requires = [
    'numpy >=1.6',
    'pymatgen >=4.0',
    ]

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def get_package_data():
    package_data={'BGWpy': ['data/structures/*', 'data/pseudos/*']}
    return package_data

def install_user_configuration():
    user_config = os.path.join('config', 'user_configuration.py')
    dest = os.path.join('BGWpy', 'config', 'user_configuration.py')
    if os.path.exists(user_config):
        shutil.copy(user_config, dest)

# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #

install_user_configuration()

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
      package_data      = get_package_data(),
      )

if __name__ == "__main__":
    setup(**setup_args)

