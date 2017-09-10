#!/usr/bin/env python

import struct
import zlib

import numpy

class Walker(object):
    @staticmethod
    def memmap(filepath, index=0):
        return Walker(numpy.memmap(filepath, dtype=numpy.uint8, mode="r"), index)

    def __init__(self, data, index=0, origin=None):
        self.data = data
        self.index = index
        self.refs = {}
        if origin is not None:
            self.origin = origin

    def copy(self, index=None, skip=None, origin=None):
        if index is None:
            index = self.index
        out = Walker(self.data, index)
        if skip is not None:
            out.skip(skip)
        out.refs = self.refs   # refs are shared among all Walkers that operate on a given file
        if origin is not None:
            out.origin = origin
        return out

    def skip(self, format):
        if isinstance(format, int):
            self.index += format
        else:
            self.index += struct.calcsize(format)

    def fields(self, format, index=None, read=False):
        if index is None:
            index = self.index
        start = index
        end = index + struct.calcsize(format)
        if read:
            self.index = end
        return struct.unpack(format, self.data[start:end])

    def readfields(self, format, index=None):
        return self.fields(format, index, True)

    def field(self, format, index=None, read=False):
        out, = self.fields(format, index, read)
        return out

    def readfield(self, format, index=None):
        out, = self.fields(format, index, True)
        return out

    def bytes(self, length, index=None, read=False):
        if index is None:
            index = self.index
        start = index
        end = index + length
        if read:
            self.index = end
        return self.data[start:end]

    def readbytes(self, length, index=None):
        return self.bytes(length, index, True)

    def array(self, dtype, length, index=None, read=False):
        if index is None:
            index = self.index
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        start = index
        end = index + length * dtype.itemsize
        if read:
            self.index = end
        return self.data[start:end].view(dtype)

    def readarray(self, dtype, length, index=None):
        return self.array(dtype, length, index, True)

    def string(self, index=None, length=None, read=False):
        if index is None:
            index = self.index
        if length is None:
            length = self.data[index]
            index += 1
            if length == 255:
                length = self.data[index : index + 4].view(numpy.uint32)
                index += 4
        end = index + length
        if read:
            self.index = end
        return self.data[index : end].tostring()

    def readstring(self, index=None, length=None):
        return self.string(index, length, True)

    def cstring(self, index=None, read=False):
        if index is None:
            index = self.index
        start = index
        end = index
        while self.data[end] != 0:
            end += 1
        if read:
            self.index = end + 1
        return self.data[start:end].tostring()

    def readcstring(self, index=None):
        return self.cstring(index, True)

    kByteCountMask  = numpy.int64(0x40000000)
    kByteCountVMask = numpy.int64(0x4000)
    kClassMask      = numpy.int64(0x80000000)
    kNewClassTag    = numpy.int64(0xFFFFFFFF)

    kIsOnHeap       = numpy.uint32(0x01000000)
    kIsReferenced   = numpy.uint32(1 << 4)

    kMapOffset      = 2

    def readversion(self):
        bcnt, vers = self.readfields("!IH")
        bcnt = int(numpy.int64(bcnt) & ~self.kByteCountMask)
        if bcnt == 0:
            raise IOError("readversion byte count is zero")
        return vers, bcnt

    def skipversion(self):
        version = self.readfield("!h")
        if numpy.int64(version) & self.kByteCountVMask:
            self.skip("!hh")

    def skiptobject(self):
        id, bits = self.readfields("!II")
        bits = numpy.uint32(bits) | self.kIsOnHeap
        if bits & self.kIsReferenced:
            self.skip("!H")

