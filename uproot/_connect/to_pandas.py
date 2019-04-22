#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import itertools
import functools
import operator

import numpy

import awkward as awkwardbase

import uproot.tree
import uproot.interp.numerical
from uproot.interp.jagged import asjagged
from uproot.interp.numerical import asdtype
from uproot.interp.objects import asobj
from uproot.interp.objects import astable

from uproot.source.memmap import MemmapSource
from uproot.source.xrootd import XRootDSource
from uproot.source.http import HTTPSource

class TTreeMethods_pandas(object):
    def __init__(self, tree):
        self._tree = tree

    def df(self, branches=None, namedecode="utf-8", entrystart=None, entrystop=None, flatten=True, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        import pandas
        return self._tree.arrays(branches=branches, outputtype=pandas.DataFrame, namedecode=namedecode, entrystart=entrystart, entrystop=entrystop, flatten=flatten, flatname=flatname, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking)

    def iterate(self, branches=None, entrysteps=None, namedecode="utf-8", entrystart=None, entrystop=None, flatten=True, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        import pandas
        return self._tree.iterate(branches=branches, entrysteps=entrysteps, outputtype=pandas.DataFrame, namedecode=namedecode, reportentries=False, entrystart=entrystart, entrystop=entrystop, flatten=flatten, flatname=flatname, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking)

def default_flatname(branchname, fieldname, index):
    out = branchname
    if not isinstance(branchname, str):
        out = branchname.decode("utf-8")
    if fieldname is not None:
        out += "." + fieldname
    if index != ():
        out += "[" + "][".join(str(x) for x in index) + "]"
    return out

def futures2df(futures, outputtype, entrystart, entrystop, flatten, flatname, awkward):
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

        index = pandas.RangeIndex(entrystart, entrystop, name="entry")
        return outputtype(columns=columns, data=data, index=index)

    else:
        starts, stops = None, None

        needbroadcasts = []
        names = []
        interpretations = []
        arrays = []
        for name, interpretation, future in futures:
            if isinstance(interpretation, asobj) and isinstance(interpretation.content, astable):
                interpretation = interpretation.content
            if isinstance(interpretation, astable) and isinstance(interpretation.content, asdtype):
                interpretation = interpretation.content

            array = future()
            if isinstance(interpretation, asjagged):
                interpretation = interpretation.content
                if isinstance(interpretation, asobj) and isinstance(interpretation.content, astable):
                    interpretation = interpretation.content
                if isinstance(interpretation, astable) and isinstance(interpretation.content, asdtype):
                    interpretation = interpretation.content

                # justifies the assumption that array.content == array.flatten() and array.stops.max() == array.stops[-1]
                assert len(array.starts) == 0 or ((array.offsetsaliased(array.starts, array.stops) or (len(array.starts.shape) == 1 and array.numpy.array_equal(array.starts[1:], array.stops[:-1]))) and array.starts[0] == 0)

                if starts is None:
                    starts = array.starts
                    stops = array.stops
                    index = array.index
                else:
                    if starts is not array.starts and not awkward.numpy.array_equal(starts, array.starts):
                        raise ValueError("cannot use flatten=True on branches with different jagged structure, such as electrons and muons (different, variable number of each per event); either explicitly select compatible branches, such as [\"MET_*\", \"Muon_*\"] (scalar and variable per event is okay), or set flatten=False")

                if len(array.starts) == 0:
                    array = array.content[0:0]
                else:
                    array = array.content
                needbroadcasts.append(False)

            else:
                needbroadcasts.append(True)

            names.append(name)
            interpretations.append(interpretation)
            arrays.append(array)

        index = pandas.MultiIndex.from_arrays([index.tojagged(numpy.arange(entrystart, entrystop, dtype=numpy.int64)).content, index.content], names=["entry", "subentry"])

        df = outputtype(index=index)

        for name, interpretation, array, needbroadcast in zip(names, interpretations, arrays, needbroadcasts):
            if isinstance(interpretation, uproot.interp.numerical._asnumeric):
                if isinstance(array, awkwardbase.ObjectArray):
                    array = array.content

                if needbroadcast:
                    # Invoke jagged broadcasting to align arrays
                    originaldtype = array.dtype
                    originaldims = array.shape[1:]

                    if isinstance(array, awkwardbase.Table):
                        for nn in array.columns:
                            array[nn] = awkward.JaggedArray(starts, stops, awkward.numpy.empty(stops[-1], dtype=array[nn].dtype)).tojagged(array[nn]).content

                    else:
                        if len(originaldims) != 0:
                            array = array.view(awkward.numpy.dtype([(str(i), array.dtype) for i in range(functools.reduce(operator.mul, array.shape[1:]))])).reshape(array.shape[0])

                        array = awkward.JaggedArray(starts, stops, awkward.numpy.empty(stops[-1], dtype=array.dtype)).tojagged(array).content
                        if len(originaldims) != 0:
                            array = array.view(originaldtype).reshape((-1,) + originaldims)

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

                array = awkward.numpy.array(array, dtype=object)
                indexes = numpy.arange(len(array))

                indexes = awkward.JaggedArray(starts, stops, awkward.numpy.empty(stops[-1], dtype=object)).tojagged(indexes).content

                array = array[indexes]

                if len(array) != 0 and isinstance(array[0], awkward.numpy.ndarray):
                    df[fn] = list(array)
                else:
                    df[fn] = array

        return df
