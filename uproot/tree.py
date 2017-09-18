#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import namedtuple
from functools import reduce
import re
import sys

import numpy

import uproot._walker.arraywalker
import uproot._walker.lazyarraywalker
import uproot.rootio
import uproot.core

def _delayedraise(cls, err, trc):
    if sys.version_info[0] <= 2:
        exec("raise cls, err, trc")
    else:
        raise err.with_traceback(trc)
    
class TTree(uproot.core.TNamed,
            uproot.core.TAttLine,
            uproot.core.TAttFill,
            uproot.core.TAttMarker):
    """Represents a TTree, a table of data (possibly a ragged table, as some types allow for multiple items per TTree entry).

    Reading data:

        * `tree.arrays(...)` gets all or selected branches as arrays. It has many options; see help(TTree.arrays).
        * `tree.array(branch, ...)` gets a single branch as an array. It has many options; see help(TTree.array).
        * `tree.iterator(numentries, ...)` iterates over a fixed number of numentries at a time. It has many options; see help(TTree.iterator).

    Information about the tree:

        * `tree.numentries` is the number of entries.
        * `tree.branch(name)` gets a branch object by name.
        * `tree.branches` are the TBranch objects directly attached to the TTree's root.
        * `tree.allbranches` are all the TBranch objects, recursively following branches' branches.
        * `tree.branchnames` are all the directly attached branch names.
        * `tree.allbranchnames` are all the branch names, recursively following branches' branches.
        * `tree.branchtypes` is a `{name: dtype}` dict of all the directly attached branch names.
        * `tree.allbranchtypes` is a `{name: dtype}` dict of all the branch names, recursively following branches' branches.
        * `tree.leaves` are all the TLeaf objects.
        * `tree.counter` is a dict from branch names to Counter(branch, leaf) for branches that may have multiple items per TTree entry.

    `tree[name]` is a synonym for `tree.branch(name)`.

    TTree is not iterable, but `len(tree)` is a synonym for `tree.numentries`.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        uproot.core.TNamed.__init__(self, filewalker, walker)
        uproot.core.TAttLine.__init__(self, filewalker, walker)
        uproot.core.TAttFill.__init__(self, filewalker, walker)
        uproot.core.TAttMarker.__init__(self, filewalker, walker)

        self.numentries, totbytes, zipbytes = walker.readfields("!qqq")

        if vers < 16:
            raise NotImplementedError("TTree too old")

        if vers >= 16:
            walker.skip("!q")  # fSavedBytes

        if vers >= 18:
            walker.skip("!q")  # flushed bytes

        walker.skip("!diii")   # fWeight, fTimerInterval, fScanField, fUpdate

        if vers >= 17:
            walker.skip("!i")  # fDefaultEntryOffsetLen

        if vers >= 19:
            nclus = walker.readfield("!i")  # fNClusterRange

        walker.skip("!qqqq")   # fMaxEntries, fMaxEntryLoop, fMaxVirtualSize, fAutoSave

        if vers >= 18:
            walker.skip("!q")  # fAutoFlush

        walker.skip("!q")      # fEstimate

        if vers >= 19:         # "FIXME" in go-hep
            walker.skip(1)
            walker.skip(nclus * 8)   # fClusterRangeEnd
            walker.skip(1)
            walker.skip(nclus * 8)   # fClusterSize

        self.branches = list(uproot.core.TObjArray(filewalker, walker))
        self.leaves = list(uproot.core.TObjArray(filewalker, walker))

        for i in range(7):
            # fAliases, fIndexValues, fIndex, fTreeIndex, fFriends, fUserInfo, fBranchRef
            uproot.rootio.Deserialized._deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

        leaves2branches = {}
        def recurse(obj):
            for branch in obj.branches:
                for leaf in branch.leaves:
                    leaves2branches[leaf.name] = branch.name
                recurse(branch)
        recurse(self)

        self.counter = {}
        def recurse(obj):
            for branch in obj.branches:
                for leaf in branch.leaves:
                    if leaf.counter is not None:
                        leafname = leaf.counter.name
                        branchname = leaves2branches[leafname]
                        self.counter[branch.name] = self.Counter(branchname, leafname)
                recurse(branch)
        recurse(self)

    Counter = namedtuple("Counter", ["branch", "leaf"])

    def __del__(self):
        del self.branches

    def __repr__(self):
        return "<TTree {0} len={1} at 0x{2:012x}>".format(repr(self.name), self.numentries, id(self))

    def __len__(self):
        return len(self.numentries)

    def __getitem__(self, name):
        return self.branch(name)

    def __iter__(self):
        # prevent Python's attempt to interpret __len__ and __getitem__ as iteration
        raise TypeError("'TTree' object is not iterable")

    def branch(self, name):
        """Get a branch object by name.
        """
        if isinstance(name, str):
            name = name.encode("ascii")

        for branch in self.branches:
            if branch.name == name:
                return branch

            if isinstance(branch, TBranchElement):
                try:
                    return branch.branch(name)
                except KeyError:
                    pass

        raise KeyError("not found: {0}".format(repr(name)))

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
    def branchtypes(self):
        return dict((branch.name, branch.dtype) for branch in self.branches)

    @property
    def allbranchtypes(self):
        return dict((branch.name, branch.dtype) for branch in self.allbranches)

    @staticmethod
    def _normalizeselection(branchdtypes, allbranches):
        if callable(branchdtypes):
            for branch in allbranches:
                dtype = branchdtypes(branch)
                if dtype is not None:
                    if isinstance(dtype, numpy.ndarray):
                        dtype = dtype.reshape(reduce(lambda x, y: x*y, dtype.shape, 1))
                    elif not isinstance(dtype, numpy.dtype):
                        dtype = numpy.dtype(dtype)
                    yield branch, dtype

        elif isinstance(branchdtypes, dict):
            allbranches = dict((x.name, x) for x in allbranches)
            for name, dtype in branchdtypes.items():
                if hasattr(name, "encode"):
                    name = name.encode("ascii")
                if name in allbranches:
                    branch = allbranches[name]
                    if hasattr(branch, "dtype"):
                        if isinstance(dtype, numpy.ndarray):
                            dtype = dtype.reshape(reduce(lambda x, y: x*y, dtype.shape, 1))
                        elif not isinstance(dtype, numpy.dtype):
                            dtype = numpy.dtype(dtype)
                        yield branch, dtype
                    else:
                        raise ValueError("cannot produce an array from branch {0}".format(repr(name)))
                else:
                    raise ValueError("cannot find branch {0}".format(repr(name)))

        elif isinstance(branchdtypes, (str, bytes)):
            if hasattr(branchdtypes, "encode"):
                name = branchdtypes.encode("ascii")
            else:
                name = branchdtypes

            branch = [x for x in allbranches if x.name == name]
            if len(branch) == 1:
                if hasattr(branch[0], "dtype"):
                    yield branch[0], branch[0].dtype
                else:
                    raise ValueError("cannot produce an array from branch {0}".format(repr(name)))
            else:
                raise ValueError("cannot find branch {0}".format(repr(name)))

        else:
            try:
                names = [x.encode("ascii") if hasattr(x, "encode") else x for x in branchdtypes]
            except:
                raise TypeError("branchdtypes argument not understood")
            else:
                allbranches = dict((x.name, x) for x in allbranches)
                for name in names:
                    if name in allbranches:
                        branch = allbranches[name]
                        if hasattr(branch, "dtype"):
                            yield branch, dtype
                        else:
                            raise ValueError("cannot produce an array from branch {0}".format(repr(name)))
                    else:
                        raise ValueError("cannot find branch {0}".format(repr(name)))

    def iterator(self, entries, branchdtypes=lambda branch: branch.dtype, executor=None, outputtype=dict, reportentries=False):
        """Iterates over a fixed number of entries at a time.

        Instead of loading all entries from a tree with `tree.arrays()`, load a manageable number that will fit in memory at once and apply a continuous process to it. Example use:

            for px, py in tree.iterator(10000, ["px", "py"], outputtype=tuple):
                do_something(sqrt(px**2 + py**2))

        Arguments:

            * `entries` *(required)*

              If a positive integer, the number of entries to yield in each step of iteration.
              Otherwise, `entries` is interpreted as an iterable over `(entrystart, entryend)` ranges, which must be strictly increasing.

            * `branchdtypes` (same as in `TTree.arrays`)

              If a single string, the string names the only branch to load.
              If an iterable of strings, all of these are loaded (in the specified order).
              If a dict of `{name: dtype}`, load the specified branch names and cast them into a given `dtype` (such as conversion to little endian).
              If a function from branch names to `dtype` or `None`, load the branches into the given `dtypes` and don't load the branches mapped to `None`.

              If any `dtypes` are actually arrays, rather than `dtype` objects, then those arrays will be filled instead of creating new ones (shape must match).

            * `executor` (same as in `TTree.arrays`)

              A `concurrent.futures.Executor` that would be used to parallelize the basket loading/decompression.
              If `None`, the process is serial.

            * `outputtype` (same as in `TTree.arrays`)

              Constructor for the objects to yield in the iterator. Good choices include `dict`, `tuple`, `namedtuple`, `list`.

            * `reportentries`

              If `True`, yield `(entrystart, entryend, data)` instead of just `data`. Intended as a convenience or cross-check for analysis.
        """
        if isinstance(entries, int):
            if entries < 1:
                raise ValueError("number of entries per iteration must be at least 1")
            if sys.version_info[0] <= 2:
                ranges = ((x, x + entries) for x in xrange(0, self.numentries, entries))
            else:
                ranges = ((x, x + entries) for x in range(0, self.numentries, entries))
        else:
            ranges = entries

        toget = []
        for branch, dtype in self._normalizeselection(branchdtypes, self.allbranches):
            toget.append((branch, dtype, []))
            if not hasattr(branch, "basketwalkers"):
                branch._preparebaskets()

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, dtype, cache in toget])

        lastentryend = None
        for entrystart, entryend in ranges:
            if lastentryend is not None and entrystart < lastentryend:
                raise ValueError("entries expressed as (entrystart, entryend) pairs must always have entrystart[i+1] >= entryend[i], but entrystart[i+1] is {0} and entryend[i] is {1}".format(entrystart, lastentryend))
            lastentryend = entryend

            def dobranch(branchdtypecache):
                branch, dtype, cache = branchdtypecache

                # always addtocache before delfromcache so that it doesn't forget the last basketnumber (i)
                branch._addtocache(cache, entrystart, entryend, executor is not None)
                branch._delfromcache(cache, entrystart)

                out = branch._getfromcache(cache, entrystart, entryend, dtype)

                if issubclass(outputtype, dict):
                    return branch.name, out
                else:
                    return out

            if executor is None:
                out = [dobranch(x) for x in toget]
            else:
                out = list(executor.map(dobranch, toget))

            if issubclass(outputtype, dict) or outputtype == tuple or outputtype == list:
                out = outputtype(out)
            else:
                out = outputtype(*out)

            if reportentries:
                yield entrystart, min(entryend, self.numentries), out
            else:
                yield out

    def arrays(self, branchdtypes=lambda branch: branch.dtype, executor=None, outputtype=dict, block=True):
        """Extracts whole branches into Numpy arrays.

        Individual branches from TTrees are typically small enough to fit into memory. If this is not your case, consider `tree.iterator(entries)` to load a given number of entries at a time.

        Arguments:

            * `branchdtypes` (same as in `TTree.iterator`)

              If a single string, the string names the only branch to load.
              If an iterable of strings, all of these are loaded (in the specified order).
              If a dict of `{name: dtype}`, load the specified branch names and cast them into a given `dtype` (such as conversion to little endian).
              If a function from branch names to `dtype` or `None`, load the branches into the given `dtypes` and don't load the branches mapped to `None`.

              If any `dtypes` are actually arrays, rather than `dtype` objects, then those arrays will be filled instead of creating new ones (shape must match).

            * `executor` (same as in `TTree.iterator`)

              A `concurrent.futures.Executor` that would be used to parallelize the basket loading/decompression.
              If `None`, the process is serial.

            * `outputtype` (same as in `TTree.iterator`)

              Constructor for the objects to yield in the iterator. Good choices include `dict`, `tuple`, `namedtuple`, `list`.

            * `block`

              If `True` and parallel processing with an `executor`, return `data, errors` instead of just `data`, where `errors` is a generator of exceptions raised by the parallel threads.
              When you're ready to wait for all threads to finish, evaluate the `errors` generator.
        """
        toget = []
        for branch, dtype in self._normalizeselection(branchdtypes, self.allbranches):
            toget.append((branch, dtype))
            if not hasattr(branch, "basketwalkers"):
                branch._preparebaskets()

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, dtype in toget])

        out = []
        errorslist = []
        for branch, dtype in toget:
            outi, res = branch.array(dtype, executor, False)
            if outputtype == dict:
                out.append((branch.name, outi))
            else:
                out.append(outi)
            errorslist.append(res)

        if issubclass(outputtype, dict) or outputtype == tuple or outputtype == list:
            out = outputtype(out)
        else:
            out = outputtype(*out)

        if block:
            for errors in errorslist:
                for cls, err, trc in errors:
                    if cls is not None:
                        _delayedraise(cls, err, trc)
            return out
        else:
            return out, (item for sublist in errorslist for item in sublist)

    def array(self, branch, dtype=None, executor=None, block=True):
        """Extracts a whole branch into a Numpy array.

        Individual branches from TTrees are typically small enough to fit into memory. If this is not your case, consider `tree.iterator(entries)` to load a given number of entries at a time.

        Arguments:

            * `branch` *(required)*

               Branch name to extract.

            * `dtype`

               If not `None`, cast the array into a given `dtype` (such as conversion to little endian).
               If an array object, fill that array instead of creating a new one (shape must match).

            * `executor` (same as in `TTree.arrays`)

              A `concurrent.futures.Executor` that would be used to parallelize the basket loading/decompression.
              If `None`, the process is serial.

            * `block`

              If `True` and parallel processing with an `executor`, return `data, errors` instead of just `data`, where `errors` is a generator of exceptions raised by the parallel threads.
              When you're ready to wait for all threads to finish, evaluate the `errors` generator.
        """
        branch = branch.encode("ascii") if hasattr(branch, "encode") else branch

        if dtype is None:
            branchdtypes = branch
        else:
            branchdtypes = {branch: dtype}

        if block:
            out, = self.arrays(branchdtypes=branchdtypes, executor=executor, outputtype=tuple, block=block)
            return out
        else:
            (out,), errors = self.arrays(branchdtypes=branchdtypes, executor=executor, outputtype=tuple, block=block)
            return out, errors

uproot.rootio.Deserialized.classes[b"TTree"] = TTree

## TODO: this is a good candidate for acceleration with Numba...
if sys.version_info[0] <= 2:
    def _fixspeedbumps(array, outdata, offs):
        outi = 0
        for i in xrange(len(offs) - 1):
            length = offs[i + 1] - offs[i] - 1
            outdata[outi:outi + length] = array[offs[i] + 1:offs[i + 1]]
            outi += length
else:
    def _fixspeedbumps(array, outdata, offs):
        outi = 0
        for i in range(len(offs) - 1):
            length = offs[i + 1] - offs[i] - 1
            outdata[outi:outi + length] = array[offs[i] + 1:offs[i + 1]]
            outi += length

class TBranch(uproot.core.TNamed,
              uproot.core.TAttFill):
    """Represents a TBranch, a single column of data in a TTree.

    Reading data:

        * `branch.array(...)` gets the branch as an array. It has many options; see help(TBranch.array).
        * `tree.iterator(entries, ...)` iterates over a fixed number of entries at a time. It has many options; see help(TTree.iterator).

    Information about the branch:

        * `branch.itemdims` are the fixed (non-counter) dimensions of this branch, derived from its title.
        * `branch.branch(name)` gets a subbranch object by name.
        * `branch.branches` are the subbranches directly attached to this TBranch.
        * `branch.allbranches` are all the subbranches, recursively following subbranches' branches.
        * `branch.branchnames` are all the directly attached subbranch names.
        * `branch.allbranchnames` are all the subbranch names, recursively following subbranches' branches.
        * `branch.branchtypes` is a `{name: dtype}` dict of all the directly attached subbranch names.
        * `branch.allbranchtypes` is a `{name: dtype}` dict of all the subbranch names, recursively following subbranches' branches.
        * `branch.leaves` are all the TLeaf objects directly attached to this TBranch.
        * `branch.numbaskets` is the number of baskets.

    `branch[name]` is a synonym for `branch.branch(name)`.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        if vers < 11:
            raise NotImplementedError("TBranch version too old")

        uproot.core.TNamed.__init__(self, filewalker, walker)
        uproot.core.TAttFill.__init__(self, filewalker, walker)

        compression, basketSize, entryOffsetLen, writeBasket, entryNumber, offset, maxBaskets, splitLevel, entries, firstEntry, totBytes, zipBytes = walker.readfields("!iiiiqiiiqqqq")
        self.compression = uproot.rootio._interpret_compression(compression)

        self.branches = list(uproot.core.TObjArray(filewalker, walker))
        self.leaves = list(uproot.core.TObjArray(filewalker, walker))
        walker.skipbcnt() # reading baskets is expensive and useless

        walker.skip(1)  # isArray
        # self.basketBytes = walker.readarray(">i4", maxBaskets)[:writeBasket]
        walker.skip(4 * maxBaskets)

        walker.skip(1)  # isArray
        self._basketEntry = walker.readarray(">i8", maxBaskets)[:writeBasket]

        walker.skip(1)  # isArray
        self._basketSeek = walker.readarray(">i8", maxBaskets)[:writeBasket]

        fname = walker.readstring()

        self._checkbytecount(walker.index - start, bcnt)

        if len(self.leaves) == 1 and hasattr(self.leaves[0], "dtype"):
            self.dtype = self.leaves[0].dtype
            self._speedbumps = self.leaves[0]._speedbumps

        self._filewalker = filewalker

        self.itemdims = tuple(int(x) for x in re.findall(self._itemdimpattern, self.title))

    _itemdimpattern = re.compile(b"\[([1-9][0-9]*)\]")

    def __del__(self):
        del self.branches
        del self._filewalker

    @property
    def numbaskets(self):
        return len(self._basketSeek)

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
    def branchtypes(self):
        return dict((branch.name, branch.dtype) for branch in self.branches)

    @property
    def allbranchtypes(self):
        return dict((branch.name, branch.dtype) for branch in self.allbranches)

    def __getitem__(self, name):
        return self.branch(name)

    def __iter__(self):
        # prevent Python's attempt to interpret __getitem__ as iteration
        raise TypeError("'TBranch' object is not iterable")

    def branch(self, name):
        """Get a subbranch object by name.
        """
        if isinstance(name, str):
            name = name.encode("ascii")

        for branch in self.branches:
            if branch.name == name:
                return branch
            try:
                return branch.branch(name)
            except KeyError:
                pass

        raise KeyError("not found: {0}".format(repr(name)))

    def _preparebaskets(self):
        self._filewalker.startcontext()

        self._basketobjlens = []
        self._basketkeylens = []
        self._basketborders = []
        self._basketlengths = []
        self._basketwalkers = []
        for seek in self._basketSeek:
            basketwalker = self._filewalker.copy(seek)
            basketwalker.startcontext()

            bytes, version, objlen, datetime, keylen, cycle = basketwalker.readfields("!ihiIhh")
            if version > 1000:
                seekkey, seekpdir = basketwalker.readfields("!qq")
            else:
                seekkey, seekpdir = basketwalker.readfields("!ii")

            self._basketobjlens.append(objlen)
            self._basketkeylens.append(keylen)

            classname = basketwalker.readstring()
            name = basketwalker.readstring()
            title = basketwalker.readstring()
            vers, bufsize, nevsize, nevbuf, last, flag = basketwalker.readfields("!HiiiiB")
            border = last - keylen

            self._basketborders.append(border)
            if self._speedbumps:
                self._basketlengths.append(border - (objlen - border - 8) // 4)
            else:
                self._basketlengths.append(border)

            #  object size != compressed size means it's compressed
            if objlen != bytes - keylen:
                function = uproot.rootio._decompressfcn(self.compression, objlen)
                self._basketwalkers.append(uproot._walker.lazyarraywalker.LazyArrayWalker(self._filewalker.copy(seekkey + keylen), function, bytes - keylen))

            # otherwise, it's uncompressed
            else:
                self._basketwalkers.append(self._filewalker.copy(seek + keylen))

    def _basket(self, i, offsets=False, parallel=False):
        self._basketwalkers[i]._evaluate(parallel)
        self._basketwalkers[i].startcontext()
        start = self._basketwalkers[i].index

        try:
            if self.dtype == numpy.dtype(object) or self._speedbumps:
                array = self._basketwalkers[i].readarray(numpy.uint8, self._basketobjlens[i])
            else:
                array = self._basketwalkers[i].readarray(self.dtype, self._basketobjlens[i] // self.dtype.itemsize)
        finally:
            self._basketwalkers[i]._unevaluate()
            self._basketwalkers[i].index = start

        if self._speedbumps:
            offs = array[self._basketborders[i] + 4:].view(">i4") - self._basketkeylens[i]
            offs[-1] = self._basketborders[i]

            outdata = numpy.empty(self._basketborders[i] - (len(offs) - 1), dtype=numpy.uint8)
            _fixspeedbumps(array, outdata, offs)

            if offsets:
                return outdata.view(self.dtype), None
            else:
                return outdata.view(self.dtype)

        if self.dtype == numpy.dtype(object):
            dataend = self._basketborders[i]
        else:
            dataend = self._basketborders[i] // self.dtype.itemsize
                
        if offsets:
            if dataend == len(array):
                return array, None
            else:
                outdata = array[:dataend]
                outoff = array.view(numpy.uint8)[self._basketborders[i] + 4 : -4].view(">i4") - self._basketkeylens[i]
                return outdata, outoff

        elif dataend < len(array):
            return array[:dataend]

        else:
            return array

    def _adddimensions(self, array):
        if self.itemdims == () or len(array.shape) != 1:
            return array
        else:
            product = reduce(lambda x, y: x*y, self.itemdims, 1)
            if len(array) % product != 0:
                return array
            else:
                newlen = len(array) // product
                return array.reshape((newlen,) + self.itemdims)

    def _addtocache(self, cache, entrystart, entryend, parallel=False):
        if len(cache) == 0:
            i = 0
        else:
            i = cache[-1][0] + 1

        while i < len(self._basketEntry) and entryend > self._basketEntry[i]:
            if i + 1 >= len(self._basketEntry) or self._basketEntry[i + 1] > entrystart:
                data, off = self._basket(i, offsets=True, parallel=parallel)
                cache.append((i, data, off))
            i += 1

    def _delfromcache(self, cache, entrystart):
        firsttokeep = 0
        for i, data, off in cache:
            if i + 1 < len(self._basketEntry) and self._basketEntry[i + 1] <= entrystart:
                firsttokeep += 1
            else:
                break
        del cache[:firsttokeep]

    def _getfromcache(self, cache, entrystart, entryend, dtype):
        if len(cache) == 0:
            if isinstance(dtype, numpy.ndarray):
                out = dtype.reshape(reduce(lambda x, y: x*y, dtype.shape, 1))
                dtype = out.dtype
                if out.shape != (0,):
                    raise ValueError("provided array does not have the right number of elements: {0}".format(0))
                return self._adddimensions(out)
            else:
                return self._adddimensions(numpy.array([], dtype=dtype))

        i, firstdata, firstoff = cache[0]
        istartoff = entrystart - self._basketEntry[i]
        if firstoff is None:
            istart = istartoff
        else:
            istart = firstoff[istartoff]

        i, lastdata, lastoff = cache[-1]
        iendoff = entryend - self._basketEntry[i]
        if lastoff is None:
            iend = min(iendoff, len(lastdata))
        elif iendoff < len(lastoff):
            iendoff = min(iendoff, len(lastoff))
            iend = lastoff[iendoff]
        else:
            iendoff = min(iendoff, len(lastoff))
            iend = len(lastdata)

        strings = (dtype == numpy.dtype(object))

        if len(cache) == 1:
            outdata = firstdata[istart:iend]
            if not strings:
                if isinstance(dtype, numpy.ndarray):
                    out = dtype
                    dtype = out.dtype
                    expected = len(firstdata)
                    if out.shape != (expected,):
                        raise ValueError("provided array does not have the right number of elements: {0}".format(expected))
                    out[:] = outdata
                    outdata = out
                else:
                    outdata = numpy.array(outdata, dtype=dtype)
            else:
                outoff = firstoff[istartoff:iendoff] - istart

        else:
            middle = cache[1:-1]
            size = (len(firstdata) - istart) + sum(len(mdata) for mi, mdata, moff in middle) + (iend)

            if isinstance(dtype, numpy.ndarray):
                outdata = dtype
                dtype = outdata.dtype
                if outdata.shape != (size,):
                    raise ValueError("provided array does not have the right number of elements: {0}".format(size))
            else:
                outdata = numpy.empty(size, dtype=numpy.uint8 if strings else dtype)

            if strings:
                outoff = numpy.empty((len(firstoff) - istartoff) + sum(len(moff) for mi, mdata, moff in middle) + (iendoff), dtype=firstoff.dtype)

            i = len(firstdata) - istart
            outdata[:i] = firstdata[istart:]
            if strings:
                ioff = len(firstoff) - istartoff
                outoff[:ioff] = firstoff[istartoff:] - istart
                correction = i

            for mi, mdata, moff in middle:
                outdata[i:i + len(mdata)] = mdata
                i += len(mdata)
                if strings:
                    outoff[ioff:ioff + len(moff)] = moff + correction
                    ioff += len(moff)
                    correction += len(mdata)

            outdata[i:] = lastdata[:iend]
            if strings:
                outoff[ioff:] = lastoff[:iendoff] + correction

        if strings:
            out = numpy.empty(len(outoff), dtype=numpy.dtype(object))
            for j, offset in enumerate(outoff):
                size = outdata[offset]
                out[j] = outdata[offset + 1:offset + 1 + size].tostring()
            return self._adddimensions(out)
        else:
            return self._adddimensions(outdata)

    def array(self, dtype=None, executor=None, block=True):
        """Extracts the whole branch into a Numpy array.

        Individual branches are typically small enough to fit into memory. If this is not your case, consider `tree.iterator(entries)` to load a given number of entries at a time.

        Arguments:

            * `dtype`

               If not `None`, cast the array into a given `dtype` (such as conversion to little endian).
               If an array object, fill that array instead of creating a new one (shape must match).

            * `executor` (same as in `TTree.array`)

              A `concurrent.futures.Executor` that would be used to parallelize the basket loading/decompression.
              If `None`, the process is serial.

            * `block`

              If `True` and parallel processing with an `executor`, return `data, errors` instead of just `data`, where `errors` is a generator of exceptions raised by the parallel threads.
              When you're ready to wait for all threads to finish, evaluate the `errors` generator.
        """

        if not hasattr(self, "basketwalkers"):
            self._preparebaskets()

        if isinstance(dtype, numpy.ndarray):
            out = dtype.reshape(reduce(lambda x, y: x*y, dtype.shape, 1))
            dtype = out.dtype
            expected = sum(self._basketlengths) // dtype.itemsize
            if out.shape != (expected,):
                raise ValueError("provided array does not have the right number of elements: {0}".format(expected))

        else:
            if dtype is None:
                dtype = self.dtype

            if not isinstance(dtype, numpy.dtype):
                dtype = numpy.dtype(dtype)

            if dtype == numpy.dtype(object):
                return self._adddimensions(self._strings(executor, block))

            out = numpy.empty(sum(self._basketlengths) // dtype.itemsize, dtype=dtype)

        if executor is None:
            start = 0
            for i in range(len(self._basketwalkers)):
                end = start + self._basketlengths[i] // dtype.itemsize
                out[start:end] = self._basket(i, parallel=False)
                start = end

            if block:
                return self._adddimensions(out)
            else:
                return self._adddimensions(out), ()

        else:
            ends = (numpy.cumsum(self._basketlengths) // dtype.itemsize).tolist()
            starts = [0] + ends[:-1]

            def fill(i):
                try:
                    out[starts[i]:ends[i]] = self._basket(i, parallel=True)
                except:
                    return sys.exc_info()
                else:
                    return None, None, None

            errors = executor.map(fill, range(len(self._basketwalkers)))
            if block:
                for cls, err, trc in errors:
                    if cls is not None:
                        _delayedraise(cls, err, trc)
                return self._adddimensions(out)
            else:
                return self._adddimensions(out), errors

    def _strings(self, executor, block):
        out = numpy.empty(sum((self._basketobjlens[i] - self._basketborders[i] - 8) // 4 for i in range(len(self._basketobjlens))), dtype=numpy.dtype(object))

        if executor is None:
            for i in range(len(self._basketwalkers)):
                data, offsets = self._basket(i, offsets=True, parallel=False)
                for j, offset in enumerate(offsets):
                    size = data[offset]
                    out[self._basketEntry[i] + j] = data[offset + 1:offset + 1 + size].tostring()

            if block:
                return out
            else:
                return out, ()

        else:
            def fill(i):
                try:
                    data, offsets = self._basket(i, offsets=True, parallel=True)
                    for j, offset in enumerate(offsets):
                        size = data[offset]
                        out[self._basketEntry[i] + j] = data[offset + 1:offset + 1 + size].tostring()
                except:
                    return sys.exc_info()
                else:
                    return None, None, None

            errors = executor.map(fill, range(len(self._basketwalkers)))
            if block:
                for cls, err, trc in errors:
                    if cls is not None:
                        _delayedraise(cls, err, trc)
                return out
            else:
                return out, errors

uproot.rootio.Deserialized.classes[b"TBranch"] = TBranch

class TBranchElement(TBranch):
    """Represents a TBranchElement, a column of data represented an object that has been split.

    All methods and members are the same as TBranch.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        if vers < 9:
            raise NotImplementedError("TBranchElement version too old")

        TBranch.__init__(self, filewalker, walker)

        self.classname = walker.readstring()
        parent = walker.readstring()
        clones = walker.readstring()

        checksum = walker.readfield("!I")
        if vers >= 10:
            classversion = walker.readfield("!H")
        else:
            classversion = walker.readfield("!I")
        identifier, btype, stype, themax = walker.readfields("!iiii")
            
        bcount1 = uproot.rootio.Deserialized._deserialize(filewalker, walker)
        bcount2 = uproot.rootio.Deserialized._deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

    def array(self, dtype=None, executor=None, block=True):
        """Extracts the whole branch into a Numpy array.

        Individual branches are typically small enough to fit into memory. If this is not your case, consider `tree.iterator(entries)` to load a given number of entries at a time.

        Arguments:

            * `dtype`

               If not `None`, cast the array into a given `dtype` (such as conversion to little endian).
               If an array object, fill that array instead of creating a new one (shape must match).

            * `executor` (same as in `TTree.array`)

              A `concurrent.futures.Executor` that would be used to parallelize the basket loading/decompression.
              If `None`, the process is serial.

            * `block`

              If `True` and parallel processing with an `executor`, return `data, errors` instead of just `data`, where `errors` is a generator of exceptions raised by the parallel threads.
              When you're ready to wait for all threads to finish, evaluate the `errors` generator.
        """
        if hasattr(self, "dtype"):
            return TBranch.array(self, dtype, executor, block)
        else:
            raise NotImplementedError

uproot.rootio.Deserialized.classes[b"TBranchElement"] = TBranchElement

class TLeaf(uproot.core.TNamed):
    """Represents a TLeaf object, which is only used for type and dimensionality information.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        uproot.core.TNamed.__init__(self, filewalker, walker)

        len, etype, offset, hasrange, self.unsigned = walker.readfields("!iii??")
        self.counter = uproot.rootio.Deserialized._deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

uproot.rootio.Deserialized.classes[b"TLeaf"] = TLeaf

for classname, format, dtype1, dtype2 in [
    ("TLeafO", "!??", "bool", "bool"),
    ("TLeafB", "!bb", "i1", "u1"),
    ("TLeafS", "!hh", ">i2", ">u2"),
    ("TLeafI", "!ii", ">i4", ">u4"),
    ("TLeafL", "!qq", ">i8", ">u8"),
    ("TLeafF", "!ff", ">f4", ">f4"),
    ("TLeafD", "!dd", ">f8", ">f8"),
    ("TLeafC", "!ii", "object", "object"),
    ("TLeafObject", "!ii", "object", "object"),
    ]:
    exec("""
class {0}(TLeaf):
    "Represents a {0} object, which is only used for type and dimensionality information."
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        TLeaf.__init__(self, filewalker, walker)

        min, max = walker.readfields("{1}")
        if self.unsigned:
            self.dtype = numpy.dtype("{3}")
        else:
            self.dtype = numpy.dtype("{2}")
        self._speedbumps = False
        
        self._checkbytecount(walker.index - start, bcnt)

uproot.rootio.Deserialized.classes[b"{0}"] = {0}
""".format(classname, format, dtype1, dtype2), globals())

class TLeafElement(TLeaf):
    """Represents a TLeafElement object, which is only used for type and dimensionality information.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        TLeaf.__init__(self, filewalker, walker)

        identifier, ltype = walker.readfields("!ii")

        if ltype == 65:
            self.dtype = numpy.dtype(object)

        elif ltype > 0 and ltype % 20 not in (0, 9, 10, 19):
            # typename = [
            #     "", "Char_t",  "Short_t",  "Int_t",  "Long_t",  "Float_t", "Int_t",    "char*",     "Double_t", "Double32_t",
            #     "", "UChar_t", "UShort_t", "UInt_t", "ULong_t", "UInt_t",  "Long64_t", "ULong64_t", "Bool_t",   "Float16_t"
            #     ][ltype % 20]
            self.dtype = numpy.dtype([
                None, "i1", ">i2", ">i4", ">i8", ">f4", ">i4", "u1",  ">f8",  None,
                None, "u1", ">u2", ">u4", ">u8", ">u4", ">i8", ">u8", "bool", None
                ][ltype % 20])

        elif ltype == -1:  # counter
            self.dtype = numpy.dtype(">i4")

        self._speedbumps = 40 <= ltype < 60

        self._checkbytecount(walker.index - start, bcnt)

uproot.rootio.Deserialized.classes[b"TLeafElement"] = TLeafElement
