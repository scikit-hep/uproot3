#!/usr/bin/env python

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

import numpy

from uproot.interp import asdtype
from uproot.interp import asjagged
from uproot.interp import asstrings

class TTreeMethods_pandas(object):
    def __init__(self, tree):
        self._tree = tree

    def df(self, branches=None, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None, executor=None):
        import pandas

        branches = list(self._tree._normalize_branches(branches))
        entrystart, entrystop = self._tree._normalize_entrystartstop(entrystart, entrystop)

        # verify that the types are allowed and create stubs for the numerical types
        initialcolumns = {}
        for branch, interpretation in branches:
            if isinstance(interpretation, asdtype):
                initialcolumns[branch.name] = interpretation.todtype.type(0)
            elif isinstance(interpretation, asjagged):
                pass
            elif isinstance(interpretation, asstrings):
                pass
            else:
                raise TypeError("cannot convert interpretation {0} to DataFrame".format(interpretation))

        # when Pandas creates a DataFrame with numerical stubs, it allocates memory the way it wants to
        out = pandas.DataFrame(initialcolumns, index=numpy.arange(entrystart, entrystop))

        # in the common case of converting the whole tree, you can safely fill Pandas's internal arrays in-place
        if entrystart == 0 and entrystop == self._tree.numentries:
            newbranches = {}
            for branch, interpretation in branches:
                if isinstance(interpretation, asdtype):
                    newbranches[branch.name] = interpretation.toarray(out[branch.name].values)
                else:
                    newbranches[branch.name] = interpretation

        # actually read all the data, possibly in parallel
        arrays = self._tree.arrays(newbranches, entrystart=entrystart, entrystop=entrystop, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor)

        # numerical data are already in the DataFrame, but the others have to be merged in
        for branch, interpretation in branches:
            if isinstance(interpretation, asdtype):
                out[branch.name] = arrays[branch.name]
            elif isinstance(interpretation, asjagged):
                out[branch.name] = list(arrays[branch.name])
            elif isinstance(interpretation, asstrings):
                out[branch.name] = list(arrays[branch.name])
            else:
                raise AssertionError

        return out
