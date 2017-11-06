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

import glob
import numbers
import os.path
import re
import struct
import sys
import threading
from collections import namedtuple
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
try:
    from collections import OrderedDict
except ImportError:
    class OrderedDict(dict):
        def __init__(self, items=(), **kwds):
            items = list(items)
            self._order = [k for k, v in items] + [k for k, v in kwds.items()]
            super(OrderedDict, self).__init__(items)
        def keys(self):
            return self._order
        def values(self):
            return [self[k] for k in self._order]
        def items(self):
            return [(k, self[k]) for k in self._order]
        def __setitem__(self, name, order):
            if name not in self._order:
                self._order.append(name)
            super(OrderedDict, self).__setitem__(name, value)
        def __delitem__(self, name):
            if name in self._order:
                self._order.remove(name)
            super(OrderedDict, self).__delitem__(name)
        def __repr__(self):
            return "OrderedDict([{0}])".format(", ".join("({0}, {1})".format(repr(k), repr(v)) for k, v in self.items()))

import numpy

import uproot.rootio
from uproot.rootio import _bytesid
from uproot.source.cursor import Cursor

def _delayedraise(excinfo):
    if excinfo is not None:
        cls, err, trc = excinfo
        if sys.version_info[0] <= 2:
            exec("raise cls, err, trc")
        else:
            raise err.with_traceback(trc)

if sys.version_info[0] <= 2:
    string_types = (unicode, str)
else:
    string_types = (str, bytes)

################################################################ high-level interface

def iterate(path, treepath, entrystepsize, branches=None, outputtype=dict, reportentries=False, rawcache=None, cache=None, executor=None, memmap=True, chunkbytes=8*1024, limitbytes=1024**2):
    def explode(x):
        parsed = urlparse(x)
        if _bytesid(parsed.scheme) == b"file" or len(parsed.scheme) == 0:
            return sorted(glob.glob(os.path.expanduser(parsed.netloc + parsed.path)))
        else:
            return [x]

    if isinstance(path, string_types):
        paths = explode(path)
    else:
        paths = [y for x in path for y in explode(x)]

    if not isinstance(entrystepsize, numbers.Integral) or entrystepsize <= 0:
        raise ValueError("'entrystepsize' must be a positive integer")

    oldpath = None
    oldbranches = None
    holdover = None
    holdoverentries = 0
    outerstart = 0
    for path in paths:
        tree = uproot.rootio.open(path, memmap=memmap, chunkbytes=chunkbytes, limitbytes=limitbytes)[treepath]
        listbranches = list(tree._normalize_branches(branches))

        newbranches = OrderedDict((branch.name, interpretation) for branch, interpretation in listbranches)
        if oldbranches is not None:
            for key in set(oldbranches.keys()).union(set(newbranches.keys())):
                if key not in newbranches:
                    raise ValueError("branch {0} cannot be found in {1}, but it was in {2}".format(repr(key), repr(path), repr(oldpath)))
                if key not in oldbranches:
                    del newbranches[key]
                elif not _compatible_interpretation(newbranches[key], oldbranches[key]):
                    raise ValueError("branch {0} interpreted as {1} in {2}, but as {3} in {4}".format(repr(key), newbranches[key], repr(path), oldbranches[key], repr(oldpath)))

        oldpath = path
        oldbranches = newbranches

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in listbranches])

        def output(arrays, outerstart, outerstop):
            if issubclass(outputtype, dict):
                out = outputtype(arrays.items())
            elif outputtype == tuple or outputtype == list:
                out = outputtype(arrays.values())
            else:
                out = outputtype(*arrays.values())
            if reportentries:
                return outerstart, outerstop, out
            else:
                return out

        def startstop():
            start = 0
            while start < tree.numentries:
                if start == 0 and holdoverentries != 0:
                    stop = start + (entrystepsize - holdoverentries)
                else:
                    stop = start + entrystepsize
                yield start, stop
                start = stop

        for innerstart, innerstop, arrays in tree._iterate(startstop(), newbranches, OrderedDict, True, rawcache, cache, executor):
            numentries = innerstop - innerstart

            if holdover is not None:
                arrays = OrderedDict((name, numpy.concatenate((oldarray, arrays[name]))) for name, oldarray in holdover.items())
                numentries += holdoverentries
                holdover = None
                holdoverentries = 0

            if numentries < entrystepsize:
                holdover = arrays
                holdoverentries = numentries
            else:
                yield output(arrays, outerstart, outerstart + numentries)
                outerstart += numentries

    if holdover is not None:
        yield output(arrays, outerstart, outerstart + numentries)

################################################################ interpretation tools

