#!/usr/bin/env python

from setuptools import setup

# This needs to have the following format - see Makefile 'upload' target.
VERSION = '1.0.3'

setup(name='rpnpy',
      version=VERSION,
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
      extras_require={
        'dev': [
            'flake8',
            'pytest',
        ]
      })
