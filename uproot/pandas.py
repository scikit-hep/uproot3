#!/usr/bin/env python

# Copyright (c) 2019, IRIS-HEP
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

"""Top-level functions for Pandas."""

import uproot.tree
from uproot.source.memmap import MemmapSource
from uproot.source.xrootd import XRootDSource
from uproot.source.http import HTTPSource

def iterate(path, treepath, branches=None, entrysteps=None, namedecode="utf-8", reportpath=False, reportfile=False, flatten=True, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, **options):
    import pandas
    return uproot.tree.iterate(path, treepath, branches=branches, entrysteps=entrysteps, outputtype=pandas.DataFrame, namedecode=namedecode, reportpath=reportpath, reportfile=reportfile, reportentries=False, flatten=flatten, flatname=flatname, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, **options)
