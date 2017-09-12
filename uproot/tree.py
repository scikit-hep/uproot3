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

import uproot.walker.arraywalker
import uproot.walker.lazyarraywalker
import uproot.rootio
import uproot.core

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

            if isinstance(branch, TBranchElement):
                try:
                    return branch.branch(name)
                except KeyError:
                    pass

        raise KeyError("not found: {0}".format(repr(name)))
        
uproot.rootio.Deserialized.classes[b"TTree"] = TTree

class TBranch(uproot.core.TNamed,
              uproot.core.TAttFill):
    def __init__(self, filewalker, walker):
        walker.startcontext()
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
        baskets = uproot.core.TObjArray(filewalker, walker)

        walker.skip(1)  # isArray
        # self.basketBytes = walker.readarray(">i4", maxBaskets)[:writeBasket]
        walker.skip(4 * maxBaskets)

        walker.skip(1)  # isArray
        # self.basketEntry = walker.readarray(">i8", maxBaskets)[:writeBasket]
        walker.skip(8 * maxBaskets)

        walker.skip(1)  # isArray
        self.basketSeek = walker.readarray(">i8", maxBaskets)[:writeBasket]

        fname = walker.readstring()

        self._checkbytecount(walker.index - start, bcnt)

        if len(self.leaves) == 1 and hasattr(self.leaves[0], "dtype"):
            self.dtype = self.leaves[0].dtype
        self.filewalker = filewalker

    def _preparebaskets(self):
        self.filewalker.startcontext()

        self.basketobjlens = []
        self.basketkeylens = []
        self.basketborders = []
        self.basketwalkers = []
        for seek in self.basketSeek:
            basketwalker = self.filewalker.copy(seek)
            basketwalker.startcontext()

            bytes, version, objlen, datetime, keylen, cycle = basketwalker.readfields("!ihiIhh")
            if version > 1000:
                seekkey, seekpdir = basketwalker.readfields("!qq")
            else:
                seekkey, seekpdir = basketwalker.readfields("!ii")

            self.basketobjlens.append(objlen)
            self.basketkeylens.append(keylen)

            classname = basketwalker.readstring()
            name = basketwalker.readstring()
            title = basketwalker.readstring()
            vers, bufsize, nevsize, nevbuf, last, flag = basketwalker.readfields("!HiiiiB")
            border = last - keylen

            self.basketborders.append(border)

            #  object size != compressed size means it's compressed
            if objlen != bytes - keylen:
                function = uproot.rootio.decompressfcn(self.compression, objlen)
                self.basketwalkers.append(uproot.walker.lazyarraywalker.LazyArrayWalker(self.filewalker, function, bytes - keylen, seekkey + keylen, newfile=True))

            # otherwise, it's uncompressed
            else:
                self.basketwalkers.append(self.filewalker.copy(seek + keylen, newfile=True))

    def basket(self, i, offsets=False):
        if not hasattr(self, "basketwalkers"):
            self._preparebaskets()

        self.basketwalkers[i].startcontext()
        array = self.basketwalkers[i].readarray(self.dtype, self.basketobjlens[i] // self.dtype.itemsize)
        self.basketwalkers[i]._unevaluate()

        if offsets:
            outdata = array[:self.basketborders[i] // self.dtype.itemsize]
            outoff = array.view(numpy.uint8)[self.basketborders[i] + 4 : -4].view(">i4") - self.basketkeylens[i]
            return outdata, outoff
        else:
            return array[:self.basketborders[i] // self.dtype.itemsize]

    def array(self, dtype=None):
        if not hasattr(self, "basketwalkers"):
            self._preparebaskets()

        if dtype is None:
            dtype = self.dtype

        out = numpy.empty(sum(self.basketborders) // self.dtype.itemsize, dtype=dtype)

        start = 0
        for i in range(len(self.basketwalkers)):
            end = start + self.basketborders[i] // self.dtype.itemsize
            out[start:end] = self.basket(i)
            start = end

        return out

    def strings(self):
        if not hasattr(self, "basketwalkers"):
            self._preparebaskets()

        for i in range(len(self.basketwalkers)):
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
        self.parent = walker.readstring()
        self.clones = walker.readstring()

        checksum = walker.readfield("!I")
        if vers >= 10:
            classversion = walker.readfield("!H")
        else:
            classversion = walker.readfield("!I")
        identifier, btype, stype, self.max = walker.readfields("!iiii")
            
        bcount1 = uproot.rootio.Deserialized.deserialize(filewalker, walker)
        bcount2 = uproot.rootio.Deserialized.deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

    def basket(self, i, offsets=False):
        if hasattr(self, "dtype"):
            return TBranch.basket(self, i, offsets)
        else:
            raise NotImplementedError

    def array(self, dtype=None):
        if hasattr(self, "dtype"):
            return TBranch.array(self, dtype)
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

        self.len, self.etype, self.offset, self.hasrange, self.unsigned = walker.readfields("!iii??")
        self.count = uproot.rootio.Deserialized.deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

        if self.len == 0:
            self.len = 1

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
