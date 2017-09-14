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
import sys

import numpy

import uproot.walker.arraywalker
import uproot.walker.lazyarraywalker
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
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        uproot.core.TNamed.__init__(self, filewalker, walker)
        uproot.core.TAttLine.__init__(self, filewalker, walker)
        uproot.core.TAttFill.__init__(self, filewalker, walker)
        uproot.core.TAttMarker.__init__(self, filewalker, walker)

        self.entries, totbytes, zipbytes = walker.readfields("!qqq")

        if vers < 16:
            raise NotImplementedError("TTree too old")
        elif vers == 16:
            walker.skip(8)

        if vers >= 19:
            walker.skip("!q")  # fSavedBytes

        if vers >= 18:
            walker.skip("!q")  # flushed bytes

        walker.skip("!diii")   # fWeight, fTimerInterval, fScanField, fUpdate

        if vers >= 18:
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

        self.branches = uproot.core.TObjArray(filewalker, walker)
        self.leaves = uproot.core.TObjArray(filewalker, walker)

        for i in range(7):
            # fAliases, fIndexValues, fIndex, fTreeIndex, fFriends, fUserInfo, fBranchRef
            uproot.rootio.Deserialized.deserialize(filewalker, walker)

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

    def __repr__(self):
        return "<TTree {0} len={1} at 0x{2:012x}>".format(repr(self.name), self.entries, id(self))

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, name):
        return self.branch(name)

    def __iter__(self):
        # prevent Python's attempt to interpret __len__ and __getitem__ as iteration
        raise TypeError("'TTree' object is not iterable")

    def branch(self, name):
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
        def recurse(obj):
            for branch in obj.branches:
                yield branch
                for x in recurse(branch):
                    yield x
        return recurse(self)

    def branchnames(self, recursive=True):
        for branch in self.branches:
            yield branch.name
            if recursive:
                for x in branch.branchnames(recursive):
                    yield x

    def arrays(self, branchdtypes=lambda branch: branch.dtype, executor=None, block=True):
        if callable(branchdtypes):
            selection = branchdtypes

        elif isinstance(branchdtypes, dict):
            branchdtypes = dict((name.encode("ascii") if hasattr(name, "encode") else name, dtype) for name, dtype in branchdtypes.items())

            def selection(branch):
                if branch.name in branchdtypes:
                    if hasattr(branch, "dtype"):
                        return branchdtypes[branch.name]
                    else:
                        raise TypeError("cannot produce an array from branch {0}".format(repr(branch.name)))
                else:
                    return None

        elif isinstance(branchdtypes, (str, bytes)):
            branchdtypes = branchdtypes.encode("ascii") if hasattr(branchdtypes, "encode") else branchdtypes
            def selection(branch):
                if branch.name == branchdtypes:
                    return branch.dtype
                else:
                    return None

        else:
            try:
                iter(branchdtypes)
            except:
                raise TypeError("branchdtypes argument not understood")
            else:
                def selection(branch):
                    if branch.name in branchdtypes:
                        if hasattr(branch, "dtype"):
                            return branch.dtype
                        else:
                            raise TypeError("cannot produce an array from branch {0}".format(repr(branch.name)))
                    else:
                        return None

        out = {}
        nested = []
        for branch in self.allbranches:
            dtype = selection(branch)
            if dtype is not None:
                out[branch.name], res = branch.array(dtype, executor, False)
                nested.append(res)

        if block:
            for errors in nested:
                for cls, err, trc in errors:
                    if cls is not None:
                        _delayedraise(cls, err, trc)
            return out
        else:
            return out, (item for sublist in errors for item in sublist)

    def array(self, branch, dtype=None, executor=None, block=True):
        branch = branch.encode("ascii") if hasattr(branch, "encode") else branch

        def branchdtypes(b):
            if branch == b.name:
                if dtype is None:
                    return b.dtype
                else:
                    return dtype
            else:
                return None

        if block:
            out = self.arrays(branchdtypes, executor, block)
            out, = out.values()
            return out
        else:
            out, errors = self.arrays(branchdtypes, executor, block)
            out, = out.values()
            return out, errors

uproot.rootio.Deserialized.classes[b"TTree"] = TTree

