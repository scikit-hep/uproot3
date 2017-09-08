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

    def copy(self, index=None, skip=None):
        if index is None:
            index = self.index
        out = Walker(self.data, index)
        if skip is not None:
            out.skip(skip)
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

    kByteCountMask  = numpy.int64(0x40000000)
    kByteCountVMask = numpy.int64(0x4000)
    kIsOnHeap       = numpy.uint32(0x01000000)
    kIsReferenced   = numpy.uint32(1 << 4)

    def readversion(self):
        bcnt, vers = self.readfields("!IH")
        bcnt = int(numpy.int64(bcnt) & ~self.kByteCountMask)
        if bcnt == 0:
            raise IOError("readversion byte count is zero")
        return vers, bcnt

    # def readversion(file, index):
    #     bcnt, vers = fields(file, index, "!IH")
    #     index = step(index, "!IH")
    #     bcnt = int(numpy.int64(bcnt) & ~self.kByteCountMask)
    #     if bcnt == 0:
    #         raise IOError("readversion byte count is zero")
    #     return index, (vers, bcnt)

    def skipversion(self):
        version = self.readfield("!h")
        if numpy.int64(version) & self.kByteCountVMask:
            self.skip("!hh")
        
    # def skipversion(file, index):
    #     version = field(file, index, "!h")
    #     index = step(index, "!h")
    #     if numpy.int64(version) & self.kByteCountVMask:
    #         index = step(index, "!hh")
    #     return index

    def skiptobject(self):
        id, bits = self.readfields("!II")
        bits = numpy.uint32(bits) | self.kIsOnHeap
        if bits & self.kIsReferenced:
            self.skip("!H")

    # def skiptobject(file, index):
    #     id, bits = fields(file, index, "!II")
    #     index = step(index, "!II")
    #     bits = numpy.uint32(bits) | self.kIsOnHeap
    #     if bits & skiptobject.kIsReferenced:
    #         index = step(index, "!H")
    #     return index

# def step(index, format):
#     return index + struct.calcsize(format)

# def stepstring(file, index, length=None):
#     if length is None:
#         length = file[index]
#         index += 1
#         if length == 255:
#             length = file[index : index + 4].view(numpy.uint32)
#             index += 4
#     return index + length

# def string(file, index, length=None):
#     if length is None:
#         length = file[index]
#         index += 1
#         if length == 255:
#             length = file[index : index + 4].view(numpy.uint32)
#             index += 4
#     return file[index : index + length].tostring()

# def field(file, index, format):
#     return struct.unpack(format, file[index : index + struct.calcsize(format)])[0]

# def fields(file, index, format):
#     return struct.unpack(format, file[index : index + struct.calcsize(format)])

# def databytes(file, index, dtype, bytes):
#     return file[index : index + bytes].view(dtype)

