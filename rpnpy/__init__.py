import sys

from .calculator import Calculator

if sys.version_info < (3,):
    raise Exception('Calculator needs Python 3.')

# Note that the version string must have the following format, otherwise it
# will not be found by the version() function in ../setup.py
#
# Remember to update ../CHANGELOG.md describing what's new in each version.
__version__ = '1.0.29'

# Keep Python linters quiet.
_ = Calculator

__all__ = ['Calculator']
