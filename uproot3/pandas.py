#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

"""Top-level functions for Pandas."""
from __future__ import absolute_import

import uproot3.tree
from uproot3.source.memmap import MemmapSource
from uproot3.source.xrootd import XRootDSource
from uproot3.source.http import HTTPSource

def iterate(path, treepath, branches=None, entrysteps=None, namedecode="utf-8", reportpath=False, reportfile=False, flatten=True, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, **options):
    import pandas
    return uproot3.tree.iterate(path, treepath, branches=branches, entrysteps=entrysteps, outputtype=pandas.DataFrame, namedecode=namedecode, reportpath=reportpath, reportfile=reportfile, reportentries=False, flatten=flatten, flatname=flatname, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, **options)
