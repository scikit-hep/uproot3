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

import itertools

import numpy

from uproot.interp.jagged import asjagged
from uproot.interp.numerical import asdtype
from uproot.interp.objects import asobj
from uproot.interp.objects import astable

class TTreeMethods_pandas(object):
    def __init__(self, tree):
        self._tree = tree

    def df(self, branches=None, namedecode="utf-8", entrystart=None, entrystop=None, flatten=True, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        import pandas
        return self._tree.arrays(branches=branches, outputtype=pandas.DataFrame, namedecode=namedecode, entrystart=entrystart, entrystop=entrystop, flatten=flatten, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking)

def futures2df(futures, outputtype, entrystart, entrystop, flatten):
    import pandas

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
                        columns.append(name)
                        data[name] = array
                    else:
                        for nn in interpretation.todtype.names:
                            if not nn.startswith(" "):
                                columns.append("{0}.{1}".format(name, nn))
                                data["{0}.{1}".format(name, nn)] = array[nn]
                else:
                    for tup in itertools.product(*[range(x) for x in interpretation.todims]):
                        n = "{0}[{1}]".format(name, "][".join(str(x) for x in tup))
                        if interpretation.todtype.names is None:
                            columns.append(n)
                            data[n] = array[(slice(None),) + tup]
                        else:
                            for nn in interpretation.todtype.names:
                                if not nn.startswith(" "):
                                    columns.append("{0}.{1}".format(name, nn))
                                    data["{0}.{1}".format(name, nn)] = array[nn][(slice(None),) + tup]
            else:
                columns.append(name)
                data[name] = list(array)     # must be serialized as a Python list for Pandas to accept it

        return outputtype(columns=columns, data=data)

    else:
        index = pandas.MultiIndex.from_arrays([numpy.arange(entrystart, entrystop, dtype=numpy.int64), numpy.zeros(entrystop - entrystart, dtype=numpy.int64)], names=["entry", "subentry"])
        out = outputtype(index=index)
        scalars = []

        for name, interpretation, future in futures:
            array = future()

            if isinstance(interpretation, asobj) and isinstance(interpretation.content, astable):
                interpretation = interpretation.content
            if isinstance(interpretation, astable) and isinstance(interpretation.content, asdtype):
                interpretation = interpretation.content

            if isinstance(interpretation, asjagged):
                entries = numpy.empty(len(array.content), dtype=numpy.int64)
                subentries = numpy.empty(len(array.content), dtype=numpy.int64)
                starts, stops = array.starts, array.stops
                i = 0
                numentries = entrystop - entrystart
                while i < numentries:
                    entries[starts[i]:stops[i]] = i + entrystart
                    subentries[starts[i]:stops[i]] = numpy.arange(stops[i] - starts[i])
                    i += 1

                df = outputtype(index=pandas.MultiIndex.from_arrays([entries, subentries], names=["entry", "subentry"]))

                interpretation = interpretation.content
                if isinstance(interpretation, asobj) and isinstance(interpretation.content, astable):
                    interpretation = interpretation.content
                if isinstance(interpretation, astable) and isinstance(interpretation.content, asdtype):
                    interpretation = interpretation.content

                if isinstance(interpretation, asdtype):
                    if interpretation.todims == ():
                        if interpretation.todtype.names is None:
                            df[name] = array.flatten()
                        else:
                            for nn in interpretation.todtype.names:
                                if not nn.startswith(" "):
                                    df["{0}.{1}".format(name, nn)] = array[nn].flatten()
                    else:
                        for tup in itertools.product(*[range(x) for x in interpretation.todims]):
                            if interpretation.todtype.names is None:
                                df["{0}[{1}]".format(name, "][".join(str(x) for x in tup))] = array[(slice(None),) + tup].flatten()
                            else:
                                for nn in interpretation.todtype.names:
                                    if not nn.startswith(" "):
                                        df["{0}[{1}].{2}".format(name, "][".join(str(x) for x in tup), nn)] = array[nn][(slice(None),) + tup].flatten()

                else:
                    df[name] = list(array.flatten())

            elif isinstance(interpretation, asdtype):
                df = outputtype(index=index)
                if interpretation.todims == ():
                    if interpretation.todtype.names is None:
                        df[name] = array
                        scalars.append(name)
                    else:
                        for nn in interpretation.todtype.names:
                            if not nn.startswith(" "):
                                df["{0}.{1}".format(name, nn)] = array[nn]
                                scalars.append("{0}.{1}".format(name, nn))
                else:
                    for tup in itertools.product(*[range(x) for x in interpretation.todims]):
                        if interpretation.todtype.names is None:
                            df["{0}[{1}]".format(name, "][".join(str(x) for x in tup))] = array[(slice(None),) + tup]
                            scalars.append("{0}[{1}]".format(name, "][".join(str(x) for x in tup)))
                        else:
                            for nn in interpretation.todtype.names:
                                if not nn.startswith(" "):
                                    df["{0}[{1}].{2}".format(name, "][".join(str(x) for x in tup), nn)] = array[nn][(slice(None),) + tup]
                                    scalars.append("{0}[{1}].{2}".format(name, "][".join(str(x) for x in tup), nn))

            else:
                df = outputtype(index=index, columns=[name], data={name: list(array)})
                scalars.append(name)

            out = pandas.merge(out, df, how="outer", left_index=True, right_index=True)

        for name in scalars:
            out[name].fillna(method="ffill", inplace=True)
        return out