class TFile(object):
    def __init__(self, filepath):
        walker = Walker.memmap(filepath)

        if walker.readfield("!4s") != b"root":
            raise IOError("not a ROOT file (wrong magic bytes)")

        version, begin = walker.readfields("!ii")

        if version < 1000000:  # small file
            end, seekfree, nbytesfree, nfree, nbytesname, units, self.compression, seekinfo, nbytesinfo = walker.readfields("!iiiiiBiii")
        else:                  # big file
            end, seekfree, nbytesfree, nfree, nbytesname, units, self.compression, seekinfo, nbytesinfo = walker.readfields("!qqiiiBiqi")
        version %= 1000000

        uuid = walker.readfield("!18s")

        recordSize = 2 + 4 + 4 + 4 + 4   # fVersion, ctime, mtime, nbyteskeys, nbytesname
        if version >= 40000:
            recordSize += 8 + 8 + 8      # seekdir, seekparent, seekkeys
        else:
            recordSize += 4 + 4 + 4      # seekdir, seekparent, seekkeys

        nbytes = nbytesname + recordSize

        if nbytes + begin > end:
            raise IOError("TDirectory header length")

        self.dir = TDirectory(walker.copy(index=begin), walker.copy(index=begin + nbytesname))

    def __repr__(self):
        return "<TFile {0} at 0x{1:012x}>".format(repr(self.dir.name), id(self))

    def get(self, name):
        return self.dir.get(name)

class TDirectory(object):
    def __init__(self, walker, walkerhead):
        version, ctime, mtime = walkerhead.readfields("!hII")
        nbyteskeys, nbytesname = walkerhead.readfields("!ii")

        if version <= 1000:
            seekdir, seekparent, seekkeys = walkerhead.readfields("!iii")
        else:
            seekdir, seekparent, seekkeys = walkerhead.readfields("!qqq")

        walker.skip(4)
        keyversion = walker.field("!h")
        if keyversion > 1000:
            nk_minus_4 = 2 + 2*4 + 2*2 + 2*8  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory
        else:
            nk_minus_4 = 2 + 2*4 + 2*2 + 2*4  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory

        walker.skip(nk_minus_4)

        classname = walker.readstring()
        self.name = walker.readstring()
        self.title = walker.readstring()

        if not 10 <= nbytesname <= 1000:
            raise IOError("directory info")

        self.keys = TKeys(walker.copy(index=seekkeys))

    def __repr__(self):
        return "<TDirectory {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def get(self, name):
        # FIXME: parse slashes and get subdirectories
        return self.keys.get(name)

class TKeys(object):
    def __init__(self, walker):
        walkerkeys = walker.copy()
        self.header = TKey(walker)
        walkerkeys.skip(self.header.keylen)
        nkeys = walkerkeys.readfield("!i")
        self.keys = [TKey(walkerkeys) for i in range(nkeys)]

    def __repr__(self):
        return "<TKeys len={0} at 0x{1:012x}>".format(len(self.keys), id(self))

    def __getitem__(self, i):
        return self.keys[i]

    def __len__(self):
        return len(self.keys)

    def __iter__(self):
        return iter(self.keys)

    def get(self, name):
        if isinstance(name, str):
            name = name.encode("ascii")
        for key in self.keys:
            if key.name == name:
                return key.get()
        raise KeyError("not found: {0}".format(repr(name)))

class TKey(object):
    def __init__(self, walker):
        self.bytes, version, self.objlen, datetime, self.keylen, cycle = walker.readfields("!ihiIhh")

        if version > 1000:
            self.seekkey, seekpdir = walker.readfields("!qq")
        else:
            self.seekkey, seekpdir = walker.readfields("!ii")

        self.classname = walker.readstring()
        self.name = walker.readstring()
        self.title = walker.readstring()

        self.filewalker = walker

        #  object size != compressed size means it's compressed
        if self.objlen != self.bytes - self.keylen:
            inflated = zlib.decompress(walker.bytes(self.bytes - self.keylen, index=self.seekkey + self.keylen + 9))
            self.walker = Walker(numpy.frombuffer(inflated, dtype=numpy.uint8), 0, origin=-self.keylen)

        # otherwise, it's uncompressed
        else:
            self.walker = walker.copy(index=self.seekkey + self.keylen, origin=self.seekkey)

    def __repr__(self):
        return "<TKey {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def get(self):
        if self.classname not in Deserialized.classes:
            raise NotImplementedError("class not recognized: {0}".format(self.classname))
        return Deserialized.classes[self.classname](self.filewalker, self.walker)