class TBranch(uproot.core.TNamed,
              uproot.core.TAttFill):
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

        self.branches = uproot.core.TObjArray(filewalker, walker)
        self.leaves = uproot.core.TObjArray(filewalker, walker)
        walker.skipbcnt() # baskets

        walker.skip(1)  # isArray
        # self.basketBytes = walker.readarray(">i4", maxBaskets)[:writeBasket]
        walker.skip(4 * maxBaskets)

        walker.skip(1)  # isArray
        # self.basketEntry = walker.readarray(">i8", maxBaskets)[:writeBasket]
        walker.skip(8 * maxBaskets)

        walker.skip(1)  # isArray
        self._basketSeek = walker.readarray(">i8", maxBaskets)[:writeBasket]

        fname = walker.readstring()

        self._checkbytecount(walker.index - start, bcnt)

        if len(self.leaves) == 1 and hasattr(self.leaves[0], "dtype"):
            self.dtype = self.leaves[0].dtype
        self._filewalker = filewalker

    def _preparebaskets(self):
        self._filewalker.startcontext()

        self._basketobjlens = []
        self._basketkeylens = []
        self._basketborders = []
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

            #  object size != compressed size means it's compressed
            if objlen != bytes - keylen:
                function = uproot.rootio._decompressfcn(self.compression, objlen)
                self._basketwalkers.append(uproot.walker.lazyarraywalker.LazyArrayWalker(self._filewalker.copy(seekkey + keylen), function, bytes - keylen))

            # otherwise, it's uncompressed
            else:
                self._basketwalkers.append(self._filewalker.copy(seek + keylen))

    def branchnames(self, recursive=True):
        for branch in self.branches:
            yield branch.name
            if recursive:
                for x in branch.branchnames(recursive):
                    yield x

    def basket(self, i, offsets=False, parallel=False):
        self._basketwalkers[i]._evaluate(parallel)
        self._basketwalkers[i].startcontext()
        start = self._basketwalkers[i].index

        try:
            array = self._basketwalkers[i].readarray(self.dtype, self._basketobjlens[i] // self.dtype.itemsize)
        finally:
            self._basketwalkers[i]._unevaluate()
            self._basketwalkers[i].index = start

        if offsets:
            outdata = array[:self._basketborders[i] // self.dtype.itemsize]
            outoff = array.view(numpy.uint8)[self._basketborders[i] + 4 : -4].view(">i4") - self._basketkeylens[i]
            return outdata, outoff
        else:
            return array[:self._basketborders[i] // self.dtype.itemsize]

    def array(self, dtype=None, executor=None, block=True):
        if not hasattr(self, "basketwalkers"):
            self._preparebaskets()

        if dtype is None:
            dtype = self.dtype

        out = numpy.empty(sum(self._basketborders) // self.dtype.itemsize, dtype=dtype)

        if executor is None:
            start = 0
            for i in range(len(self._basketwalkers)):
                end = start + self._basketborders[i] // self.dtype.itemsize
                out[start:end] = self.basket(i, parallel=False)
                start = end

            if block:
                return out
            else:
                return out, ()

        else:
            ends = (numpy.cumsum(self._basketborders) // self.dtype.itemsize).tolist()
            starts = [0] + ends[:-1]

            def fill(i):
                try:
                    out[starts[i]:ends[i]] = self.basket(i, parallel=True)
                except Exception as err:
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

    def strings(self):
        if not hasattr(self, "basketwalkers"):
            self._preparebaskets()

        for i in range(len(self._basketwalkers)):
            data, offsets = self.basket(i, offsets=True)
            for offset in offsets:
                size = data[offset]
                yield data[offset + 1 : offset + 1 + size].tostring()

uproot.rootio.Deserialized.classes[b"TBranch"] = TBranch

class TBranchElement(TBranch):
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
            
        bcount1 = uproot.rootio.Deserialized.deserialize(filewalker, walker)
        bcount2 = uproot.rootio.Deserialized.deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

    def basket(self, i, offsets=False, parallel=False):
        if hasattr(self, "dtype"):
            return TBranch.basket(self, i, offsets, parallel)
        else:
            raise NotImplementedError

    def array(self, dtype=None, executor=None, block=True):
        if hasattr(self, "dtype"):
            return TBranch.array(self, dtype, executor, block)
        else:
            raise NotImplementedError

    def strings(self):
        if hasattr(self, "dtype"):
            return TBranch.strings(self)
        else:
            raise NotImplementedError

    def branch(self, name):
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

uproot.rootio.Deserialized.classes[b"TBranchElement"] = TBranchElement

class TLeaf(uproot.core.TNamed):
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        uproot.core.TNamed.__init__(self, filewalker, walker)

        len, etype, offset, hasrange, unsigned = walker.readfields("!iii??")
        self.counter = uproot.rootio.Deserialized.deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

uproot.rootio.Deserialized.classes[b"TLeaf"] = TLeaf

for classname, format, dtype in [
    ("TLeafO", "!??", "bool"),
    ("TLeafB", "!bb", "i1"),
    ("TLeafS", "!hh", ">i2"),
    ("TLeafI", "!ii", ">i4"),
    ("TLeafL", "!qq", ">i8"),
    ("TLeafF", "!ff", ">f4"),
    ("TLeafD", "!dd", ">f8"),
    ("TLeafC", "!ii", "u1"),
    ("TLeafObject", "!ii", "u1"),
    ]:
    exec("""
class {0}(TLeaf):
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        TLeaf.__init__(self, filewalker, walker)

        self.min, self.max = walker.readfields("{1}")
        self.dtype = numpy.dtype("{2}")

        self._checkbytecount(walker.index - start, bcnt)

uproot.rootio.Deserialized.classes[b"{0}"] = {0}
""".format(classname, format, dtype), globals())

class TLeafElement(TLeaf):
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        TLeaf.__init__(self, filewalker, walker)

        identifier, ltype = walker.readfields("!ii")

        if ltype > 0 and ltype % 20 not in (0, 9, 10, 19):
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

        self._checkbytecount(walker.index - start, bcnt)

uproot.rootio.Deserialized.classes[b"TLeafElement"] = TLeafElement