def interpret(branch, classes=None, swapbytes=True):
    if classes is None:
        classes = branch._context.classes

    class NotNumpy(Exception): pass

    def leaf2dtype(leaf):
        classname = leaf.__class__.__name__
        if classname == "TLeafO":
            return numpy.dtype(numpy.bool)
        elif classname == "TLeafB":
            if leaf.fIsUnsigned:
                return numpy.dtype(numpy.uint8)
            else:
                return numpy.dtype(numpy.int8)
        elif classname == "TLeafS":
            if leaf.fIsUnsigned:
                return numpy.dtype(numpy.uint16)
            else:
                return numpy.dtype(numpy.int16)
        elif classname == "TLeafI":
            if leaf.fIsUnsigned:
                return numpy.dtype(numpy.uint32)
            else:
                return numpy.dtype(numpy.int32)
        elif classname == "TLeafL":
            if leaf.fIsUnsigned:
                return numpy.dtype(numpy.uint64)
            else:
                return numpy.dtype(numpy.int64)
        elif classname == "TLeafF":
            return numpy.dtype(numpy.float32)
        elif classname == "TLeafD":
            return numpy.dtype(numpy.float64)
        else:
            raise NotNumpy

    dims = ()
    if len(branch.fLeaves) == 1:
        m = interpret._titlehasdims.match(branch.fLeaves[0].fTitle)
        if m is not None:
            dims = tuple(int(x) for x in re.findall(interpret._itemdimpattern, branch.fLeaves[0].fTitle))
    else:
        for leaf in branch.fLeaves:
            if interpret._titlehasdims.match(leaf.fTitle):
                return None

    try:
        if len(branch.fLeaves) == 1:
            fromdtype = leaf2dtype(branch.fLeaves[0]).newbyteorder(">")
            if swapbytes:
                return asdtype(fromdtype, fromdtype.newbyteorder("="), dims, dims)
            else:
                return asdtype(fromdtype, fromdtype, dims, dims)
        else:
            fromdtype = numpy.dtype([(leaf.fName, leaf2dtype(leaf).newbyteorder(">")) for leaf in branch.fLeaves])
            if swapbytes:
                todtype = numpy.dtype([(leaf.fName, leaf2dtype(leaf).newbyteorder("=")) for leaf in branch.fLeaves])
            else:
                todtype = fromdtype
            return asdtype(fromdtype, todtype, dims, dims)

    except NotNumpy:
        if len(branch.fLeaves) == 1:
            if branch.fLeaves[0].__class__.__name__ == "TLeafC":
                return uproot.rootio.TString

            elif branch.fLeaves[0].__class__.__name__ == "TLeafElement":
                classname = None
                if classname in classes:
                    cls = classes[classname]
                    # the 'interpretation' interface
                    if hasattr(cls, "nocopy") and hasattr(cls, "numitems") and hasattr(cls, "frombytes") and hasattr(cls, "destarray") and hasattr(cls, "filldest"):
                        return classes[classname]

        return None

interpret._titlehasdims = re.compile(br"^([^\[\]]+)(\[[^\[\]]+\])+")
interpret._itemdimpattern = re.compile(br"\[([1-9][0-9]*)\]")

def _dimsprod(dims):
    out = 1
    for x in dims:
        out *= x
    return out

def _compatible_interpretation(one, two):
    if isinstance(one, (asdtype, asarray)) and isinstance(two, (asdtype, asarray)):
        return one.todtype == two.todtype and one.todims == two.todims
    elif isinstance(one, uproot.rootio.ROOTStreamedObject) and isinstance(two, uproot.rootio.ROOTStreamedObject):
        return one.__name__ == two.__name__
    else:
        return False

