"""
Legacy setup.py for backward compatibility.

For new installations, please use:
    pip install .

This setup.py is maintained for backward compatibility only.
Modern packaging configuration is in pyproject.toml.
"""

import warnings

from setuptools import setup

warnings.warn(
    "setup.py is deprecated. Please use 'pip install .' instead, "
    "which will use pyproject.toml for configuration.",
    DeprecationWarning,
    stacklevel=2,
)

# All configuration is now in pyproject.toml
# This file exists only for backward compatibility
setup()