class Deserialized(object):
    classes = {}

    def __init__(self, *args, **kwds):
        raise TypeError("Deserialized is an abstract class")

    @staticmethod
    def deserialize(filewalker, walker):
        beg = walker.index - walker.origin
        bcnt = walker.readfield("!I")

        if numpy.int64(bcnt) & Walker.kByteCountMask == 0 or numpy.int64(bcnt) == Walker.kNewClassTag:
            vers = 0
            start = 0
            tag = bcnt
            bcnt = 0
        else:
            vers = 1
            start = walker.index - walker.origin
            tag = walker.readfield("!I")

        if numpy.int64(tag) & Walker.kClassMask == 0:
            # reference object
            if tag == 0:
                return None                # return null

            elif tag == 1:
                raise NotImplementedError("tag == 1 means self; not implemented yet")

            elif tag not in walker.refs:
                # jump past this object
                walker.index = walker.origin + beg + bcnt + 4
                return None                # return null

            else:
                return walker.refs[tag]    # return object
            
        elif tag == Walker.kNewClassTag:
            # new class and object
            cname = walker.readcstring()

            if cname not in Deserialized.classes:
                raise NotImplementedError("class not recognized: {0}".format(cname))

            fct = Deserialized.classes[cname]

            if vers > 0:
                walker.refs[start + Walker.kMapOffset] = fct
            else:
                walker.refs[len(walker.refs) + 1] = fct

            obj = fct(filewalker, walker)

            if vers > 0:
                walker.refs[beg + Walker.kMapOffset] = obj
            else:
                walker.refs[len(walker.refs) + 1] = obj

            return obj                     # return object

        else:
            # reference class, new object
            ref = int(numpy.int64(tag) & ~Walker.kClassMask)

            if ref not in walker.refs:
                raise IOError("invalid class-tag reference")

            fct = walker.refs[ref]         # reference class

            if fct not in Deserialized.classes.values():
                raise IOError("invalid class-tag reference (not a factory)")

            obj = fct(filewalker, walker)  # new object

            if vers > 0:
                walker.refs[beg + Walker.kMapOffset] = obj
            else:
                walker.refs[len(walker.refs) + 1] = obj

            return obj                     # return object

    def _checkbytecount(self, observed, expected):
        if observed != expected + 4:
            raise IOError("{0} byte count".format(self.__class__.__name__))

class TObjArray(Deserialized):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        if vers >= 3:
            # TObjArray is a TObject
            walker.skipversion()
            walker.skiptobject()

        if vers >= 2:
            # TObjArray is a not a TObject
            self.name = walker.readstring()

        nobjs, low = walker.readfields("!ii")

        self.items = [Deserialized.deserialize(filewalker, walker) for i in range(nobjs)]

        self._checkbytecount(walker.index - start, bcnt)

    def __repr__(self):
        return "<TObjArray len={0} at 0x{1:012x}>".format(len(self.items), id(self))

    def __getitem__(self, i):
        return self.items[i]

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

Deserialized.classes[b"TObjArray"] = TObjArray

class TNamed(Deserialized):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skipversion()
        walker.skiptobject()

        self.name = walker.readstring()
        self.title = walker.readstring()

        self._checkbytecount(walker.index - start, bcnt)

class TAttLine(Deserialized):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hhh")  # color, style, width
        self._checkbytecount(walker.index - start, bcnt)

class TAttFill(Deserialized):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hh")  # color, style
        self._checkbytecount(walker.index - start, bcnt)

class TAttMarker(Deserialized):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hhf")  # color, style, width
        self._checkbytecount(walker.index - start, bcnt)

