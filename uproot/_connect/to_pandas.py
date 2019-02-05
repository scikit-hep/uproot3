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

import itertools

import numpy

from uproot.interp.jagged import asjagged
from uproot.interp.numerical import asdtype
from uproot.interp.objects import asobj
from uproot.interp.objects import astable

class TTreeMethods_pandas(object):
    def __init__(self, tree):
        self._tree = tree

    def df(self, branches=None, namedecode="utf-8", entrystart=None, entrystop=None, flatten=True, flatname=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        import pandas
        return self._tree.arrays(branches=branches, outputtype=pandas.DataFrame, namedecode=namedecode, entrystart=entrystart, entrystop=entrystop, flatten=flatten, flatname=flatname, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking)

def default_flatname(branchname, fieldname, index):
    out = branchname
    if not isinstance(branchname, str):
        out = branchname.decode("utf-8")
    if fieldname is not None:
        out += "." + fieldname
    if index != ():
        out += "[" + "][".join(str(x) for x in index) + "]"
    return out

def futures2df(futures, outputtype, entrystart, entrystop, flatten, flatname):
    import awkward
    import pandas

    if flatname is None:
        flatname = default_flatname

    if not flatten or all(interpretation.__class__ is not asjagged for name, interpretation, future in futures):
        columns = []
        data = {}
        for name, interpretation, future in futures:
            array = future()

            if isinstance(interpretation, asobj) and isinstance(interpretation.content, astable):
                interpretation = interpretation.content
            if isinstance(interpretation, astable) and isinstance(interpretation.content, asdtype):
                interpretation = interpretation.content

            if isinstance(interpretation, asdtype):
                if interpretation.todims == ():
                    if interpretation.todtype.names is None:
                        fn = flatname(name, None, ())
                        columns.append(fn)
                        data[fn] = array
                    else:
                        for nn in interpretation.todtype.names:
                            if not nn.startswith(" "):
                                fn = flatname(name, nn, ())
                                columns.append(fn)
                                data[fn] = array[nn]
                else:
                    for tup in itertools.product(*[range(x) for x in interpretation.todims]):
                        if interpretation.todtype.names is None:
                            fn = flatname(name, None, tup)
                            columns.append(fn)
                            data[fn] = array[(slice(None),) + tup]
                        else:
                            for nn in interpretation.todtype.names:
                                if not nn.startswith(" "):
                                    fn = flatname(name, nn, tup)
                                    columns.append(fn)
                                    data[fn] = array[nn][(slice(None),) + tup]
            else:
                fn = flatname(name, None, ())
                columns.append(fn)
                data[fn] = list(array)     # must be serialized as a Python list for Pandas to accept it

        return outputtype(columns=columns, data=data)

    else:
        scalars = []

        length = None
        starts, stops = None, None

        unpacked_tuple = []

        for future_tuple in futures:
            name, interpretation, future = future_tuple

            if isinstance(interpretation, asobj) and isinstance(interpretation.content, astable):
                interpretation = interpretation.content
            if isinstance(interpretation, astable) and isinstance(interpretation.content, asdtype):
                interpretation = interpretation.content

            if isinstance(interpretation, asjagged):
                array = future()
                if starts is None:
                    starts = array.starts
                    stops = array.stops
                array = array.flatten()

                if length is None:
                    length = len(array)

            else:
                array = future()

            unpacked_tuple.append((name, interpretation, array))

        index = pandas.Index(numpy.arange(length))
        out = outputtype(index=index)

        def align_by_broadcast(array):
            # Invoke jagged broadcasting to align arrays
            content = awkward.numpy.zeros(stops.max(), dtype=array.dtype)
            return (awkward.JaggedArray(starts, stops, content) + array).flatten()


        names, interpretations, arrays = zip(*unpacked_tuple)

        for name, interpretation, array in zip(names, interpretations, arrays):

            if isinstance(interpretation, asjagged):

                df = outputtype(index=index)

                interpretation = interpretation.content
                if isinstance(interpretation, asobj) and isinstance(interpretation.content, astable):
                    interpretation = interpretation.content
                if isinstance(interpretation, astable) and isinstance(interpretation.content, asdtype):
                    interpretation = interpretation.content

                if isinstance(interpretation, asdtype):
                    if interpretation.todims == ():
                        if interpretation.todtype.names is None:
                            fn = flatname(name, None, ())
                            df[fn] = array
                        else:
                            for nn in interpretation.todtype.names:
                                if not nn.startswith(" "):
                                    fn = flatname(name, nn, ())
                                    df[fn] = array[nn]
                    else:
                        for tup in itertools.product(*[range(x) for x in interpretation.todims]):
                            if interpretation.todtype.names is None:
                                fn = flatname(name, None, tup)
                                df[fn] = array[(slice(None),) + tup]
                            else:
                                for nn in interpretation.todtype.names:
                                    if not nn.startswith(" "):
                                        fn = flatname(name, nn, tup)
                                        df[fn] = array[nn][(slice(None),) + tup]

                else:
                    fn = flatname(name, None, ())
                    df[fn] = list(array)

            elif isinstance(interpretation, asdtype):
                df = outputtype(index=index)
                if interpretation.todims == ():
                    if interpretation.todtype.names is None:
                        fn = flatname(name, None, ())
                        df[fn] = align_by_broadcast(array)
                        scalars.append(fn)
                    else:
                        for nn in interpretation.todtype.names:
                            if not nn.startswith(" "):
                                fn = flatname(name, nn, ())
                                df[fn] = align_by_broadcast(array[nn])
                                scalars.append(fn)
                else:
                    for tup in itertools.product(*[range(x) for x in interpretation.todims]):
                        if interpretation.todtype.names is None:
                            fn = flatname(name, None, tup)
                            df[fn] = align_by_broadcast(array[(slice(None),) + tup])
                            scalars.append(fn)
                        else:
                            for nn in interpretation.todtype.names:
                                if not nn.startswith(" "):
                                    fn = flatname(name, nn, tup)
                                    df[fn] = align_by_broadcast(array[nn][(slice(None),) + tup])
                                    scalars.append(fn)

            else:
                fn = flatname(name, None, ())
                df = outputtype(index=index, columns=[fn], data={fn: list(array)})
                scalars.append(fn)

            out = pandas.merge(out, df, how="outer", left_index=True, right_index=True)

        for n in scalars:
            out[n].fillna(method="ffill", inplace=True)
        return out
