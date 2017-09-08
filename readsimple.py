#!/usr/bin/env python

import struct

import numpy

class Walker(object):
    @staticmethod
    def memmap(filepath, index=0):
        return Walker(numpy.memmap(filepath, dtype=numpy.uint8, mode="r"), index)

    def __init__(self, data, index=0):
        self.data = data
        self.index = index
        self.refs = {}

    def copy(self, index=None, skip=None):
        if index is None:
            index = self.index
        out = Walker(self.data, index)
        if skip is not None:
            out.skip(skip)
        out.refs = self.refs    # refs are shared among all Walkers that operate on a given file
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
        self.filepath = filepath
        walker = Walker.memmap(self.filepath)

        if walker.readfield("!4s") != "root":
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
        return "<TFile {0} at 0x{1:012x}>".format(repr(self.filepath), id(self))

    def get(self, name):
        self.dir.get(name)

class TDirectory(object):
    def __init__(self, walker, walkerhead):
        version, ctime, mtime = walkerhead.readfields("!hII")
        nbyteskeys, nbytesname = walkerhead.readfields("!ii")

        if version <= 1000:
            seekdir, seekparent, seekkeys = walkerhead.readfields("!iii")
        else:
            seekdir, seekparent, seekkeys = walkerhead.readfields("!qqq")

        nk = 4
        walker.skip(nk)
        keyversion = walker.field("!h")
        if keyversion > 1000:
            nk += 2 + 2*4 + 2*2 + 2*8  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory
        else:
            nk += 2 + 2*4 + 2*2 + 2*4  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory

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
        self.keys.get(name)

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

    def get(self, name):
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
        self.walker = walker.copy(index=self.seekkey + self.keylen)

    def __repr__(self):
        return "<TKey {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    @property
    def isCompressed(self):
        return self.objlen != self.bytes - self.keylen

    def get(self):
        if self.classname not in Deserialized.classes:
            raise NotImplementedError("class not recognized: {0}".format(self.classname))

        if self.isCompressed:
            raise NotImplementedError

        return Deserialized.classes[self.classname](self.walker)

class Deserialized(object):
    classes = {}

    def __init__(self, *args, **kwds):
        raise TypeError("Deserialized is an abstract class")

    @staticmethod
    def deserialize(walker):
        beg = walker.index
        bcnt = walker.readfield("!I")

        if numpy.int64(bcnt) & Walker.kByteCountMask == 0 or numpy.int64(bcnt) == Walker.kNewClassTag:
            vers = 0
            start = 0
            tag = bcnt
            bcnt = 0
        else:
            vers = 1
            start = walker.index
            tag = walker.readfield("!I")

        if numpy.int64(tag) & Walker.kClassMask == 0:
            if tag == 0:
                return None

            elif tag == 1:
                raise NotImplementedError("tag == 1 means self; not implemented yet")

            elif tag not in walker.refs:
                walker.index = beg + bcnt + 4
                return None

            else:
                return walker.refs[tag]
            
        elif tag == Walker.kNewClassTag:
            cname = walker.readcstring()
            if cname not in Deserialized.classes:
                raise NotImplementedError("class not recognized: {0}".format(cname))

            fct = Deserialized.classes[cname]

            if vers > 0:
                walker.refs[start + Walker.kMapOffset] = fct
            else:
                walker.refs[len(walker.refs) + 1] = fct

            obj = fct(walker)

            if vers > 0:
                walker.refs[beg + Walker.kMapOffset] = obj
            else:
                walker.refs[len(walker.refs) + 1] = obj

            return obj

        else:
            print "deserialize, default"

            raise NotImplementedError("FIXME")

class TObjArray(Deserialized):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        if vers >= 3:
            # TObject
            walker.skipversion()
            walker.skiptobject()

        if vers >= 2:
            # not a TObject
            self.name = walker.readstring()

        nobjs, low = walker.readfields("!ii")

        self.items = [Deserialized.deserialize(walker) for i in range(nobjs)]

        if walker.index - start != bcnt + 4:
            raise IOError("TObjArray byte count")

    def __repr__(self):
        return "<TObjArray len={0} at 0x{1:012x}>".format(len(self.items), id(self))

    def __getitem__(self, i):
        return self.items[i]

    def __len__(self):
        return len(self.items)

