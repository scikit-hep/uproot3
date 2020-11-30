#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

import sys
import os.path

from setuptools import find_packages
from setuptools import setup

def get_version():
    g = {}
    exec(open(os.path.join("uproot3", "version.py")).read(), g)
    return g["__version__"]

def get_description():
    description = open("README.rst", "rb").read().decode("utf8", "ignore")

    before = """.. image:: https://raw.githubusercontent.com/scikit-hep/uproot3/master/docs/source/logo-300px.png
   :alt: uproot
   :target: https://github.com/scikit-hep/uproot3

"""

    start = description.index(".. inclusion-marker-1-5-do-not-remove")
    stop = description.index(".. inclusion-marker-3-do-not-remove")
    middle = description[start:stop].strip()
    start_replaceplots = middle.index(".. inclusion-marker-replaceplots-start")
    stop_replaceplots = middle.index(".. inclusion-marker-replaceplots-stop") + len(".. inclusion-marker-replaceplots-stop")
    middle = middle[:start_replaceplots] + """
.. image:: https://raw.githubusercontent.com/scikit-hep/uproot3/master/docs/root-none-muon.png
   :width: 350 px
.. image:: https://raw.githubusercontent.com/scikit-hep/uproot3/master/docs/rootnumpy-none-muon.png
   :width: 350 px
""" + middle[stop_replaceplots:]

    after = """

Tutorial
========

See the `project homepage <https://github.com/scikit-hep/uproot3>`__ for a `tutorial <https://github.com/scikit-hep/uproot3#tutorial>`__.

Run `that tutorial <https://mybinder.org/v2/gh/scikit-hep/uproot3/master?urlpath=lab/tree/binder%2Ftutorial.ipynb>`__ on Binder.

**Tutorial contents:**

* `Introduction <https://github.com/scikit-hep/uproot3#introduction>`__
* `What is Uproot? <https://github.com/scikit-hep/uproot3#what-is-uproot>`__
* `Exploring a file <https://github.com/scikit-hep/uproot3#exploring-a-file>`__

  - `Compressed objects in ROOT files <https://github.com/scikit-hep/uproot3#compressed-objects-in-root-files>`__
  - `Exploring a TTree <https://github.com/scikit-hep/uproot3#exploring-a-ttree>`__
  - `Some terminology <https://github.com/scikit-hep/uproot3#some-terminology>`__

* `Reading arrays from a TTree <https://github.com/scikit-hep/uproot3#reading-arrays-from-a-ttree>`__
* `Caching data <https://github.com/scikit-hep/uproot3#caching-data>`__

  - `Automatically managed caches <https://github.com/scikit-hep/uproot3#automatically-managed-caches>`__
  - `Caching at all levels of abstraction <https://github.com/scikit-hep/uproot3#caching-at-all-levels-of-abstraction>`__

* `Lazy arrays <https://github.com/scikit-hep/uproot3#lazy-arrays>`__

  - `Lazy array of many files <https://github.com/scikit-hep/uproot3#lazy-array-of-many-files>`__
  - `Lazy arrays with caching <https://github.com/scikit-hep/uproot3#lazy-arrays-with-caching>`__
  - `Lazy arrays as lightweight skims <https://github.com/scikit-hep/uproot3#lazy-arrays-as-lightweight-skims>`__
  - `Lazy arrays in Dask <https://github.com/scikit-hep/uproot3#lazy-arrays-in-dask>`__

* `Iteration <https://github.com/scikit-hep/uproot3#iteration>`__

  - `Filenames and entry numbers while iterating <https://github.com/scikit-hep/uproot3#filenames-and-entry-numbers-while-iterating>`__
  - `Limiting the number of entries to be read <https://github.com/scikit-hep/uproot3#limiting-the-number-of-entries-to-be-read>`__
  - `Controlling lazy chunk and iteration step sizes <https://github.com/scikit-hep/uproot3#controlling-lazy-chunk-and-iteration-step-sizes>`__
  - `Caching and iteration <https://github.com/scikit-hep/uproot3#caching-and-iteration>`__

* `Changing the output container type <https://github.com/scikit-hep/uproot3#changing-the-output-container-type>`__
* `Filling Pandas DataFrames <https://github.com/scikit-hep/uproot3#filling-pandas-dataframes>`__
* `Selecting and interpreting branches <https://github.com/scikit-hep/uproot3#selecting-and-interpreting-branches>`__

  - `TBranch interpretations <https://github.com/scikit-hep/uproot3#tbranch-interpretations>`__
  - `Reading data into a preexisting array <https://github.com/scikit-hep/uproot3#reading-data-into-a-preexisting-array>`__
  - `Passing many new interpretations in one call <https://github.com/scikit-hep/uproot3#passing-many-new-interpretations-in-one-call>`__
  - `Multiple values per event: fixed size arrays <https://github.com/scikit-hep/uproot3#multiple-values-per-event-fixed-size-arrays>`__
  - `Multiple values per event: leaf-lists <https://github.com/scikit-hep/uproot3#multiple-values-per-event-leaf-lists>`__
  - `Multiple values per event: jagged arrays <https://github.com/scikit-hep/uproot3#multiple-values-per-event-jagged-arrays>`__
  - `Jagged array performance <https://github.com/scikit-hep/uproot3#jagged-array-performance>`__
  - `Special physics objects: Lorentz vectors <https://github.com/scikit-hep/uproot3#special-physics-objects-lorentz-vectors>`__
  - `Variable-width values: strings <https://github.com/scikit-hep/uproot3#variable-width-values-strings>`__
  - `Arbitrary objects in TTrees <https://github.com/scikit-hep/uproot3#arbitrary-objects-in-ttrees>`__
  - `Doubly nested jagged arrays (i.e. std::vector<std::vector<T>>) <https://github.com/scikit-hep/uproot3#doubly-nested-jagged-arrays-ie-stdvectorstdvectort>`__

* `Parallel array reading <https://github.com/scikit-hep/uproot3#parallel-array-reading>`__
* `Histograms, TProfiles, TGraphs, and others <https://github.com/scikit-hep/uproot3#histograms-tprofiles-tgraphs-and-others>`__
* `Creating and writing data to ROOT files <https://github.com/scikit-hep/uproot3#creating-and-writing-data-to-root-files>`__

  - `Writing histograms <https://github.com/scikit-hep/uproot3#writing-histograms>`__
  - `Writing TTrees <https://github.com/scikit-hep/uproot3#writing-ttrees>`__
"""
    return before + middle + after

