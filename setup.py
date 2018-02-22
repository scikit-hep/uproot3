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
    description = open("README.rst").read()
    start = description.index(".. inclusion-marker-1-5-do-not-remove")
    stop = description.index(".. inclusion-marker-5-do-not-remove")
    before = """.. image:: https://raw.githubusercontent.com/scikit-hep/uproot/master/docs/source/logo-300px.png
   :alt: uproot
   :target: https://github.com/scikit-hep/uproot

"""

    after = """

.. _Exploring a file: https://github.com/scikit-hep/uproot#exploring-a-file
.. _Array-reading parameters: https://github.com/scikit-hep/uproot#array-reading-parameters
.. _Remote files through XRootD: https://github.com/scikit-hep/uproot#remote-files-through-xrootd
.. _Reading only part of a TBranch: https://github.com/scikit-hep/uproot#reading-only-part-of-a-tbranch
.. _Iterating over files (like TChain): https://github.com/scikit-hep/uproot#iterating-over-files-like-tchain
.. _Non-flat TTrees\: jagged arrays and more: https://github.com/scikit-hep/uproot#non-flat-ttrees-jagged-arrays-and-more
.. _Non-TTrees\: histograms and more: https://github.com/scikit-hep/uproot#non-ttrees-histograms-and-more
.. _Caching data: https://github.com/scikit-hep/uproot#caching-data
.. _Parallel processing: https://github.com/scikit-hep/uproot#parallel-processing
.. _Connectors to other packages: https://github.com/scikit-hep/uproot#connectors-to-other-packages
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
      install_requires = ["numpy"],
      tests_require = ["lz4", "backports.lzma", "futures"] if sys.version_info[0] <= 2 else ["lz4"],
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
