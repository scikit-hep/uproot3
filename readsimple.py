#!/usr/bin/env python

import struct

import numpy

def step(index, format):
    return index + struct.calcsize(format)

def stepstring(file, index, length=None):
    if length is None:
        length = file[index]
        index += 1
        if length == 255:
            length = file[index : index + 4].view(numpy.uint32)
            index += 4
    return index + length

def string(file, index, length=None):
    if length is None:
        length = file[index]
        index += 1
        if length == 255:
            length = file[index : index + 4].view(numpy.uint32)
            index += 4
    return file[index : index + length].tostring()

def field(file, index, format):
    return struct.unpack(format, file[index : index + struct.calcsize(format)])[0]

def fields(file, index, format):
    return struct.unpack(format, file[index : index + struct.calcsize(format)])

def databytes(file, index, dtype, bytes):
    return file[index : index + bytes].view(dtype)

def dataitems(file, index, dtype, items):
    if not isinstance(dtype, numpy.dtype):
        dtype = numpy.dtype(dtype)
    return file[index : index + dtype.itemsize * items].view(dtype)

class TFile(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.file = numpy.memmap(self.filepath, mode="r")

        index = 0

        assert field(self.file, index, "!4s") == "root", "magic"
        index = step(index, "!4s")

        self.version, self.begin = fields(self.file, index, "!ii")
        index = step(index, "!ii")

        if self.version < 1000000:  # small file
            self.end, self.seekfree, self.nbytesfree, self.nfree, self.nbytesname, self.units, self.compression, self.seekinfo, self.nbytesinfo = fields(self.file, index, "!iiiiiBiii")
            index = step(index, "!iiiiiBiii")
        else:
            self.end, self.seekfree, self.nbytesfree, self.nfree, self.nbytesname, self.units, self.compression, self.seekinfo, self.nbytesinfo = fields(self.file, index, "!qqiiiBiqi")
            index = step(index, "!qqiiiBiqi")
        self.version %= 1000000

        self.uuid = field(self.file, index, "!18s")
        index = step(index, "!18s")

        recordSize = 2 + 4 + 4 + 4 + 4   # fVersion, ctime, mtime, nbyteskeys, nbytesname
        if self.version >= 40000:
            recordSize += 8 + 8 + 8      # seekdir, seekparent, seekkeys
        else:
            recordSize += 4 + 4 + 4      # seekdir, seekparent, seekkeys

        nbytes = self.nbytesname + recordSize

        assert nbytes + self.begin <= self.end, "dir header length"

        self.dir = TDirectory(self.file, self.begin, self.nbytesname)

    def __repr__(self):
        return "<TFile {0} at 0x{1:012x}>".format(repr(self.filepath), id(self))

    def get(self, name):
        self.dir.get(name)

class TDirectory(object):
    def __init__(self, file, begin, nbytesname):
        self.file = file
        index = begin + nbytesname

        self.version, self.ctime, self.mtime = fields(self.file, index, "!hII")
        index = step(index, "!hII")

        self.nbyteskeys, self.nbytesname = fields(self.file, index, "!ii")
        index = step(index, "!ii")

        if self.version <= 1000:
            self.seekdir, self.seekparent, self.seekkeys = fields(self.file, index, "!iii")
        else:
            self.seekdir, self.seekparent, self.seekkeys = fields(self.file, index, "!qqq")

        nk = 4
        keyversion = field(self.file, begin + nk, "!h")
        if keyversion > 1000:
            nk += 2 + 2*4 + 2*2 + 2*8  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory
        else:
            nk += 2 + 2*4 + 2*2 + 2*4  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory

        index = begin + nk
        self.classname = string(self.file, index)
        index = stepstring(self.file, index)
        self.name = string(self.file, index)
        index = stepstring(self.file, index)
        self.title = string(self.file, index)
        index = stepstring(self.file, index)

        assert 10 <= self.nbytesname <= 1000, "directory info"

        self.keys = TKeys(self.file, self.seekkeys)

    def __repr__(self):
        return "<TDirectory {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def get(self, name):
        # FIXME: parse slashes and get subdirectories
        self.keys.get(name)

class TKeys(object):
    def __init__(self, file, index):
        self.file = file
        self.header = TKey(self.file, index)

        index += self.header.keylen
        nkeys = field(self.file, index, "!i")
        index = step(index, "!i")

        self.keys = []
        for i in range(nkeys):
            self.keys.append(TKey(self.file, index))
            index = self.keys[-1]._index

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

    def __init__(self, file, index):
        self.file = file

        self.bytes, self.version, self.objlen, self.datetime, self.keylen, self.cycle = fields(self.file, index, "!ihiIhh")
        index = step(index, "!ihiIhh")

        if self.version > 1000:
            self.seekkey, self.seekpdir = fields(self.file, index, "!qq")
            index = step(index, "!qq")
        else:
            self.seekkey, self.seekpdir = fields(self.file, index, "!ii")
            index = step(index, "!ii")

        self.classname = string(self.file, index)
        index = stepstring(self.file, index)
        self.name = string(self.file, index)
        index = stepstring(self.file, index)
        self.title = string(self.file, index)
        self._index = stepstring(self.file, index)

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

        start = self.seekkey + self.keylen
        return self.classes[self.classname](self.file, start)

def readversion(file, index):
    bcnt, vers = fields(file, index, "!IH")
    index = step(index, "!IH")
    bcnt = int(numpy.int64(bcnt) & ~readversion.kByteCountMask)
    assert bcnt != 0, "too old file"
    return index, (vers, bcnt)
readversion.kByteCountMask = numpy.int64(0x40000000)

def skipversion(file, index):
    version = field(file, index, "!h")
    index = step(index, "!h")
    if numpy.int64(version) & skipversion.kByteCountVMask:
        index = step(index, "!hh")
    return index
skipversion.kByteCountVMask = numpy.int64(0x4000)

def skiptobject(file, index):
    id, bits = fields(file, index, "!II")
    index = step(index, "!II")
    bits = numpy.uint32(bits) | skiptobject.kIsOnHeap
    if bits & skiptobject.kIsReferenced:
        index = step(index, "H")
    return index
skiptobject.kIsOnHeap = numpy.uint32(0x01000000)
skiptobject.kIsReferenced = numpy.uint32(1 << 4)

class TTree(object):
    def __init__(self, file, index):
        self.file = file

        index, (vers, bcnt) = readversion(self.file, index)
        print "TTree vers, bcnt", vers, bcnt

        index, (vers, bcnt) = readversion(self.file, index)
        print "TNamed vers, bcnt", vers, bcnt

        index = skipversion(self.file, index)
        index = skiptobject(self.file, index)

        self.name = repr(string(self.file, index))
        index = stepstring(self.file, index)
        self.title = repr(string(self.file, index))
        index = stepstring(self.file, index)



        
TKey.classes["TTree"] = TTree

file = TFile("/home/pivarski/storage/data/TrackResonanceNtuple_uncompressed.root")
print file.get("twoMuon")