class TTree(TNamed, TAttLine, TAttFill, TAttMarker):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        TNamed.__init__(self, filewalker, walker)
        TAttLine.__init__(self, filewalker, walker)
        TAttFill.__init__(self, filewalker, walker)
        TAttMarker.__init__(self, filewalker, walker)

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

        self.branches = TObjArray(filewalker, walker)
        self.leaves = TObjArray(filewalker, walker)

        for i in range(7):
            # fAliases, fIndexValues, fIndex, fTreeIndex, fFriends, fUserInfo, fBranchRef
            Deserialized.deserialize(filewalker, walker)

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
        
Deserialized.classes[b"TTree"] = TTree

class TBranch(TNamed, TAttFill):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        if vers < 12:
            raise NotImplementedError("TBranch version too old")

        TNamed.__init__(self, filewalker, walker)
        TAttFill.__init__(self, filewalker, walker)

        self.compress, self.basketSize, self.entryOffsetLen, self.writeBasket, self.entryNumber, self.offset, self.maxBaskets, self.splitLevel, self.entries, self.firstEntry, self.totBytes, self.zipBytes = walker.readfields("!iiiiqiiiqqqq")

        self.branches = TObjArray(filewalker, walker)
        self.leaves = TObjArray(filewalker, walker)
        self.baskets = TObjArray(filewalker, walker)

        walker.skip(1)  # isArray
        self.basketBytes = walker.readarray(">i4", self.maxBaskets)[:self.writeBasket]

        walker.skip(1)  # isArray
        self.basketEntry = walker.readarray(">i8", self.maxBaskets)[:self.writeBasket]

        walker.skip(1)  # isArray
        self.basketSeek = walker.readarray(">i8", self.maxBaskets)[:self.writeBasket]

        self.fname = walker.readstring()

        self._checkbytecount(walker.index - start, bcnt)

        if self.splitLevel == 0 and len(self.branches) > 0:
            self.splitLevel = 1

        if len(self.leaves) == 1:
            self.dtype = self.leaves[0].dtype
        self.basketwalkers = [filewalker.copy(x) for x in self.basketSeek]
        self.basketsize = [filewalker.field("!i", index=x + 6) // self.dtype.itemsize for x in self.basketSeek]
        
    def __repr__(self):
        return "<TBranch {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def basket(self, i):
        walker = self.basketwalkers[i]
        bytes, version, objlen, datetime, keylen = walker.fields("!ihiIh")
        return walker.array(self.dtype, self.basketsize[i], index=walker.index + keylen)

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

Deserialized.classes[b"TBranch"] = TBranch

class TLeaf(TNamed):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        TNamed.__init__(self, filewalker, walker)

        self.len, self.etype, self.offset, self.hasrange, self.unsigned = walker.readfields("!iii??")
        self.count = Deserialized.deserialize(filewalker, walker)

        self._checkbytecount(walker.index - start, bcnt)

        if self.len == 0:
            self.len = 1

    def __repr__(self):
        return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, repr(self.name), id(self))

Deserialized.classes[b"TLeaf"] = TLeaf

for classname, format, dtype in [("TLeafF", "!ff", ">f4")]:
    exec("""
class {0}(TLeaf):
    def __init__(self, filewalker, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        TLeaf.__init__(self, filewalker, walker)

        self.min, self.max = walker.readfields("{1}")
        self.dtype = numpy.dtype("{2}")

        self._checkbytecount(walker.index - start, bcnt)

Deserialized.classes[b"{0}"] = {0}
""".format(classname, format, dtype), globals())

file = TFile("/home/pivarski/storage/data/TrackResonanceNtuple_compressed.root")
tree = file.get("twoMuon")

print(tree.branch("mass_mumu").array())
print(tree.branch("px").array())
print(tree.branch("py").array())
print(tree.branch("pz").array())

# 20 ms to load a tree, 60 ms to get the data (uncompressed)
# ROOT takes 88 ms to load a tree, 220 ms to get the data