# def dataitems(file, index, dtype, items):
#     if not isinstance(dtype, numpy.dtype):
#         dtype = numpy.dtype(dtype)
#     return file[index : index + dtype.itemsize * items].view(dtype)

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

        # if field(self.file, index, "!4s") != "root":
        #     raise IOError("not a ROOT file (wrong magic bytes)")
        # index = step(index, "!4s")

        # self.version, self.begin = fields(self.file, index, "!ii")
        # index = step(index, "!ii")

        # if self.version < 1000000:  # small file
        #     self.end, self.seekfree, self.nbytesfree, self.nfree, self.nbytesname, self.units, self.compression, self.seekinfo, self.nbytesinfo = fields(self.file, index, "!iiiiiBiii")
        #     index = step(index, "!iiiiiBiii")
        # else:
        #     self.end, self.seekfree, self.nbytesfree, self.nfree, self.nbytesname, self.units, self.compression, self.seekinfo, self.nbytesinfo = fields(self.file, index, "!qqiiiBiqi")
        #     index = step(index, "!qqiiiBiqi")
        # self.version %= 1000000

        # self.uuid = field(self.file, index, "!18s")
        # index = step(index, "!18s")

        # recordSize = 2 + 4 + 4 + 4 + 4   # fVersion, ctime, mtime, nbyteskeys, nbytesname
        # if self.version >= 40000:
        #     recordSize += 8 + 8 + 8      # seekdir, seekparent, seekkeys
        # else:
        #     recordSize += 4 + 4 + 4      # seekdir, seekparent, seekkeys

        # nbytes = self.nbytesname + recordSize

        # if nbytes + self.begin > self.end:
        #     raise IOError("TDirectory header length")

        # self.dir = TDirectory(self.file, self.begin, self.nbytesname)

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




        # index = begin + nbytesname

        # self.version, self.ctime, self.mtime = fields(self.file, index, "!hII")
        # index = step(index, "!hII")

        # self.nbyteskeys, self.nbytesname = fields(self.file, index, "!ii")
        # index = step(index, "!ii")

        # if self.version <= 1000:
        #     self.seekdir, self.seekparent, self.seekkeys = fields(self.file, index, "!iii")
        # else:
        #     self.seekdir, self.seekparent, self.seekkeys = fields(self.file, index, "!qqq")

        # nk = 4
        # keyversion = field(self.file, begin + nk, "!h")
        # if keyversion > 1000:
        #     nk += 2 + 2*4 + 2*2 + 2*8  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory
        # else:
        #     nk += 2 + 2*4 + 2*2 + 2*4  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory

        # index = begin + nk
        # self.classname = string(self.file, index)
        # index = stepstring(self.file, index)
        # self.name = string(self.file, index)
        # index = stepstring(self.file, index)
        # self.title = string(self.file, index)
        # index = stepstring(self.file, index)

        # if not 10 <= self.nbytesname <= 1000:
        #     raise IOError("directory info")

        # self.keys = TKeys(self.file, self.seekkeys)

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

        print "nkeys", nkeys

        self.keys = [TKey(walkerkeys) for i in range(nkeys)]

        # self.file = file
        # self.header = TKey(self.file, index)

        # index += self.header.keylen
        # nkeys = field(self.file, index, "!i")
        # index = step(index, "!i")

        # self.keys = []
        # for i in range(nkeys):
        #     self.keys.append(TKey(self.file, index))
        #     index = self.keys[-1]._index

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
    classes = {}

    def __init__(self, walker):
        self.bytes, version, self.objlen, datetime, self.keylen, cycle = walker.readfields("!ihiIhh")

        if version > 1000:
            self.seekkey, seekpdir = walker.readfields("!qq")
        else:
            self.seekkey, seekpdir = walker.readfields("!ii")

        self.classname = walker.readstring()
        self.name = walker.readstring()
        self.title = walker.readstring()

        print "KEY", self.classname, self.name, self.title

        self.walker = walker.copy(index=self.seekkey + self.keylen)

        # self.file = file

        # self.bytes, self.version, self.objlen, self.datetime, self.keylen, self.cycle = fields(self.file, index, "!ihiIhh")
        # index = step(index, "!ihiIhh")

        # if self.version > 1000:
        #     self.seekkey, self.seekpdir = fields(self.file, index, "!qq")
        #     index = step(index, "!qq")
        # else:
        #     self.seekkey, self.seekpdir = fields(self.file, index, "!ii")
        #     index = step(index, "!ii")

        # self.classname = string(self.file, index)
        # index = stepstring(self.file, index)
        # self.name = string(self.file, index)
        # index = stepstring(self.file, index)
        # self.title = string(self.file, index)
        # self._index = stepstring(self.file, index)

    def __repr__(self):
        return "<TKey {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    @property
    def isCompressed(self):
        return self.objlen != self.bytes - self.keylen

    def get(self):
        if self.classname not in self.classes:
            raise NotImplementedError("class not recognized: {0}".format(self.classname))

        if self.isCompressed:
            raise NotImplementedError

        return self.classes[self.classname](self.walker)

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
        print self.entries, self.totbytes, self.zipbytes

        # self.file = file

        # ttree_start = index
        # index, (ttree_vers, ttree_bcnt) = readversion(self.file, index)

        # # START TNamed
        # tnamed_start = index
        # index, (tnamed_vers, tnamed_bcnt) = readversion(self.file, index)

        # index = skipversion(self.file, index)
        # index = skiptobject(self.file, index)

        # self.name = string(self.file, index)
        # index = stepstring(self.file, index)
        # self.title = string(self.file, index)
        # index = stepstring(self.file, index)

        # if index - tnamed_start != tnamed_bcnt + 4:
        #     raise IOError("TNamed byte count")
        # # END TNamed

        # # START TAttLine
        # tattline_start = index
        # index, (tattline_vers, tattline_bcnt) = readversion(self.file, index)
        # index = step(index, "!hhh")  # color, style, width
        # if index - tattline_start != tattline_bcnt + 4:
        #     raise IOError("TAttLine byte count")
        # # END TAttLine

        # # START TAttFill
        # tattfill_start = index
        # index, (tattfill_vers, tattfill_bcnt) = readversion(self.file, index)
        # index = step(index, "!hh")  # color, style
        # if index - tattfill_start != tattfill_bcnt + 4:
        #     raise IOError("TAttFill byte count")
        # # END TAttFill

        # # START TAttMarker
        # tattmarker_start = index
        # index, (tattmarker_vers, tattmarker_bcnt) = readversion(self.file, index)
        # index = step(index, "!hhf")  # color, style, width
        # if index - tattmarker_start != tattmarker_bcnt + 4:
        #     raise IOError("TAttMarker byte count")
        # # END TAttMarker

        # self.entries, self.totbytes, self.zipbytes = fields(self.file, index, "!qqq")
        # index = step(index, "!qqq")

        # if ttree_vers < 16:
        #     raise NotImplementedError("TTree too old")

        # if ttree_vers >= 19:
        #     index = step(index, "!q")  # fSavedBytes

        # if ttree_vers >= 18:
        #     index = step(index, "!q")  # flushed bytes

        # index = step(index, "!diii")   # fWeight, fTimerInterval, fScanField, fUpdate

        # if ttree_vers >= 18:
        #     index = step(index, "!i")  # fDefaultEntryOffsetLen

        # nclus = 0
        # if ttree_vers >= 19:
        #     nclus = field(self.file, index, "!i")
        #     index = step(index, "!i")  # fNClusterRange

        # index = step(index, "!qqqq")   # fMaxEntries, fMaxEntryLoop, fMaxVirtualSize, fAutoSave

        # if ttree_vers >= 18:
        #     index = step(index, "!q")  # fAutoFlush

        # index = step(index, "!q")      # fEstimate

        # if ttree_vers >= 19:  # "FIXME" in go-hep
        #     index = step(index, "!b{0}qb{0}b".format(nclus))  # ?, fClusterRangeEnd, ?, fClusterSize

        # print "TObjArray", readversion(self.file, index)




TKey.classes["TTree"] = TTree

file = TFile("/home/pivarski/storage/data/TrackResonanceNtuple_uncompressed.root")
print file.get("twoMuon")
