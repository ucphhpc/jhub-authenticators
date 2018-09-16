#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Juptyer Development Team.
# Distributed under the terms of the Modified BSD License.

# -----------------------------------------------------------------------------
# Minimal Python version sanity check (from IPython/Jupyterhub)
# -----------------------------------------------------------------------------

from __future__ import print_function

import os

from setuptools import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))

# Get the current package version.
version_ns = {}
with open(pjoin(here, 'version.py')) as f:
    exec(f.read(), {}, version_ns)

long_description = open('README.rst').read()

setup(
    name='jhub-authenticators',
    version=version_ns['__version__'],
    long_description=long_description,
    author="Rasmus Munk",
    author_email="munk1@live.dk",
    packages=['jhubauthenticators'],
    url="https://github.com/rasmunk/jhub-authenticators",
    license="GPLv3",
    platforms="Linux, Mac OS X",
    keywords=['Interactive', 'Interpreter', 'Shell', 'Web'],
    install_requires=[
        'jupyterhub>=0.9.2',
        'docutils>=0.14'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
