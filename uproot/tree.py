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

import numpy

import uproot.walker.lazyarraywalker
import uproot.rootio
import uproot.core

class TTree(uproot.core.TNamed,
            uproot.core.TAttLine,
            uproot.core.TAttFill,
            uproot.core.TAttMarker):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        uproot.core.TNamed.__init__(self, filewalker, walker)
        uproot.core.TAttLine.__init__(self, filewalker, walker)
        uproot.core.TAttFill.__init__(self, filewalker, walker)
        uproot.core.TAttMarker.__init__(self, filewalker, walker)

        self.entries, self.totbytes, self.zipbytes = walker.readfields("!qqq")

        if vers < 16:
            raise NotImplementedError("TTree too old")

        if vers >= 19:
            walker.skip("!q")  # fSavedBytes

        if vers >= 18:
            walker.skip("!q")  # flushed bytes

        walker.skip("!diii")   # fWeight, fTimerInterval, fScanField, fUpdate

        if vers >= 18:
            walker.skip("!i")  # fDefaultEntryOffsetLen

        nclus = 0
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

    def __repr__(self):
        return "<TTree {0} len={1} at 0x{2:012x}>".format(repr(self.name), self.entries, id(self))

    def branch(self, name):
        if isinstance(name, str):
            name = name.encode("ascii")
        for branch in self.branches:
            if branch.name == name:
                return branch
        raise KeyError("not found: {0}".format(repr(name)))
        
uproot.rootio.Deserialized.classes[b"TTree"] = TTree

class TBranch(uproot.core.TNamed,
              uproot.core.TAttFill):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        if vers < 12:
            raise NotImplementedError("TBranch version too old")

        uproot.core.TNamed.__init__(self, filewalker, walker)
        uproot.core.TAttFill.__init__(self, filewalker, walker)

        compression, basketSize, entryOffsetLen, writeBasket, entryNumber, offset, maxBaskets, splitLevel, entries, firstEntry, totBytes, zipBytes = walker.readfields("!iiiiqiiiqqqq")
        self.compression = uproot.rootio.interpret_compression(compression)

        self.branches = uproot.core.TObjArray(filewalker, walker)
        self.leaves = uproot.core.TObjArray(filewalker, walker)
        self.baskets = uproot.core.TObjArray(filewalker, walker)

        walker.skip(1)  # isArray
        self.basketBytes = walker.readarray(">i4", maxBaskets)[:writeBasket]

        walker.skip(1)  # isArray
        self.basketEntry = walker.readarray(">i8", maxBaskets)[:writeBasket]

        walker.skip(1)  # isArray
        self.basketSeek = walker.readarray(">i8", maxBaskets)[:writeBasket]

        fname = walker.readstring()

        self._checkbytecount(walker.index - start, bcnt)

        if len(self.leaves) == 1:
            self.dtype = self.leaves[0].dtype
        self.basketwalkers = [filewalker.copy(x) for x in self.basketSeek]
        self.basketsize = [filewalker.field("!i", index=x + 6) // self.dtype.itemsize for x in self.basketSeek]
        
    def __repr__(self):
        return "<TBranch {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def basket(self, i, offsets=False):
        walker = self.basketwalkers[i]

        # DO NOT CHANGE STATE, so that I can parallelize this later
        index = walker.index
        bytes, version, objlen, datetime, keylen, cycle = walker.fields("!ihiIhh")
        index += walker.size("!ihiIhh")
        if version > 1000:
            seekkey, seekpdir = walker.fields("!qq", index=index)
            index += walker.size("!qq")
        else:
            seekkey, seekpdir = walker.fields("!ii", index=index)
            index += walker.size("!ii")
        if offsets:
            index += walker.sizestring(walker, index)  # classname
            index += walker.sizestring(walker, index)  # name
            index += walker.sizestring(walker, index)  # title
            vers, bufsize, nevsize, nevbuf, last, flag = walker.fields("!HiiiiB", index=index)
            border = last - keylen
        # END DO NOT CHANGE STATE

        #  object size != compressed size means it's compressed
        if objlen != bytes - keylen:
            function = uproot.rootio.decompressfcn(self.compression, objlen)
            walker = uproot.walker.lazyarraywalker.LazyArrayWalker(walker, function, bytes - keylen, seekkey + keylen)
            array = walker.array(self.dtype, self.basketsize[i])

        # otherwise, it's uncompressed
        else:
            array = walker.array(self.dtype, self.basketsize[i], index=walker.index + keylen)

        # if requested, do extra deserialization and manipulation to return offsets array
        if offsets:
            outdata = array[:border // self.dtype.itemsize]
            outoff = array.view(numpy.uint8)[border + 4 : -4].view(">i4") - keylen
            return outdata, outoff
        else:
            return array

    def array(self, dtype=None):
        if dtype is None:
            dtype = self.dtype

        out = numpy.empty(sum(self.basketsize), dtype=dtype)

        start = 0
        for i in range(len(self.basketwalkers)):
            end = start + self.basketsize[i]
            out[start:end] = self.basket(i)
            start = end

        return out

    def strings(self):
        for i in range(len(self.basketwalkers)):
            data, offsets = self.basket(i, offsets=True)
            for offset in offsets:
                size = data[offset]
                yield data[offset + 1 : offset + 1 + size].tostring()

uproot.rootio.Deserialized.classes[b"TBranch"] = TBranch

class TLeaf(uproot.core.TNamed):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        uproot.core.TNamed.__init__(self, filewalker, walker)

        self.len, self.etype, self.offset, self.hasrange, self.unsigned = walker.readfields("!iii??")
        self.count = uproot.rootio.Deserialized.deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

        if self.len == 0:
            self.len = 1

    def __repr__(self):
        return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, repr(self.name), id(self))

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
        start = walker.index
        vers, bcnt = walker.readversion()

        TLeaf.__init__(self, filewalker, walker)

        self.min, self.max = walker.readfields("{1}")
        self.dtype = numpy.dtype("{2}")

        self._checkbytecount(walker.index - start, bcnt)

uproot.rootio.Deserialized.classes[b"{0}"] = {0}
""".format(classname, format, dtype), globals())
