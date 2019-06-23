import sys

from .calculator import Calculator

if sys.version_info < (3,):
    raise Exception('Calculator needs Python 3.')

# Note that the version string must have the following format, otherwise it
# will not be found by the version() function in ../setup.py
#
# Actually, the code in ../setup.py doesn't work for me when running pip
# install (as of 2019-06-23) so I've for now put the version directly into that
# file. Which means you need to manually keep the two in sync until it gets
# figured out. See https://github.com/terrycojones/rpnpy/issues/1
#
# Remember to update ../CHANGELOG.md describing what's new in each version.
__version__ = '1.0.27'

# Keep Python linters quiet.
_ = Calculator

__all__ = ['Calculator']
