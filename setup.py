#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import os.path

from setuptools import find_packages
from setuptools import setup

def get_version():
    g = {}
    exec(open(os.path.join("uproot", "version.py")).read(), g)
    return g["__version__"]

def get_description():
    description = open("README.rst", "rb").read().decode("utf8", "ignore")
    start = description.index(".. inclusion-marker-1-5-do-not-remove")
    stop = description.index(".. inclusion-marker-3-do-not-remove")
    before = """.. image:: https://raw.githubusercontent.com/scikit-hep/uproot/master/docs/source/logo-300px.png
   :alt: uproot
   :target: https://github.com/scikit-hep/uproot

"""

    after = """

Tutorial
========

See the `project homepage <https://github.com/scikit-hep/uproot>`__ for a `tutorial <https://github.com/scikit-hep/uproot#tutorial>`__.

Interactive tutorial
====================

Run `this tutorial <https://mybinder.org/v2/gh/scikit-hep/uproot/master?filepath=binder%2Ftutorial.ipynb>`__ on Binder.

Reference documentation
=======================

* `Opening files <http://uproot.readthedocs.io/en/latest/opening-files.html>`__

  - `uproot.open <http://uproot.readthedocs.io/en/latest/opening-files.html#uproot-open>`__
  - `uproot.xrootd <http://uproot.readthedocs.io/en/latest/opening-files.html#uproot-xrootd>`__
  - `uproot.iterate <http://uproot.readthedocs.io/en/latest/opening-files.html#uproot-iterate>`__

* `ROOT I/O <http://uproot.readthedocs.io/en/latest/root-io.html>`__

  - `uproot.rootio.ROOTDirectory <http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootdirectory>`__
  - `uproot.rootio.ROOTObject <http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootobject>`__
  - `uproot.rootio.ROOTStreamedObject <http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootstreamedobject>`__

* `TTree Handling <http://uproot.readthedocs.io/en/latest/ttree-handling.html>`__

  - `uproot.tree.TTreeMethods <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__
  - `uproot.tree.TBranchMethods <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__

* `Interpretation <http://uproot.readthedocs.io/en/latest/interpretation.html>`__
* `Caches <http://uproot.readthedocs.io/en/latest/caches.html>`__
* `Parallel I/O <http://uproot.readthedocs.io/en/latest/parallel-io.html>`__
"""
    return before + description[start:stop].strip() + after

setup(name = "uproot",
      version = get_version(),
      packages = find_packages(exclude = ["tests"]),
      scripts = [],
      data_files = ["README.rst"],
      description = "ROOT I/O in pure Python and Numpy.",
      long_description = get_description(),
      author = "Jim Pivarski (DIANA-HEP)",
      author_email = "pivarski@fnal.gov",
      maintainer = "Jim Pivarski (DIANA-HEP)",
      maintainer_email = "pivarski@fnal.gov",
      url = "https://github.com/scikit-hep/uproot",
      download_url = "https://github.com/scikit-hep/uproot/releases",
      license = "BSD 3-clause",
      test_suite = "tests",
      install_requires = ["numpy>=1.13.1", "awkward>=0.5.6", "uproot-methods>=0.2.0", "cachetools", "lz4"],
      setup_requires = ["pytest-runner"],
      tests_require = ["pytest", 'backports.lzma;python_version<"3.3"'],
      classifiers = [
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: BSD License",
          "Operating System :: MacOS",
          "Operating System :: POSIX",
          "Operating System :: Unix",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Topic :: Scientific/Engineering",
          "Topic :: Scientific/Engineering :: Information Analysis",
          "Topic :: Scientific/Engineering :: Mathematics",
          "Topic :: Scientific/Engineering :: Physics",
          "Topic :: Software Development",
          "Topic :: Utilities",
          ],
      platforms = "Any",
      )
