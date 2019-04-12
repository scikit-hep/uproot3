#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

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

    before = """.. image:: https://raw.githubusercontent.com/scikit-hep/uproot/master/docs/source/logo-300px.png
   :alt: uproot
   :target: https://github.com/scikit-hep/uproot

"""

    start = description.index(".. inclusion-marker-1-5-do-not-remove")
    stop = description.index(".. inclusion-marker-3-do-not-remove")
    middle = description[start:stop].strip()
    start_replaceplots = middle.index(".. inclusion-marker-replaceplots-start")
    stop_replaceplots = middle.index(".. inclusion-marker-replaceplots-stop") + len(".. inclusion-marker-replaceplots-stop")
    middle = middle[:start_replaceplots] + """
.. image:: https://raw.githubusercontent.com/scikit-hep/uproot/master/docs/root-none-muon.png
   :width: 350 px
.. image:: https://raw.githubusercontent.com/scikit-hep/uproot/master/docs/rootnumpy-none-muon.png
   :width: 350 px
""" + middle[stop_replaceplots:]

    after = """

Tutorial
========

See the `project homepage <https://github.com/scikit-hep/uproot>`__ for a `tutorial <https://github.com/scikit-hep/uproot#tutorial>`__.

Run `that tutorial <https://mybinder.org/v2/gh/scikit-hep/uproot/master?urlpath=lab/tree/binder%2Ftutorial.ipynb>`__ on Binder.

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
    return before + middle + after

setup(name = "uproot",
      version = get_version(),
      packages = find_packages(exclude = ["tests"]),
      scripts = [],
      description = "ROOT I/O in pure Python and Numpy.",
      long_description = get_description(),
      author = "Jim Pivarski (IRIS-HEP)",
      author_email = "pivarski@princeton.edu",
      maintainer = "Jim Pivarski (IRIS-HEP)",
      maintainer_email = "pivarski@princeton.edu",
      url = "https://github.com/scikit-hep/uproot",
      download_url = "https://github.com/scikit-hep/uproot/releases",
      license = "BSD 3-clause",
      test_suite = "tests",
      install_requires = ["numpy>=1.13.1", "awkward>=0.9.0", "uproot-methods>=0.5.0", "cachetools"],
      setup_requires = ["pytest-runner"],
      tests_require = ["pytest>=3.9", "pkgconfig", "lz4", 'backports.lzma;python_version<"3.3"', "mock", "requests"],
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