setup(name = "uproot3",
      version = get_version(),
      packages = find_packages(exclude = ["tests"]),
      scripts = [],
      description = "ROOT I/O in pure Python and Numpy.",
      long_description = get_description(),
      author = "Jim Pivarski (IRIS-HEP)",
      author_email = "pivarski@princeton.edu",
      maintainer = "Jim Pivarski (IRIS-HEP)",
      maintainer_email = "pivarski@princeton.edu",
      url = "https://github.com/scikit-hep/uproot3",
      download_url = "https://github.com/scikit-hep/uproot3/releases",
      license = "BSD 3-clause",
      test_suite = "tests",
      python_requires = ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
      install_requires = ["numpy>=1.13.1", "awkward0", "uproot3-methods", "cachetools"],
      setup_requires = ["pytest-runner"],
      extras_require = {
          "testing": ["pytest>=3.9", "pkgconfig", "lz4", "zstandard", 'backports.lzma;python_version<"3.3"', "xxhash", "mock", "requests"],
          "compress": ["lz4", "zstandard", 'backports.lzma;python_version<"3.3"', "xxhash"],
      },
      classifiers = [
          "Development Status :: 7 - Inactive",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: BSD License",
          "Operating System :: MacOS",
          "Operating System :: POSIX",
          "Operating System :: Unix",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
          "Topic :: Scientific/Engineering",
          "Topic :: Scientific/Engineering :: Information Analysis",
          "Topic :: Scientific/Engineering :: Mathematics",
          "Topic :: Scientific/Engineering :: Physics",
          "Topic :: Software Development",
          "Topic :: Utilities",
          ],
      platforms = "Any",
      )