Deserialized.classes["TObjArray"] = TObjArray

class TNamed(Deserialized):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skipversion()
        walker.skiptobject()

        self.name = walker.readstring()
        self.title = walker.readstring()

        if walker.index - start != bcnt + 4:
            raise IOError("TNamed byte count")

class TAttLine(Deserialized):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hhh")  # color, style, width
        if walker.index - start != bcnt + 4:
            raise IOError("TAttLine byte count")

class TAttFill(Deserialized):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hh")  # color, style
        if walker.index - start != bcnt + 4:
            raise IOError("TAttFill byte count")

class TAttMarker(Deserialized):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hhf")  # color, style, width
        if walker.index - start != bcnt + 4:
            raise IOError("TAttMarker byte count")

class TTree(TNamed, TAttLine, TAttFill, TAttMarker):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        TNamed.__init__(self, walker)
        TAttLine.__init__(self, walker)
        TAttFill.__init__(self, walker)
        TAttMarker.__init__(self, walker)

        self.entries, self.totbytes, self.zipbytes = walker.readfields("!qqq")
        print "entries, tot, zip", self.entries, self.totbytes, self.zipbytes

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

        if vers >= 19:  # "FIXME" in go-hep
            walker.skip("!b{0}qb{0}b".format(nclus))  # ?, fClusterRangeEnd, ?, fClusterSize

        tmp = TObjArray(walker)
        # HERE

    def __repr__(self):
        return "<TTree {0} len={0} at 0x{1:012x}>".format(repr(self.name), len(self.entries), id(self))

Deserialized.classes["TTree"] = TTree

class TBranch(TNamed, TAttFill):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        if vers < 12:
            raise NotImplementedError("TBranch version too old")

        TNamed.__init__(self, walker)
        TAttFill.__init__(self, walker)

	self.compress, self.basketSize, self.entryOffsetLen, self.writeBasket, self.entryNumber, self.offset, self.maxBaskets, self.splitLevel, self.entries, self.firstEntry, self.totBytes, self.zipBytes = walker.readfields("!iiiiqiiiqqqq")

        self.branches = TObjArray(walker)
        self.leaves = TObjArray(walker)
        self.baskets = TObjArray(walker)

        walker.skip(1)  # isArray
        self.basketBytes = walker.readarray(">i4", self.maxBaskets)  # FIXME: might need slicing

        walker.skip(1)  # isArray
        self.basketEntry = walker.readarray(">i8", self.maxBaskets)  # FIXME: might need slicing

        walker.skip(1)  # isArray
        self.basketSeek = walker.readarray(">i8", self.maxBaskets)  # FIXME: might need slicing

        self.fname = walker.readstring()

        if walker.index - start != bcnt + 4:
            raise IOError("TBranch byte count")

        if self.splitLevel == 0 and len(self.branches) > 0:
            self.splitLevel = 1

    def __repr__(self):
        return "<TBranch {0} at 0x{1:012x}>".format(repr(self.name), id(self))

Deserialized.classes["TBranch"] = TBranch

class TLeaf(TNamed):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        TNamed.__init__(self, walker)

        self.len, self.etype, self.offset, self.hasrange, self.unsigned = walker.readfields("!iii??")
        self.count = Deserialized.deserialize(walker)

        if walker.index - start != bcnt + 4:
            raise IOError("TLeaf byte count")

        if self.len == 0:
            self.len = 1

    def __repr__(self):
        return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, repr(self.name), id(self))

Deserialized.classes["TLeaf"] = TLeaf

class TLeafF(TLeaf):
    def __init__(self, walker):
        start = walker.index
        vers, bcnt = walker.readversion()

        TLeaf.__init__(self, walker)

        self.min, self.max = walker.readfields("!ff")

        if walker.index - start != bcnt + 4:
            raise IOError("TLeafF byte count")

Deserialized.classes["TLeafF"] = TLeafF

file = TFile("/home/pivarski/storage/data/TrackResonanceNtuple_uncompressed.root")
print file.get("twoMuon")