class asdtype(object):
    def __init__(self, fromdtype, todtype=None, fromdims=(), todims=None):
        if isinstance(fromdtype, numpy.dtype):
            self.fromdtype = fromdtype
        elif isinstance(fromdtype, string_types) and len(fromdtype) > 0 and fromdtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.fromdtype = numpy.dtype(fromdtype)
        else:
            self.fromdtype = numpy.dtype(fromdtype).newbyteorder(">")

        if todtype is None:
            self.todtype = self.fromdtype.newbyteorder("=")
        elif isinstance(todtype, numpy.dtype):
            self.todtype = todtype
        elif isinstance(todtype, string_types) and len(todtype) > 0 and todtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.todtype = numpy.dtype(todtype)
        else:
            self.todtype = numpy.dtype(todtype).newbyteorder("=")

        self.fromdims = fromdims

        if todims is None:
            self.todims = self.fromdims
        else:
            self.todims = todims

    def to(self, todtype, todims=None):
        return asdtype(self.fromdtype, todtype, self.fromdims, todims)

    def toarray(self, array):
        return asarray(self.fromdtype, array, self.fromdims)

    def __repr__(self):
        args = []

        if self.fromdtype.byteorder == ">":
            args.append(repr(str(self.fromdtype)))
        else:
            args.append(repr(self.fromdtype))

        if self.todtype.newbyteorder(">") != self.fromdtype.newbyteorder(">"):
            if self.todtype.byteorder == "=":
                args.append(repr(str(self.todtype)))
            else:
                args.append(repr(self.todtype))

        if self.fromdims != ():
            args.append(repr(self.fromdims))

        if self.todims != self.fromdims:
            args.append(repr(self.todims))

        return "asdtype(" + ", ".join(args) + ")"

    def nocopy(self):
        return asdtype(self.fromdtype, self.fromdtype, self.fromdims, self.fromdims)

    def numitems(self, numbytes, numentries, flattened):
        out = numbytes // self.fromdtype.itemsize
        if flattened:
            return out
        else:
            return out // _dimsprod(self.todims)

    def frombytes(self, data, offsets, entrystart, entrystop):
        array = data.view(self.fromdtype)

        if self.fromdims != ():
            product = _dimsprod(self.fromdims)
            assert len(array) % product == 0, "{0} % {1} == {2} != 0".format(len(array), product, len(array) % product)
            array = array.reshape((len(array) // product,) + self.fromdims)

        return array[entrystart:entrystop]

    def destarray(self, numitems, sourcearray):
        if sourcearray is not None and self.todtype == sourcearray.dtype and numitems * _dimsprod(self.todims) <= _dimsprod(sourcearray.shape):
            if len(sourcearray.shape) > 1:
                sourcearray_flattened = sourcearray.reshape(_dimsprod(sourcearray.shape))
            else:
                sourcearray_flattened = sourcearray
            array = sourcearray_flattened[:numitems * _dimsprod(self.todims)]
            if self.todims != ():
                return array.reshape((numitems,) + self.todims)
            else:
                return array

        else:
            return numpy.empty((numitems,) + self.todims, dtype=self.todtype)

    def filldest(self, sourcearray, destarray, itemstart, itemstop):
        reusable = itemstart == 0 and itemstop == len(destarray)

        if reusable:
            frombase = sourcearray
            while hasattr(frombase, "base") and frombase.base is not None:
                frombase = frombase.base
            tobase = destarray
            while hasattr(tobase, "base") and tobase.base is not None:
                tobase = tobase.base
            if frombase is not tobase:
                reusable = False

        if reusable:
            return destarray

        else:
            if self.fromdims != ():
                flattened_sourcearray = sourcearray.reshape(_dimsprod(self.fromdims) * len(sourcearray))
            else:
                flattened_sourcearray = sourcearray

            if self.todims != ():
                product = _dimsprod(self.todims)
                flattened_destarray = destarray.reshape(len(destarray) * product)
                flattened_itemstart = itemstart * product
                flattened_itemstop = itemstop * product
            else:
                flattened_destarray = destarray
                flattened_itemstart = itemstart
                flattened_itemstop = itemstop

            flattened_destarray[flattened_itemstart:flattened_itemstop] = flattened_sourcearray
            return destarray[itemstart:itemstop]

class asarray(object):
    def __init__(self, fromdtype, toarray, fromdims=()):
        if isinstance(fromdtype, numpy.dtype):
            self.fromdtype = fromdtype
        else:
            self.fromdtype = numpy.dtype(fromdtype).newbyteorder(">")
        self.toarray = toarray
        self.fromdims = fromdims

    @property
    def todtype(self):
        return self.toarray.dtype

    @property
    def todims(self):
        return self.toarray.shape[1:]

    def __repr__(self):
        args = []

        if self.fromdtype.byteorder == ">":
            args.append(repr(str(self.fromdtype)))
        else:
            args.append(repr(self.fromdtype))

        if self.todtype.byteorder == "=":
            args.append("<array dtype={0} at 0x{1:012x}>".format(repr(str(self.todtype)), id(self.todtype)))
        else:
            args.append("<array dtype={0} at 0x{1:012x}>".format(repr(self.todtype), id(self.todtype)))

        return "asarray(" + ", ".join(args) + ")"

    def nocopy(self):
        return asdtype(self.fromdtype, self.fromdtype, self.fromdims, self.fromdims)

    def numitems(self, numbytes, numentries, flattened):
        out = numbytes // self.fromdtype.itemsize
        if flattened:
            return out
        else:
            return out // _dimsprod(self.toarray.shape[1:])

    def frombytes(self, data, offsets, entrystart, entrystop):
        array = data.view(self.fromdtype)

        if self.fromdims != ():
            product = _dimsprod(self.fromdims)
            assert len(array) % product == 0, "{0} % {1} == {2} != 0".format(len(array), product, len(array) % product)
            array = array.reshape((len(array) // product,) + self.fromdims)

        return array[entrystart:entrystop]

    def destarray(self, numitems, sourcearray):
        if numitems > len(self.toarray):
            raise ValueError("{0} items to fill, but provided an array with only {1} items".format(numitems, len(self.toarray)))
        return self.toarray[:numitems]

    def filldest(self, sourcearray, destarray, itemstart, itemstop):
        if self.fromdims != ():
            flattened_sourcearray = sourcearray.reshape(_dimsprod(self.fromdims) * len(sourcearray))
        else:
            flattened_sourcearray = sourcearray

        if len(destarray.shape) > 1:
            flattened_destarray = destarray.reshape(_dimsprod(destarray.shape))
            product = len(flattened_destarray) // len(destarray)
            flattened_itemstart = itemstart * product
            flattened_itemstop = itemstop * product
        else:
            flattened_destarray = destarray
            flattened_itemstart = itemstart
            flattened_itemstop = itemstop

        flattened_destarray[flattened_itemstart:flattened_itemstop] = flattened_sourcearray
        return destarray[itemstart:itemstop]

################################################################ methods for TTree

class TTreeMethods(object):
    _copycontext = True

    def _postprocess(self, source, cursor, context):
        context.treename = self.name

    @property
    def name(self):
        return self.fName

    @property
    def title(self):
        return self.fTitle

    @property
    def numentries(self):
        return self.fEntries

    @property
    def branches(self):
        return self.fBranches

    @property
    def allbranches(self):
        out = []
        for branch in self.branches:
            out.append(branch)
            out.extend(branch.allbranches)
        return out

    @property
    def branchnames(self):
        return [branch.name for branch in self.branches]

    @property
    def allbranchnames(self):
        return [branch.name for branch in self.allbranches]

    def branch(self, name):
        name = _bytesid(name)
        for branch in self.branches:
            if branch.name == name:
                return branch
            try:
                return branch.branch(name)
            except KeyError:
                pass
        raise KeyError("not found: {0}".format(repr(name)))

    @property
    def clusters(self):
        # need to find an example of a file that has clusters!
        # yield as a (start, stop) generator
        raise NotImplementedError

    def array(self, branch, interpretation=None, entrystart=None, entrystop=None, rawcache=None, cache=None, executor=None, blocking=True):
        return self.branch(branch).array(interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, rawcache=rawcache, cache=cache, executor=executor, blocking=blocking)

    def lazyarray(self, branch, interpretation=None):
        return self.branch(branch).lazyarray(interpretation=interpretation)

    def arrays(self, branches=None, outputtype=dict, entrystart=None, entrystop=None, rawcache=None, cache=None, executor=None, blocking=True):
        branches = list(self._normalize_branches(branches))

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])

        futures = [(branch.name, branch.array(interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, rawcache=rawcache, cache=cache, executor=executor, blocking=False)) for branch, interpretation in branches]

        if issubclass(outputtype, dict):
            def await():
                return outputtype([(name, future()) for name, future in futures])
        elif outputtype == tuple or outputtype == list:
            def await():
                return outputtype([future() for name, future in futures])
        else:
            def await():
                return outputtype(*[future() for name, future in futures])

        if blocking:
            return await()
        else:
            return await
        
    def lazyarrays(self, branches=None, outputtype=dict):
        branches = list(self._normalize_branches(branches))

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])

        lazyarrays = [(branch.name, branch.lazyarray(interpretation=interpretation)) for branch, interpretation in branches]

        if issubclass(outputtype, dict):
            return outputtype(lazyarrays)
        elif outputtype == tuple or outputtype == list:
            return outputtype([lazyarray for name, lazyarray in lazyarrays])
        else:
            return outputtype(*[lazyarray for name, lazyarray in lazyarrays])

    def _iterate(self, startstop, branches, outputtype, reportentries, rawcache, cache, executor):
        branches = list(self._normalize_branches(branches))

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])

        branchinfo = [(branch, interpretation, {}, branch._basket_itemoffset(interpretation, 0, branch.numbaskets)) for branch, interpretation in branches]

        if rawcache is None:
            rawcache = uproot.cache.memorycache.ThreadSafeDict()
            explicit_rawcache = False
        else:
            explicit_rawcache = True

        for start, stop in startstop:
            futures = [(branch.name, branch._step_array(interpretation, baskets, basket_itemoffset, start, stop, rawcache, cache, executor, explicit_rawcache)) for branch, interpretation, baskets, basket_itemoffset in branchinfo]

            if issubclass(outputtype, dict):
                out = outputtype([(name, future()) for name, future in futures])
            elif outputtype == tuple or outputtype == list:
                out = outputtype([future() for name, future in futures])
            else:
                out = outputtype(*[future() for name, future in futures])

            if reportentries:
                yield max(0, start), min(stop, self.numentries), out
            else:
                yield out

    def iterate(self, entrystepsize, branches=None, outputtype=dict, reportentries=False, entrystart=None, entrystop=None, rawcache=None, cache=None, executor=None):
        if not isinstance(entrystepsize, numbers.Integral) or entrystepsize <= 0:
            raise ValueError("'entrystepsize' must be a positive integer")

        if entrystart is None:
            entrystart = 0
        if entrystop is None:
            entrystop = self.numentries

        def startstop():
            start = entrystart
            stop = start + entrystepsize
            while start < entrystop and start < self.numentries:
                yield start, stop
                start = stop
                stop = start + entrystepsize

        return self._iterate(startstop(), branches, outputtype, reportentries, rawcache, cache, executor)

    def iterate_clusters(self, branches=None, outputtype=dict, reportentries=False, entrystart=None, entrystop=None, executor=None):
        return self._iterate(self.clusters, branches, outputtype, reportentries, rawcache, cache, executor)

    def _normalize_branches(self, arg):
        if arg is None:                                    # no specification; read all branches
            for branch in self.allbranches:                # that have interpretations
                interpretation = interpret(branch)
                if interpretation is not None:
                    yield branch, interpretation

        elif callable(arg):
            for branch in self.allbranches:
                result = arg(branch)
                if result is None:
                    pass
                elif result is True:                       # function is a filter
                    interpretation = interpret(branch)
                    if interpretation is not None:
                        yield branch, interpretation
                else:                                      # function is giving interpretations
                    yield branch, result

        elif isinstance(arg, dict):
            for name, interpretation in arg.items():       # dict of branch-interpretation pairs
                name = _bytesid(name)
                branch = self.branch(name)
                interpretation = interpret(branch)         # but no interpretation given
                if interpretation is None:
                    raise ValueError("cannot interpret branch {0} as a Python type".format(repr(name)))
                else:
                    yield branch, interpretation

        elif isinstance(arg, string_types):
            name = _bytesid(arg)                           # one explicitly given branch name
            branch = self.branch(name)
            interpretation = interpret(branch)             # but no interpretation given
            if interpretation is None:
                raise ValueError("cannot interpret branch {0} as a Python type".format(repr(name)))
            else:
                yield branch, interpretation

        else:
            try:
                names = iter(arg)                          # only way to check for iterable (in general)
            except:
                raise TypeError("'branches' argument not understood")
            else:
                for name in names:
                    name = _bytesid(name)
                    branch = self.branch(name)
                    interpretation = interpret(branch)     # but no interpretation given
                    if interpretation is None:
                        raise ValueError("cannot interpret branch {0} as a Python type".format(repr(name)))
                    else:
                        yield branch, interpretation

    def __len__(self):
        return self.numentries

    def __getitem__(self, name):
        return self.branch(name)

    def __iter__(self):
        # prevent Python's attempt to interpret __len__ and __getitem__ as iteration
        raise TypeError("'TTree' object is not iterable")

    class _Connector(object): pass

    @property
    def pandas(self):
        import uproot._connect.to_pandas
        connector = self._Connector()
        connector.df = uproot._connect.to_pandas.df
        return connector

    @property
    def oamap(self):
        import uproot._connect.to_oamap
        connector = self._Connector()
        connector.schema  = uproot._connect.to_oamap.schema
        connector.proxy   = uproot._connect.to_oamap.proxy
        connector.run     = uproot._connect.to_oamap.run
        connector.compile = uproot._connect.to_oamap.compile
        return connector

