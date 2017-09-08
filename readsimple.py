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

file = numpy.memmap("/home/pivarski/storage/data/TrackResonanceNtuple_uncompressed.root", mode="r")
index = 0

# START File.readHeader

assert field(file, index, "!4s") == "root", "magic"
index = step(index, "!4s")

version, begin = fields(file, index, "!ii")
index = step(index, "!ii")

if version < 1000000:  # small file
    end, seekfree, nbytesfree, nfree, nbytesname, units, compression, seekinfo, nbytesinfo = fields(file, index, "!iiiiiBiii")
    index = step(index, "!iiiiiBiii")
else:
    end, seekfree, nbytesfree, nfree, nbytesname, units, compression, seekinfo, nbytesinfo = fields(file, index, "!qqiiiBiqi")
    index = step(index, "!qqiiiBiqi")
version %= 1000000

uuid = field(file, index, "!18s")
index = step(index, "!18s")

#     START dir.readDirInfo

#         START dir.recordSize

recordSize = 2 + 4 + 4 + 4 + 4   # fVersion, ctime, mtime, nbyteskeys, nbytesname
if version >= 40000:
    recordSize += 8 + 8 + 8      # seekdir, seekparent, seekkeys
else:
    recordSize += 4 + 4 + 4      # seekdir, seekparent, seekkeys

#         END dir.recordSize

nbytes = nbytesname + recordSize

assert nbytes + begin <= end, "dir header length"

#         START dir.UnmarshalROOT

def dirUnmarshalROOT(file, index):
    version, ctime, mtime = fields(file, index, "!hII")
    index = step(index, "!hII")

    nbyteskeys, nbytesname = fields(file, index, "!ii")
    index = step(index, "!ii")

    if version <= 1000:
        seekdir, seekparent, seekkeys = fields(file, index, "!iii")
    else:
        seekdir, seekparent, seekkeys = fields(file, index, "!qqq")

    return version, ctime, mtime, nbyteskeys, nbytesname, seekdir, seekparent, seekkeys

dir_version, dir_ctime, dir_mtime, dir_nbyteskeys, dir_nbytesname, dir_seekdir, dir_seekparent, dir_seekkeys = dirUnmarshalROOT(file, begin + nbytesname)

#         END dir.UnmarshalROOT

nk = 4
dir_keyversion = field(file, begin + nk, "!h")
if dir_keyversion > 1000:
    nk += 2 + 2*4 + 2*2 + 2*8  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory
else:
    nk += 2 + 2*4 + 2*2 + 2*4  # fVersion, fObjectSize*Date, fKeyLength*fCycle, fSeekKey*fSeekParentDirectory

dir_index = begin + nk
dir_classname = string(file, dir_index)
dir_index = stepstring(file, dir_index)
dir_name = string(file, dir_index)
dir_index = stepstring(file, dir_index)
dir_title = string(file, dir_index)
dir_index = stepstring(file, dir_index)

assert 10 <= dir_nbytesname <= 1000, "directory info"

#     END dir.readDirInfo

#     BEGIN readStreamerInfo      not unless we have to!
#     END readStreamerInfo

#     BEGIN dir.readKeys

#         START key.UnmarshalROOT

def keyUnmarshalROOT(file, index):
    bytes, version, objlen, datetime, keylen, cycle = fields(file, index, "!ihiIhh")
    index = step(index, "!ihiIhh")

    if version > 1000:
        seekkey, seekpdir = fields(file, index, "!qq")
        index = step(index, "!qq")
    else:
        seekkey, seekpdir = fields(file, index, "!ii")
        index = step(index, "!ii")

    classname = string(file, index)
    index = stepstring(file, index)
    name = string(file, index)
    index = stepstring(file, index)
    title = string(file, index)
    index = stepstring(file, index)

    return bytes, version, objlen, datetime, keylen, cycle, seekkey, seekpdir, classname, name, title

keyhdr_bytes, keyhdr_version, keyhdr_objlen, keyhdr_datetime, keyhdr_keylen, keyhdr_cycle, keyhdr_seekkey, keyhdr_seekpdir, keyhdr_classname, keyhdr_name, keyhdr_title = keyUnmarshalROOT(file, dir_seekkeys)

#         END key.UnmarshalROOT




#     END dir.readKeys

