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

    def items(self, dtype, length, index=None, read=False):
        if index is None:
            index = self.index
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        start = index
        end = index + length
        if read:
            self.index = end
        return self.data[start:end].view(dtype)

    def readitems(self, dtype, length, index=None):
        return self.items(dtype, length, index, True)

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
            raise NotImplementedError("FIXME")

        elif tag == Walker.kNewClassTag:
            cname = walker.readcstring()

            print "cname", cname

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
            raise NotImplementedError("FIXME")

class TObjArray(object):
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

Deserialized.classes["TObjArray"] = TObjArray

class TTree(object):
    def __init__(self, walker):
        ttree_start = walker.index
        ttree_vers, ttree_bcnt = walker.readversion()

        # START TNamed
        tnamed_start = walker.index
        tnamed_vers, tnamed_bcnt = walker.readversion()
        walker.skipversion()
        walker.skiptobject()

        self.name = walker.readstring()
        self.title = walker.readstring()

        if walker.index - tnamed_start != tnamed_bcnt + 4:
            raise IOError("TNamed byte count")
        # END TNamed

        # START TAttLine
        tattline_start = walker.index
        tattline_vers, tattline_bcnt = walker.readversion()
        walker.skip("!hhh")  # color, style, width
        if walker.index - tattline_start != tattline_bcnt + 4:
            raise IOError("TAttLine byte count")
        # END TAttLine

        # START TAttFill
        tattfill_start = walker.index
        tattfill_vers, tattfill_bcnt = walker.readversion()
        walker.skip("!hh")  # color, style
        if walker.index - tattfill_start != tattfill_bcnt + 4:
            raise IOError("TAttFill byte count")
        # END TAttFill

        # START TAttMarker
        tattmarker_start = walker.index
        tattmarker_vers, tattmarker_bcnt = walker.readversion()
        walker.skip("!hhf")  # color, style, width
        if walker.index - tattmarker_start != tattmarker_bcnt + 4:
            raise IOError("TAttMarker byte count")
        # END TAttMarker

        self.entries, self.totbytes, self.zipbytes = walker.readfields("!qqq")
        print "entries, tot, zip", self.entries, self.totbytes, self.zipbytes

        if ttree_vers < 16:
            raise NotImplementedError("TTree too old")

        if ttree_vers >= 19:
            walker.skip("!q")  # fSavedBytes

        if ttree_vers >= 18:
            walker.skip("!q")  # flushed bytes

        walker.skip("!diii")   # fWeight, fTimerInterval, fScanField, fUpdate

        if ttree_vers >= 18:
            walker.skip("!i")  # fDefaultEntryOffsetLen

        nclus = 0
        if ttree_vers >= 19:
            nclus = walker.readfield("!i")  # fNClusterRange

        walker.skip("!qqqq")   # fMaxEntries, fMaxEntryLoop, fMaxVirtualSize, fAutoSave

        if ttree_vers >= 18:
            walker.skip("!q")  # fAutoFlush

        walker.skip("!q")      # fEstimate

        if ttree_vers >= 19:  # "FIXME" in go-hep
            walker.skip("!b{0}qb{0}b".format(nclus))  # ?, fClusterRangeEnd, ?, fClusterSize

        tmp = TObjArray(walker)
        # HERE

Deserialized.classes["TTree"] = TTree

class TBranch(object):
    def __init__(self, walker):
        beg = walker.index

        vers, bcnt = walker.readversion()

        print "TBranch", vers, bcnt



Deserialized.classes["TBranch"] = TBranch



file = TFile("/home/pivarski/storage/data/TrackResonanceNtuple_uncompressed.root")
print file.get("twoMuon")
