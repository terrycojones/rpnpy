#!/usr/bin/env python

from setuptools import setup


# Modified from http://stackoverflow.com/questions/2058802/
# how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package and
# https://stackoverflow.com/questions/6786555/
# automatic-version-number-both-in-setup-py-setuptools-and-source-code#7502821

def version():
    import os
    import re

    init = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'rpnpy', '__init__.py')
    with open(init) as fp:
        initData = fp.read()
    match = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]",
                      initData, re.M)
    if match:
        return match.group(1)
    else:
        raise RuntimeError('Unable to find version string in %r.' % init)


setup(name='rpnpy',
      version=version(),
      packages=['rpnpy'],
      include_package_data=False,
      url='https://github.com/terrycojones/rpnpy',
      download_url='https://github.com/terrycojones/rpnpy',
      author='Terry Jones',
      author_email='tcj25@cam.ac.uk',
      keywords=['python reverse polish calculator'],
      classifiers=[
          'Programming Language :: Python :: 3',
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      license='MIT',
      scripts=['rpn.py'],
      description=('Control an RPN calculator from Python.'),
      install_requires=[
          'engineering_notation'
      ],
      extras_require={
        'dev': [
            'flake8',
            'pytest',
        ]
      })