uproot.rootio.methods["TTree"] = TTreeMethods

################################################################ methods for TBranch

class TBranchMethods(object):
    def _postprocess(self, source, cursor, context):
        self.fBasketBytes = self.fBasketBytes
        self.fBasketEntry = self.fBasketEntry
        self.fBasketSeek = self.fBasketSeek
        self._source = source
        self._context = context

    @property
    def name(self):
        return self.fName

    @property
    def title(self):
        return self.fTitle

    @property
    def numentries(self):
        return self.fEntryNumber

    @property
    def branches(self):
        return self.fBranches

    @property
    def allbranches(self):
        out = []
        for branch in self.branches:
            out.append(branch)
            out.extend(branch.allbranches)
        return out

    @property
    def branchnames(self):
        return [branch.name for branch in self.branches]

    @property
    def allbranchnames(self):
        return [branch.name for branch in self.allbranches]

    @property
    def numbaskets(self):
        return self.fWriteBasket

    @property
    def uncompressedbytes(self):
        keysource = self._source.threadlocal()
        try:
            out = 0
            for i in range(self.numbaskets):
                key = self._basketkey(keysource, i, False)
                out += key.fObjlen
            return out
        finally:
            keysource.dismiss()

    @property
    def compressedbytes(self):
        keysource = self._source.threadlocal()
        try:
            out = 0
            for i in range(self.numbaskets):
                key = self._basketkey(keysource, i, False)
                out += key.fNbytes - key.fKeylen
            return out
        finally:
            keysource.dismiss()

    @property
    def compressionratio(self):
        keysource = self._source.threadlocal()
        try:
            numer, denom = 0, 0
            for i in range(self.numbaskets):
                key = self._basketkey(keysource, i, False)
                numer += key.fObjlen
                denom += key.fNbytes - key.fKeylen
            return float(numer) / float(denom)
        finally:
            keysource.dismiss()

    def _normalize_interpretation(self, interpretation):
        if interpretation is None:
            interpretation = interpret(self)
        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type".format(repr(self.name)))
        return interpretation

    def numitems(self, interpretation=None, flattened=False):
        interpretation = self._normalize_interpretation(interpretation)
        keysource = self._source.threadlocal()
        try:
            out = 0
            for i in range(self.numbaskets):
                key = self._basketkey(keysource, i, True)
                out += interpretation.numitems(key.border, self.basket_numentries(i), flattened)
            return out
        finally:
            keysource.dismiss()

    @property
    def compression(self):
        return uproot.source.compressed.Compression(self.fCompress)

    def basket_entrystart(self, i):
        if not 0 <= i < self.numbaskets:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))
            return self.fBasketEntry[i]
        else:
            return self.fBasketEntry[i]

    def basket_entrystop(self, i):
        if not 0 <= i < self.numbaskets:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))
        if i + 1 < len(self.fBasketEntry):
            return self.fBasketEntry[i + 1]
        else:
            return self.fEntryNumber

    def basket_numentries(self, i):
        return self.basket_entrystop(i) - self.basket_entrystart(i)

    def basket_uncompressedbytes(self, i):
        keysource = self._source.threadlocal()
        try:
            key = self._basketkey(keysource, i, False)
            return key.fObjlen
        finally:
            keysource.dismiss()

    def basket_compressedbytes(self, i):
        keysource = self._source.threadlocal()
        try:
            key = self._basketkey(keysource, i, False)
            return key.fNbytes - key.fKeylen
        finally:
            keysource.dismiss()

    def basket_numitems(self, i, interpretation=None, flattened=False):
        interpretation = self._normalize_interpretation(interpretation)
        keysource = self._source.threadlocal()
        try:
            key = self._basketkey(keysource, i, True)
            return interpretation.numitems(key.border, self.basket_numentries(i), flattened)
        finally:
            keysource.dismiss()
            
    def branch(self, name):
        name = _bytesid(name)
        for branch in self.branches:
            if branch.name == name:
                return branch
            try:
                return branch.branch(name)
            except KeyError:
                pass
        raise KeyError("not found: {0}".format(repr(name)))

    def _normalize_entrystartstop(self, entrystart, entrystop):
        if entrystart is None:
            entrystart = 0
        if entrystop is None:
            entrystop = self.numentries
        return entrystart, entrystop

    def _localentries(self, i, entrystart, entrystop):
        local_entrystart = max(0, entrystart - self.basket_entrystart(i))
        local_entrystop  = max(0, min(entrystop - self.basket_entrystart(i), self.basket_entrystop(i) - self.basket_entrystart(i)))
        return local_entrystart, local_entrystop
        
    def _cachekey(self, i, local_entrystart, local_entrystop):
        return "{0};{1};{2};{3};{4}-{5}".format(self._context.sourcepath, self._context.treename, self.name, i, local_entrystart, local_entrystop)

    def _rawcachekey(self, i):
        return "{0};{1};{2};{3};raw".format(self._context.sourcepath, self._context.treename, self.name, i)
        
    def basket(self, i, interpretation=None, entrystart=None, entrystop=None, rawcache=None, cache=None):
        if not 0 <= i < self.numbaskets:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

        interpretation = self._normalize_interpretation(interpretation)
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)

        local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)

        sourcearray = None
        if cache is not None:
            cachekey = self._cachekey(i, local_entrystart, local_entrystop)
            sourcearray = cache.get(cachekey, None)

        if sourcearray is None:
            basketdata = None
            if rawcache is not None:
                rawcachekey = self._rawcachekey(i)
                basketdata = rawcache.get(rawcachekey, None)

            keysource = self._source.threadlocal()
            try:
                key = self._basketkey(keysource, i, True)
                if basketdata is None:
                    basketdata = key.cursor.bytes(key.source, key.fObjlen)
            finally:
                keysource.dismiss()

            if rawcache is not None:
                rawcache[rawcachekey] = basketdata

            if key.fObjlen == key.border:
                data, offsets = basketdata, None
            else:
                data = basketdata[:key.border]
                offsets = numpy.empty((key.fObjlen - key.border - 4) // 4, dtype=numpy.int32)
                offsets[:-1] = basketdata[key.border + 4 : -4].view(">i4")
                offsets[-1] = key.fLast
                numpy.subtract(offsets, key.fKeylen, offsets)

            sourcearray = interpretation.frombytes(data, offsets, local_entrystart, local_entrystop)

        if cache is not None:
            cache[cachekey] = sourcearray

        numvalues = _dimsprod(sourcearray.shape)
        todimsprod = _dimsprod(interpretation.todims)
        assert numvalues % todimsprod == 0, "{0} % {1} == {2} != 0".format(numvalues, todimsprod, numvalues % todimsprod)

        destarray = interpretation.destarray(numvalues // todimsprod, sourcearray)
        return interpretation.filldest(sourcearray, destarray, 0, len(destarray))

    def _basketstartstop(self, entrystart, entrystop):
        basketstart, basketstop = None, None
        for i in range(self.numbaskets):
            if basketstart is None:
                if entrystart < self.basket_entrystop(i) and self.basket_entrystart(i) < entrystop:
                    basketstart = i
                    basketstop = i
            else:
                if self.basket_entrystart(i) < entrystop:
                    basketstop = i

        if basketstop is not None:
            basketstop += 1    # stop is exclusive

        return basketstart, basketstop

    def baskets(self, interpretation=None, entrystart=None, entrystop=None, rawcache=None, cache=None, reportentries=False, executor=None, blocking=True):
        interpretation = self._normalize_interpretation(interpretation)
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)
        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if basketstart is None:
            if blocking:
                return []
            else:
                def await():
                    return []
                return await

        out = [None] * (basketstop - basketstart)

        def fill(j):
            try:
                basket = self.basket(j + basketstart, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, rawcache=rawcache, cache=cache)
                if reportentries:
                    local_entrystart, local_entrystop = self._localentries(j + basketstart, entrystart, entrystop)
                    basket = (local_entrystart + self.basket_entrystart(j + basketstart),
                              local_entrystop + self.basket_entrystart(j + basketstart),
                              basket)
            except:
                return sys.exc_info()
            else:
                out[j] = basket
                return None

        if executor is None:
            for j in range(basketstop - basketstart):
                _delayedraise(fill(j))
            excinfos = ()
        else:
            excinfos = executor.map(fill, range(basketstop - basketstart))

        if blocking:
            for excinfo in excinfos:
                _delayedraise(excinfo)
            return out
        else:
            def await():
                for excinfo in excinfos:
                    _delayedraise(excinfo)
                return out
            return await

    def iterate_baskets(self, interpretation=None, entrystart=None, entrystop=None, rawcache=None, cache=None, reportentries=False):
        interpretation = self._normalize_interpretation(interpretation)
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)

        for i in range(self.numbaskets):
            if entrystart < self.basket_entrystop(i) and self.basket_entrystart(i) < entrystop:
                local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)

                if local_entrystop > local_entrystart:
                    if reportentries:
                        yield (local_entrystart + self.basket_entrystart(i),
                               local_entrystop + self.basket_entrystart(i),
                               self.basket(i, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, rawcache=rawcache, cache=cache))
                    else:
                        yield self.basket(i, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, rawcache=rawcache, cache=cache)

    def _basket_itemoffset(self, interpretation, basketstart, basketstop):
        basket_itemoffset = [0]
        keysource = self._source.threadlocal()
        try:
            for i in range(basketstart, basketstop):
                key = self._basketkey(keysource, i, True)
                numitems = interpretation.numitems(key.border, self.basket_numentries(i), False)
                basket_itemoffset.append(basket_itemoffset[-1] + numitems)
        finally:
            keysource.dismiss()
        return basket_itemoffset

    def array(self, interpretation=None, entrystart=None, entrystop=None, rawcache=None, cache=None, executor=None, blocking=True):
        interpretation = self._normalize_interpretation(interpretation)
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)
        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if basketstart is None:
            if blocking:
                return numpy.empty(0, dtype=interpretation.todtype)
            else:
                def await():
                    return numpy.empty(0, dtype=interpretation.todtype)
                return await

        basket_itemoffset = self._basket_itemoffset(interpretation, basketstart, basketstop)

        nocopy = interpretation.nocopy()
        destarray = interpretation.destarray(basket_itemoffset[-1], None)

        def fill(j):
            try:
                basket = self.basket(j + basketstart, interpretation=nocopy, entrystart=entrystart, entrystop=entrystop, rawcache=rawcache, cache=cache)

                expecteditems = basket_itemoffset[j + 1] - basket_itemoffset[j]

                if j + 1 == basketstop - basketstart and expecteditems > len(basket):
                    basket_itemoffset[j + 1] -= expecteditems - len(basket)

                elif j == 0 and expecteditems > len(basket):
                    basket_itemoffset[j] += expecteditems - len(basket)

                interpretation.filldest(basket, destarray, basket_itemoffset[j], basket_itemoffset[j + 1])

            except:
                return sys.exc_info()

        if executor is None:
            for j in range(basketstop - basketstart):
                _delayedraise(fill(j))
            excinfos = ()
        else:
            excinfos = executor.map(fill, range(basketstop - basketstart))

        if blocking:
            for excinfo in excinfos:
                _delayedraise(excinfo)
            return destarray[basket_itemoffset[0] : basket_itemoffset[-1]]
        else:
            def await():
                for excinfo in excinfos:
                    _delayedraise(excinfo)
                return destarray[basket_itemoffset[0] : basket_itemoffset[-1]]
            return await

    def _step_array(self, interpretation, baskets, basket_itemoffset, entrystart, entrystop, rawcache, cache, executor, explicit_rawcache):
        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if basketstart is None:
            return lambda: numpy.empty(0, dtype=interpretation.todtype)

        for key in list(baskets):
            i, _, _ = key
            if i < basketstart:
                del baskets[key]
            if not explicit_rawcache:
                try:
                    del rawcache[self._rawcachekey(i)]
                except KeyError:
                    pass

        basket_itemoffset = basket_itemoffset[basketstart : basketstop + 1]

        nocopy = interpretation.nocopy()
        destarray = interpretation.destarray(basket_itemoffset[-1], None)
        lock = threading.Lock()
        
        def fill(j):
            try:
                key = (j + basketstart, entrystart, entrystop)

                with lock:
                    basket = baskets.get(key, None)
                if basket is None:
                    basket = self.basket(j + basketstart, interpretation=nocopy, entrystart=entrystart, entrystop=entrystop, rawcache=rawcache, cache=cache)
                    with lock:
                        baskets[key] = basket

                if not explicit_rawcache:
                    local_entrystart, local_entrystop = self._localentries(j + basketstart, entrystart, entrystop)
                    if local_entrystart == 0 and local_entrystop == self.basket_numentries(j + basketstart):
                        try:
                            del rawcache[self._rawcachekey(j + basketstart)]
                        except KeyError:
                            pass

                expecteditems = basket_itemoffset[j + 1] - basket_itemoffset[j]

                if j + 1 == basketstop - basketstart and expecteditems > len(basket):
                    basket_itemoffset[j + 1] -= expecteditems - len(basket)

                elif j == 0 and expecteditems > len(basket):
                    basket_itemoffset[j] += expecteditems - len(basket)

                interpretation.filldest(basket, destarray, basket_itemoffset[j], basket_itemoffset[j + 1])

            except:
                return sys.exc_info()

        if executor is None:
            for j in range(basketstop - basketstart):
                _delayedraise(fill(j))
            excinfos = ()
        else:
            excinfos = executor.map(fill, range(basketstop - basketstart))

        def await():
            for excinfo in excinfos:
                _delayedraise(excinfo)
            return destarray[basket_itemoffset[0] : basket_itemoffset[-1]]
        return await

    def lazyarray(self, interpretation=None):
        interpretation = self._normalize_interpretation(interpretation)
        return self._LazyArray(self, interpretation)

    class _LazyArray(object):
        def __init__(self, branch, interpretation):
            self._branch = branch
            self._interpretation = interpretation
            self._basket_itemoffset = self._branch._basket_itemoffset(self._interpretation, 0, self._branch.numbaskets)
            self._baskets = [None] * self._branch.numbaskets

        @property
        def dtype(self):
            return self._interpretation.todtype

        @property
        def shape(self):
            return (len(self),) + self._interpretation.todims

        def cumsum(self, axis=None, dtype=None, out=None):
            return self._array(self._basket_itemoffset[0], self._basket_itemoffset[-1]).cumsum(axis=axis, dtype=dtype, out=out)

        def __len__(self):
            return self._basket_itemoffset[-1]

        def __getitem__(self, index):
            if isinstance(index, slice):
                start, stop, step = self._normalize_slice(index)
                array = self._array(start, stop)
                if step == 1:
                    return array
                else:
                    return array[::step]

            else:
                index = self._normalize_index(index, False, 1)
                array = self._array(index, index + 1)
                return array[0]

        def __getslice__(self, start, end):
            return self.__getitem__(slice(start, end))

        def _array(self, itemstart=None, itemstop=None):
            if itemstart is None:
                itemstart = 0
            if itemstop is None:
                itemstop = self._branch.numitems(self._interpretation)

            basketstart, basketstop = None, None
            numitems = 0
            for i in range(self._branch.numbaskets):
                if basketstart is None:
                    if itemstart < self._basket_itemoffset[i + 1] and self._basket_itemoffset[i] < itemstop:
                        basketstart = i

                if basketstart is not None and self._basket_itemoffset[i] < itemstop:
                    basketstop = i
                    numitems += (self._basket_itemoffset[i + 1] - self._basket_itemoffset[i]
                                 - max(0, itemstart - self._basket_itemoffset[i])
                                 - max(0, self._basket_itemoffset[i + 1] - itemstop))

            if basketstop is not None:
                basketstop += 1    # stop is exclusive

            if basketstart is None:
                return numpy.empty(0, self._interpretation.todtype)

            nocopy = self._interpretation.nocopy()
            destarray = self._interpretation.destarray(numitems, None)
            desti = 0
            for i in range(basketstart, basketstop):
                if self._baskets[i] is None:
                    self._baskets[i] = self._branch.basket(i, nocopy)

                start = max(0, itemstart - self._basket_itemoffset[i])
                stop = self._basket_itemoffset[i + 1] - self._basket_itemoffset[i] - max(0, self._basket_itemoffset[i + 1] - itemstop)

                self._interpretation.filldest(self._baskets[i][start:stop], destarray, desti, desti + (stop - start))
                desti += stop - start

            return destarray

        def _normalize_index(self, i, clip, step):
            lenself = len(self)
            if i < 0:
                j = lenself + i
                if j < 0:
                    if clip:
                        return 0 if step > 0 else lenself
                    else:
                        raise IndexError("index out of range: {0} for length {1}".format(i, lenself))
                else:
                    return j
            elif i < lenself:
                return i
            elif clip:
                return lenself if step > 0 else 0
            else:
                raise IndexError("index out of range: {0} for length {1}".format(i, lenself))

        def _normalize_slice(self, s):
            lenself = len(self)
            if s.step is None:
                step = 1
            else:
                step = s.step
            if step == 0:
                raise ValueError("slice step cannot be zero")
            if s.start is None:
                if step > 0:
                    start = 0
                else:
                    start = lenself - 1
            else:
                start = self._normalize_index(s.start, True, step)
            if s.stop is None:
                if step > 0:
                    stop = lenself
                else:
                    stop = -1
            else:
                stop = self._normalize_index(s.stop, True, step)

            return start, stop, step

    class _BasketKey(object):
        def __init__(self, source, cursor, compression, complete):
            start = cursor.index
            self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir = cursor.fields(source, TBranchMethods._BasketKey._format_small)

            if self.fVersion > 1000:
                cursor.index = start
                self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir = cursor.fields(source, TBranchMethods._BasketKey._format_big)

            if complete:
                cursor.skipstring(source)
                cursor.skipstring(source)
                cursor.skipstring(source)

                self.fVersion, self.fBufferSize, self.fNevBufSize, self.fNevBuf, self.fLast = cursor.fields(source, TBranchMethods._BasketKey._format_complete)

                self.border = self.fLast - self.fKeylen

                if self.fObjlen != self.fNbytes - self.fKeylen:
                    self.source = uproot.source.compressed.CompressedSource(compression, source, Cursor(self.fSeekKey + self.fKeylen), self.fNbytes - self.fKeylen, self.fObjlen)
                    self.cursor = Cursor(0)
                else:
                    self.source = source
                    self.cursor = Cursor(self.fSeekKey + self.fKeylen)

        _format_small = struct.Struct(">ihiIhhii")
        _format_big = struct.Struct(">ihiIhhqq")
        _format_complete = struct.Struct(">Hiiii")

    def _basketkey(self, source, i, complete):
        if not 0 <= i < self.numbaskets:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))
        return self._BasketKey(source.parent(), Cursor(self.fBasketSeek[i]), uproot.source.compressed.Compression(self.fCompress), complete)
        
    def __len__(self):
        return self.numentries

    def __getitem__(self, name):
        return self.branch(name)

    def __iter__(self):
        # prevent Python's attempt to interpret __len__ and __getitem__ as iteration
        raise TypeError("'TBranch' object is not iterable")

uproot.rootio.methods["TBranch"] = TBranchMethods
