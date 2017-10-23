#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import struct
from collections import namedtuple

import numpy

import uproot.const
from uproot.source.compressed import Compression
from uproot.source.compressed import CompressedSource
from uproot.source.cursor import Cursor

################################################################ ROOTDirectory

class ROOTDirectory(object):
    """Represents a ROOT file or subdirectory; use to extract objects.

    Do not create it directly; use uproot.open or uproot.iterator to open files.

        * `dir[name]` or `dir.get(name, cycle=None)` to extract an object (aware of '/' and ';' notations).
        * `dir.name` is the name of the directory or file (as written in the file itself).
        * `dir.compression` (with `algo`, `level` and `algoname` attributes) describes the compression.

    The following have arguments `recursive=False, filtername=lambda name: True, filterclass=lambda name: True`:

        * `dir.keys()` iterates over key names (bytes objects) in this directory.
        * `dir.values()` iterates over the contents (ROOT objects) in this directory.
        * `dir.items()` iterates over key-value pairs in this directory.
        * `dir.classes()` iterates over key-classname pairs (both bytes objects) in this directory.

    Filters allow you to exclude names (bytes objects) or class names (bytes objects) from the search.
    Eliminating a directory does not eliminate its contents.

    The following are shortcuts for recursive=True:

        * `dir.allkeys()`
        * `dir.allvalues()` 
        * `dir.allitems()` 
        * `dir.allclasses()` 
    """

    class _FileContext(object):
        def __init__(self, streaminfo, classes, compression):
            self.streaminfo, self.classes, self.compression = streaminfo, classes, compression

    @staticmethod
    def readtop(source):
        # See https://root.cern/doc/master/classTFile.html

        cursor = Cursor(0)
        magic, fVersion = cursor.fields(source, ROOTDirectory._readtop_format1)
        if magic != b"root":
            raise ValueError("not a ROOT file (starts with {0} instead of 'root')".format(repr(magic)))
        if fVersion < 1000000:
            fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo, fUUID = cursor.fields(source, ROOTDirectory._readtop_format2_small)
        else:
            fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo, fUUID = cursor.fields(source, ROOTDirectory._readtop_format2_big)

        # classes requried to read streamers (bootstrap)
        streamerclasses = {b"TStreamerInfo":             TStreamerInfo,
                           b"TStreamerElement":          TStreamerElement,
                           b"TStreamerBase":             TStreamerBase,
                           b"TStreamerBasicType":        TStreamerBasicType,
                           b"TStreamerBasicPointer":     TStreamerBasicPointer,
                           b"TStreamerLoop":             TStreamerLoop,
                           b"TStreamerObject":           TStreamerObject,
                           b"TStreamerObjectPointer":    TStreamerObjectPointer,
                           b"TStreamerObjectAny":        TStreamerObjectAny,
                           b"TStreamerObjectAnyPointer": TStreamerObjectAnyPointer,
                           b"TStreamerString":           TStreamerString,
                           b"TStreamerSTL":              TStreamerSTL,
                           b"TStreamerSTLString":        TStreamerSTLString,
                           b"TStreamerArtificial":       TStreamerArtificial,
                           b"TObjArray":                 TObjArray}

        streamercontext = ROOTDirectory._FileContext(None, streamerclasses, Compression(fCompress))
        streamerkey = TKey.read(source, Cursor(fSeekInfo), streamercontext)
        streaminfo = _readstreamers(streamerkey._source, streamerkey._cursor, streamercontext)
        classes = _defineclasses(streaminfo)

        context = ROOTDirectory._FileContext(streaminfo, classes, Compression(fCompress))

        keycursor = Cursor(fBEGIN)
        mykey = TKey.read(source, keycursor, context)
        return ROOTDirectory.read(source, keycursor, context, mykey)

    _readtop_format1       = struct.Struct("!4si")
    _readtop_format2_small = struct.Struct("!iiiiiiBiii18s")
    _readtop_format2_big   = struct.Struct("!iqqiiiBiqi18s")

    @staticmethod
    def read(source, cursor, context, mykey):
        # See https://root.cern/doc/master/classTDirectoryFile.html.

        fVersion, fDatimeC, fDatimeM, fNbytesKeys, fNbytesName = cursor.fields(source, ROOTDirectory._read_format1)
        if fVersion <= 1000:
            fSeekDir, fSeekParent, fSeekKeys = cursor.fields(source, ROOTDirectory._read_format2_small)
        else:
            fSeekDir, fSeekParent, fSeekKeys = cursor.fields(source, ROOTDirectory._read_format2_big)

        subcursor = Cursor(fSeekKeys)
        headerkey = TKey.read(source, subcursor, context)

        nkeys = subcursor.field(source, ROOTDirectory._read_format3)
        keys = [TKey.read(source, subcursor, context) for i in range(nkeys)]

        out = ROOTDirectory(mykey.fName, context, keys)

        # source may now close the file (and reopen it when we read again)
        source.dismiss()
        return out

    _read_format1       = struct.Struct("!hIIii")
    _read_format2_small = struct.Struct("!iii")
    _read_format2_big   = struct.Struct("!qqq")
    _read_format3       = struct.Struct("!i")

    def __init__(self, name, context, keys):
        self.name, self._context, self._keys = name, context, keys

    @property
    def compression(self):
        return self._context.compression

    def __repr__(self):
        return "<ROOTDirectory {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def __getitem__(self, name):
        return self.get(name)

    def __len__(self):
        return len(self._keys)

    def __iter__(self):
        return self.keys()

    @staticmethod
    def _withcycle(key):
        return "{0};{1}".format(key.fName.decode("ascii"), key.fCycle).encode("ascii")

    def keys(self, recursive=False, filtername=lambda name: True, filterclass=lambda classname: True):
        """Iterates over key names (bytes objects) in this directory.

            * `recursive` if `True`, descend into subdirectories; if `False` (the default), do not.
            * `filtername` must be callable; results are returned only if `filtername(key name)` returns `True`.
            * `filterclass` must be callable; results are returned only if `filterclass(class name)` returns `True`.

        When iterating recursively, eliminating a directory does not eliminate its contents.
        """
        for key in self._keys:
            if filtername(key.fName) and filterclass(key.fClassName):
                yield self._withcycle(key)

            if recursive and key.fClassName == b"TDirectory":
                for name in key.get().keys(recursive, filtername, filterclass):
                    yield "{0}/{1}".format(self._withcycle(key).decode("ascii"), name.decode("ascii")).encode("ascii")

    def values(self, recursive=False, filtername=lambda name: True, filterclass=lambda classname: True):
        """Iterates over the contents (ROOT objects) in this directory.

            * `recursive` if `True`, descend into subdirectories; if `False` (the default), do not.
            * `filtername` must be callable; results are returned only if `filtername(key name)` returns `True`.
            * `filterclass` must be callable; results are returned only if `filterclass(class name)` returns `True`.

        When iterating recursively, eliminating a directory does not eliminate its contents.
        """
        for key in self._keys:
            if filtername(key.fName) and filterclass(key.fClassName):
                yield key.get()

            if recursive and key.fClassName == b"TDirectory":
                for value in key.get().values(recursive, filtername, filterclass):
                    yield value

    def items(self, recursive=False, filtername=lambda name: True, filterclass=lambda classname: True):
        """Iterates over key-value pairs in this directory.

            * `recursive` if `True`, descend into subdirectories; if `False` (the default), do not.
            * `filtername` must be callable; results are returned only if `filtername(key name)` returns `True`.
            * `filterclass` must be callable; results are returned only if `filterclass(class name)` returns `True`.

        When iterating recursively, eliminating a directory does not eliminate its contents.
        """
        for key in self._keys:
            if filtername(key.fName) and filterclass(key.fClassName):
                yield self._withcycle(key), key.get()

            if recursive and key.fClassName == b"TDirectory":
                for name, value in key.get().items(recursive, filtername, filterclass):
                    yield "{0}/{1}".format(self._withcycle(key).decode("ascii"), name.decode("ascii")).encode("ascii"), value

    def classes(self, recursive=False, filtername=lambda name: True, filterclass=lambda classname: True):
        """Iterates over key-classname pairs (both bytes objects) in this directory.

            * `recursive` if `True`, descend into subdirectories; if `False` (the default), do not.
            * `filtername` must be callable; results are returned only if `filtername(key name)` returns `True`.
            * `filterclass` must be callable; results are returned only if `filterclass(class name)` returns `True`.

        When iterating recursively, eliminating a directory does not eliminate its contents.
        """
        for key in self._keys:
            if filtername(key.fName) and filterclass(key.fClassName):
                yield self._withcycle(key), key.fClassName

            if recursive and key.fClassName == b"TDirectory":
                for name, classname in key.get().classes(recursive, filtername, filterclass):
                    yield "{0}/{1}".format(self._withcycle(key).decode("ascii"), name.decode("ascii")).encode("ascii"), classname

    def allkeys(self, filtername=lambda name: True, filterclass=lambda classname: True):
        """Recursively iterates over key names (bytes objects) in this directory.

            * `filtername` must be callable; results are returned only if `filtername(key name)` returns `True`.
            * `filterclass` must be callable; results are returned only if `filterclass(class name)` returns `True`.

        When iterating recursively, eliminating a directory does not eliminate its contents.
        """
        return self.keys(True, filtername, filterclass)

    def allvalues(self, filtername=lambda name: True, filterclass=lambda classname: True):
        """Recursively iterates over the contents (ROOT objects) in this directory.

            * `filtername` must be callable; results are returned only if `filtername(key name)` returns `True`.
            * `filterclass` must be callable; results are returned only if `filterclass(class name)` returns `True`.

        When iterating recursively, eliminating a directory does not eliminate its contents.
        """
        return self.values(True, filtername, filterclass)

    def allitems(self, filtername=lambda name: True, filterclass=lambda classname: True):
        """Recursively iterates over key-value pairs in this directory.

            * `filtername` must be callable; results are returned only if `filtername(key name)` returns `True`.
            * `filterclass` must be callable; results are returned only if `filterclass(class name)` returns `True`.

        When iterating recursively, eliminating a directory does not eliminate its contents.
        """
        return self.items(True, filtername, filterclass)

    def allclasses(self, filtername=lambda name: True, filterclass=lambda classname: True):
        """Recursively iterates over key-classname pairs (both bytes objects) in this directory.

            * `filtername` must be callable; results are returned only if `filtername(key name)` returns `True`.
            * `filterclass` must be callable; results are returned only if `filterclass(class name)` returns `True`.

        When iterating recursively, eliminating a directory does not eliminate its contents.
        """
        return self.classes(True, filtername, filterclass)

    def get(self, name, cycle=None):
        """Get an object from the directory, interpreting '/' as subdirectories and ';' to delimit cycle number.

        Synonym for `dir[name]`.

        An explicit `cycle` overrides any number after ';'.
        """
        if hasattr(name, "encode"):
            name = name.encode("ascii")

        if b"/" in name:
            out = self
            for n in name.split(b"/"):
                out = out.get(n, cycle)
            return out

        else:
            if cycle is None and b";" in name:
                at = name.rindex(b";")
                name, cycle = name[:at], name[at + 1:]
                cycle = int(cycle)

            for key in self._keys:
                if key.fName == name:
                    if cycle is None or key.fCycle == cycle:
                        return key.get()
            raise KeyError("not found: {0}".format(repr(name)))

    def __enter__(self, *args, **kwds):
        return self

    def __exit__(self, *args, **kwds):
        pass

################################################################ helper functions for common tasks

def _startcheck(source, cursor):
    start = cursor.index
    cnt, vers = cursor.fields(source, _startcheck._format_cntvers)
    cnt = int(numpy.int64(cnt) & ~uproot.const.kByteCountMask)
    return start, cnt + 4, vers
_startcheck._format_cntvers = struct.Struct("!IH")

def _endcheck(start, cursor, cnt):
    observed = cursor.index - start
    if observed != cnt:
        raise ValueError("object has {0} bytes; expected {1}".format(observed, cnt))

def _skiptobj(source, cursor):
    version = cursor.field(source, _skiptobj._format1)
    if numpy.int64(version) & uproot.const.kByteCountVMask:
        cursor.skip(4)
    fUniqueID, fBits = cursor.fields(source, _skiptobj._format2)
    fBits = numpy.uint32(fBits) | uproot.const.kIsOnHeap
    if fBits & uproot.const.kIsReferenced:
        cursor.skip(2)
_skiptobj._format1 = struct.Struct("!h")
_skiptobj._format2 = struct.Struct("!II")

def _nametitle(source, cursor):
    start, cnt, vers = _startcheck(source, cursor)
    _skiptobj(source, cursor)
    name = cursor.string(source)
    title = cursor.string(source)
    _endcheck(start, cursor, cnt)
    return name, title

def _readanyref(source, cursor, context):
    beg = cursor.index - cursor.origin
    bcnt = cursor.field(source, struct.Struct("!I"))

    if numpy.int64(bcnt) & uproot.const.kByteCountMask == 0 or numpy.int64(bcnt) == uproot.const.kNewClassTag:
        vers = 0
        start = 0
        tag = bcnt
        bcnt = 0
    else:
        vers = 1
        start = cursor.index - cursor.origin
        tag = cursor.field(source, struct.Struct("!I"))

    if numpy.int64(tag) & uproot.const.kClassMask == 0:
        # reference object
        if tag == 0:
            return None                             # return null

        elif tag == 1:
            raise NotImplementedError("tag == 1 means self; not implemented yet")

        elif tag not in cursor.refs:
            # jump past this object
            cursor.index = cursor.origin + beg + bcnt + 4
            return None                             # return null

        else:
            return cursor.refs[tag]                 # return object

    elif tag == uproot.const.kNewClassTag:
        # new class and object
        cname = cursor.cstring(source)

        fct = context.classes.get(cname, Undefined)

        if vers > 0:
            cursor.refs[start + uproot.const.kMapOffset] = fct
        else:
            cursor.refs[len(cursor.refs) + 1] = fct

        obj = fct(source, cursor, context)

        if vers > 0:
            cursor.refs[beg + uproot.const.kMapOffset] = obj
        else:
            cursor.refs[len(cursor.refs) + 1] = obj

        return obj                                  # return object

    else:
        # reference class, new object
        ref = int(numpy.int64(tag) & ~uproot.const.kClassMask)

        if ref not in cursor.refs:
            raise IOError("invalid class-tag reference")

        fct = cursor.refs[ref]                      # reference class

        if fct not in context.classes.values():
            raise IOError("invalid class-tag reference (not a factory)")

        obj = fct(source, cursor, context)          # new object

        if vers > 0:
            cursor.refs[beg + uproot.const.kMapOffset] = obj
        else:
            cursor.refs[len(cursor.refs) + 1] = obj

        return obj                                  # return object

def _readstreamers(source, cursor, context):
    start, cnt, vers = _startcheck(source, cursor)

    _skiptobj(source, cursor)
    name = cursor.string(source)
    size = cursor.field(source, struct.Struct("!i"))
    _format_n = struct.Struct("!B")

    infos = []
    for i in range(size):
        infos.append(_readanyref(source, cursor, context))
        assert isinstance(infos[-1], TStreamerInfo)
        # options not used, but they must be read in
        n = cursor.field(source, _format_n)
        cursor.bytes(source, n)

    _endcheck(start, cursor, cnt)

def _defineclasses(infos):
    return {b"TH1F": TH1F}

################################################################ built-in ROOT objects for bootstrapping up to streamed classes

class TKey(object):
    """Represents a key; for seeking to an object in a ROOT file.

        * `key.get()` to extract an object (initiates file-reading and possibly decompression).

    See `https://root.cern/doc/master/classTKey.html` for field definitions.
    """

    __slots__ = ("_source", "_cursor", "_context", "fNbytes", "fVersion", "fObjlen", "fDatime", "fKeylen", "fCycle", "fSeekKey", "fSeekPdir", "fClassName", "fName", "fTitle")

    @staticmethod
    def read(source, cursor, context):
        fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle = cursor.fields(source, TKey._read_format1)
        if fVersion <= 1000:
            fSeekKey, fSeekPdir = cursor.fields(source, TKey._read_format2_small)
        else:
            fSeekKey, fSeekPdir = cursor.fields(source, TKey._read_format2_big)

        fClassName = cursor.string(source)
        fName = cursor.string(source)
        if fSeekPdir == 0:
            assert source.data(cursor.index, cursor.index + 1)[0] == 0
            cursor.skip(1)     # Top TDirectory fName and fTitle...
        fTitle = cursor.string(source)
        if fSeekPdir == 0:
            assert source.data(cursor.index, cursor.index + 1)[0] == 0
            cursor.skip(1)     # ...are prefixed *and* null-terminated! Both!

        # object size != compressed size means it's compressed
        if fObjlen != fNbytes - fKeylen:
            keysource = CompressedSource(context.compression, source, Cursor(fSeekKey + fKeylen), fNbytes - fKeylen, fObjlen)
            keycursor = Cursor(0, origin=-fKeylen)

        # otherwise, it's uncompressed
        else:
            keysource = source
            keycursor = Cursor(fSeekKey + fKeylen, origin=fSeekKey)

        return TKey(keysource, keycursor, context, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle)

    _read_format1       = struct.Struct("!ihiIhh")
    _read_format2_small = struct.Struct("!ii")
    _read_format2_big   = struct.Struct("!qq")

    def __init__(self, source, cursor, context, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle):
        self._source, self._cursor, self._context, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle = source, cursor, context, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle

    def get(self):
        """Extract the object this key points to.

        Objects are not read or decompressed until this function is explicitly called.
        """
        if self.fClassName == b"TDirectory":
            return ROOTDirectory.read(self._source, self._cursor, self._context, self)

        elif self.fClassName in self._context.classes:
            return self._context.classes[self.fClassName](self._source, self._cursor.copied(), self._context)

        else:
            return Undefined(self._source, self._cursor.copied(), self._context)

class TStreamerInfo(object):
    _format = struct.Struct("!Ii")

    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        self.fName, _ = _nametitle(source, cursor)
        self.fCheckSum, self.fClassVersion = cursor.fields(source, self._format)
        self.fElements = _readanyref(source, cursor, context)
        assert isinstance(self.fElements, list)
        _endcheck(start, cursor, cnt)

    def format(self):
        return "StreamerInfo for class: {0}, version={1}, checksum=0x{2:08x}\n{3}{4}".format(self.fName, self.fClassVersion, self.fCheckSum, "\n".join("  " + x.format() for x in self.fElements), "\n" if len(self.fElements) > 0 else "")

class TStreamerElement(object):
    _format1 = struct.Struct("!iiii")
    _format2 = struct.Struct("!i")
    _format3 = struct.Struct("!ddd")

    def __init__(self, source, cursor, context):    
        start, cnt, vers = _startcheck(source, cursor)

        self.fOffset = 0
        # https://github.com/root-project/root/blob/master/core/meta/src/TStreamerElement.cxx#L505
        self.fName, self.fTitle = _nametitle(source, cursor)
        self.fType, self.fSize, self.fArrayLength, self.fArrayDim = cursor.fields(source, self._format1)

        if vers == 1:
            n = cursor.field(source, self._format2)
            self.fMaxIndex = cursor.array(source, n, ">i4")
        else:
            self.fMaxIndex = cursor.array(source, 5, ">i4")

        self.fTypeName = cursor.string(source)

        if self.fType == 11 and (self.fTypeName == "Bool_t" or self.fTypeName == "bool"):
            self.fType = 18

        if vers <= 2:
            # FIXME
            # self.fSize = self.fArrayLength * gROOT->GetType(GetTypeName())->Size()
            pass

        self.fXmin, self.fXmax, self.fFactor = 0.0, 0.0, 0.0
        if vers == 3:
            self.fXmin, self.fXmax, self.fFactor = cursor.fields(source, self._format3)
        if vers > 3:
            # FIXME
            # if (TestBit(kHasRange)) GetRange(GetTitle(),fXmin,fXmax,fFactor)
            pass

        _endcheck(start, cursor, cnt)

    def format(self):
        return "{0:15s} {1:15s} offset={2:3d} type={3:2d} {4}".format(self.fName, self.fTypeName, self.fOffset, self.fType, self.fTitle)

class TStreamerArtificial(TStreamerElement):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerArtificial, self).__init__(source, cursor, context)
        _endcheck(start, cursor, cnt)

class TStreamerBase(TStreamerElement):
    _format = struct.Struct("!i")

    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerBase, self).__init__(source, cursor, context)
        if vers > 2:
            self.fBaseVersion = cursor.field(source, self._format)
        _endcheck(start, cursor, cnt)

class TStreamerBasicPointer(TStreamerElement):
    _format = struct.Struct("!i")

    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerBasicPointer, self).__init__(source, cursor, context)
        self.fCountVersion = cursor.field(source, self._format)
        self.fCountName = cursor.string(source)
        self.fCountClass = cursor.string(source)
        _endcheck(start, cursor, cnt)

class TStreamerBasicType(TStreamerElement):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerBasicType, self).__init__(source, cursor, context)

        if uproot.const.kOffsetL < self.fType < uproot.const.kOffsetP:
            self.fType -= uproot.const.kOffsetL

        basic = True
        if self.fType in (uproot.const.kBool, uproot.const.kUChar, uproot.const.kChar):
            self.fSize = 1
        elif self.fType in (uproot.const.kUShort, uproot.const.kShort):
            self.fSize = 2
        elif self.fType in (uproot.const.kBits, uproot.const.kUInt, uproot.const.kInt, uproot.const.kCounter):
            self.fSize = 4
        elif self.fType in (uproot.const.kULong, uproot.const.kULong64, uproot.const.kLong, uproot.const.kLong64):
            self.fSize = 8
        elif self.fType in (uproot.const.kFloat, uproot.const.kFloat16):
            self.fSize = 4
        elif self.fType in (uproot.const.kDouble, uproot.const.kDouble32):
            self.fSize = 8
        elif self.fType == uproot.const.kCharStar:
            self.fSize = numpy.dtype(numpy.intp).itemsize
        else:
            basic = False

        if basic and self.fArrayLength > 0:
            self.fSize *= self.fArrayLength

        _endcheck(start, cursor, cnt)

class TStreamerLoop(TStreamerElement):
    _format = struct.Struct("!i")

    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerLoop, self).__init__(source, cursor, context)
        self.fCountVersion = cursor.field(source, self._format)
        self.fCountName = cursor.string(source)
        self.fCountClass = cursor.string(source)
        _endcheck(start, cursor, cnt)

class TStreamerObject(TStreamerElement):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerObject, self).__init__(source, cursor, context)
        _endcheck(start, cursor, cnt)

class TStreamerObjectAny(TStreamerElement):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerObjectAny, self).__init__(source, cursor, context)
        _endcheck(start, cursor, cnt)

class TStreamerObjectAnyPointer(TStreamerElement):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerObjectAnyPointer, self).__init__(source, cursor, context)
        _endcheck(start, cursor, cnt)

class TStreamerObjectPointer(TStreamerElement):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerObjectPointer, self).__init__(source, cursor, context)
        _endcheck(start, cursor, cnt)

class TStreamerSTL(TStreamerElement):
    _format = struct.Struct("!ii")

    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerSTL, self).__init__(source, cursor, context)

        if vers > 2:
            # https://github.com/root-project/root/blob/master/core/meta/src/TStreamerElement.cxx#L1936
            raise NotImplementedError
        else:
            self.fSTLtype, self.fCtype = cursor.fields(source, self._format)

        if self.fSTLtype == uproot.const.kSTLmultimap or self.fSTLtype == uproot.const.kSTLset:
            if self.fTypeName.startswith("std::set") or self.fTypeName.startswith("set"):
                self.fSTLtype = uproot.const.kSTLset
            elif self.fTypeName.startswith("std::multimap") or self.fTypeName.startswith("multimap"):
                self.fSTLtype = uproot.const.kSTLmultimap

        _endcheck(start, cursor, cnt)

class TStreamerSTLString(TStreamerSTL):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerSTLString, self).__init__(source, cursor, context)
        _endcheck(start, cursor, cnt)

class TStreamerString(TStreamerElement):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        super(TStreamerString, self).__init__(source, cursor, context)
        _endcheck(start, cursor, cnt)

################################################################ streamed classes (with some overrides)

class StreamedObject(object):
    """Base class for all objects extracted from a ROOT file using streamers.
    """

    def __init__(self, source, cursor, context):
        pass

    def __repr__(self):
        if hasattr(self, "name"):
            return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, repr(self.name), id(self))
        else:
            return "<{0} at 0x{1:012x}>".format(self.__class__.__name__, id(self))

class TObject(StreamedObject):
    "Base class for ROOT objects (ignore the streamer; use this instead)."
    def __init__(self, source, cursor, context):
        _skiptobj(source, cursor)

def TString(source, cursor, context):
    "Read a TString in as a Python string."
    return cursor.string(source)

class TObjArray(list):
    "Read a TObjArray in as a Python list."
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        _skiptobj(source, cursor)
        name = cursor.string(source)
        size, low = cursor.fields(source, struct.Struct("!ii"))
        self.extend([_readanyref(source, cursor, context) for i in range(size)])
        _endcheck(start, cursor, cnt)

class TList(list):
    "Read a TList in as a Python list."
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        _skiptobj(source, cursor)
        name = cursor.string(source)
        size = cursor.field(source, struct.Struct("!i"))
        self.extend([_readanyref(source, cursor, context) for i in range(size)])
        _endcheck(start, cursor, cnt)

class TArray(list):
    "TArrays aren't described by streamers, but they're pretty simple. We make make them a subclass of Python's list."
    _format = struct.Struct("!i")
    def __init__(self, source, cursor, context):
        length = cursor.field(source, self._format)
        self.extend(cursor.array(source, length, self._dtype))

class TArrayC(TArray):
    "TArray of 8-bit integers."
    _dtype = numpy.dtype(">i1")

class TArrayS(TArray):
    "TArray of 16-bit integers."
    _dtype = numpy.dtype(">i2")

class TArrayI(TArray):
    "TArray of 32-bit integers."
    _dtype = numpy.dtype(">i4")

class TArrayL(TArray):
    "TArray of 32-bit or 64-bit longs."
    _dtype = numpy.dtype(numpy.int_).newbyteorder(">")

class TArrayL64(TArray):
    "TArray of 64-bit integers."
    _dtype = numpy.dtype(">i8")

class TArrayF(TArray):
    "TArray of 32-bit floats."
    _dtype = numpy.dtype(">f4")

class TArrayD(TArray):
    "TArray of 64-bit floats."
    _dtype = numpy.dtype(">f8")

class Undefined(StreamedObject):
    "Represents a ROOT class that we have no deserializer for (and therefore skip over)."
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        cursor.skip(cnt - 2)
        _endcheck(start, cursor, cnt)

class TNamed(TObject):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        TObject.__init__(self, source, cursor, context)
        self.fName = cursor.string(source)
        self.fTitle = cursor.string(source)
        print "TNamed", cnt, vers, repr(self.fName), repr(self.fTitle)
        _endcheck(start, cursor, cnt)

class TAttLine(StreamedObject):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        self.fLineColor, self.fLineStyle, self.fLineWidth = cursor.fields(source, struct.Struct("!hhh"))
        print "TAttLine", self.fLineColor, self.fLineStyle, self.fLineWidth
        _endcheck(start, cursor, cnt)

class TAttFill(StreamedObject):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        self.fFillColor, self.fFillStyle = cursor.fields(source, struct.Struct("!hh"))
        print "TAttFill", self.fFillColor, self.fFillStyle
        _endcheck(start, cursor, cnt)

class TAttMarker(StreamedObject):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        self.fMarkerColor, self.fMarkerStyle, self.fMarkerSize = cursor.fields(source, struct.Struct("!hhf"))
        print "TAttMarker", self.fMarkerColor, self.fMarkerStyle, self.fMarkerSize
        _endcheck(start, cursor, cnt)

class TAttAxis(StreamedObject):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        self.fNdivisions, self.fAxisColor, self.fLabelColor, self.fLabelFont, self.fLabelOffset, self.fLabelSize, self.fTickLength, self.fTitleOffset, self.fTitleSize, self.fTitleColor, self.fTitleFont = cursor.fields(source, struct.Struct("!ihhhfffffhh"))
        print "TAttAxis", self.fNdivisions, self.fAxisColor, self.fLabelColor, self.fLabelFont, self.fLabelOffset, self.fLabelSize, self.fTickLength, self.fTitleOffset, self.fTitleSize, self.fTitleColor, self.fTitleFont
        _endcheck(start, cursor, cnt)

class TCollection(TObject):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        print "TCollection", cnt, vers
        TObject.__init__(self, source, cursor, context)
        self.fName = TString(source, cursor, context)
        self.fSize = cursor.field(source, struct.Struct("!i"))
        _endcheck(start, cursor, cnt)

class TSeqCollection(TCollection):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        print "TSeqCollection", cnt, vers
        TCollection.__init__(self, source, cursor, context)
        _endcheck(start, cursor, cnt)

class THashList(TList):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        print "THashList", cnt, vers
        TList.__init__(self, source, cursor, context)
        _endcheck(start, cursor, cnt)

class TAxis(TNamed, TAttAxis):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        TNamed.__init__(self, source, cursor, context)
        TAttAxis.__init__(self, source, cursor, context)
        self.fNbins, self.fXmin, self.fXmax = cursor.fields(source, struct.Struct("!idd"))
        self.fXbins = TArrayD(source, cursor, context)
        self.fFirst, self.fLast, self.fBits2, self.fTimeDisplay = cursor.fields(source, struct.Struct("!iiH?"))
        self.fTimeFormat = TString(source, cursor, context)
        self.fLabels = _readanyref(source, cursor, context)
        self.fModLabs = _readanyref(source, cursor, context)
        print "TAxis", self.fNbins, self.fXmin, self.fXmax, self.fXbins, self.fFirst, self.fLast, self.fBits2, self.fTimeDisplay, repr(self.fTimeFormat), self.fLabels, self.fModLabs
        _endcheck(start, cursor, cnt)

class TH1(TNamed, TAttLine, TAttFill, TAttMarker):
    _format1 = struct.Struct("!i")
    _format2 = struct.Struct("!hhdddddddd")
    _format3 = struct.Struct("!i")
    _format4 = struct.Struct("!iB")
    _format5 = struct.Struct("!i")

    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        print "TH1", cnt, vers
        TNamed.__init__(self, source, cursor, context)
        TAttLine.__init__(self, source, cursor, context)
        TAttFill.__init__(self, source, cursor, context)
        TAttMarker.__init__(self, source, cursor, context)
        self.fNcells = cursor.field(source, self._format1)
        self.fXaxis = TAxis(source, cursor, context)
        self.fYaxis = TAxis(source, cursor, context)
        self.fZaxis = TAxis(source, cursor, context)
        self.fBarOffset, self.fBarWidth, self.fEntries, self.fTsumw, self.fTsumw2, self.fTsumwx, self.fTsumwx2, self.fMaximum, self.fMinimum, self.fNormFactor = cursor.fields(source, struct.Struct("!hhdddddddd"))
        self.fContour = TArrayD(source, cursor, context)
        self.fSumw2 = TArrayD(source, cursor, context)
        self.fOption = TString(source, cursor, context)
        self.fFunctions = TList(source, cursor, context)
        self.fBufferSize, _fBuffer = cursor.fields(source, self._format4)
        self.fBuffer = cursor.array(source, self.fBufferSize, ">f8")
        self.fBinStatErrOpt = cursor.field(source, self._format5)
        _endcheck(start, cursor, cnt)

class TH1F(TH1, TArrayF):
    def __init__(self, source, cursor, context):
        start, cnt, vers = _startcheck(source, cursor)
        print "TH1F", cnt, vers
        TH1.__init__(self, source, cursor, context)
        TArrayF.__init__(self, source, cursor, context)

        print "TH1F", self.fNcells, self.fXaxis.__dict__, self.fYaxis.__dict__, self.fZaxis.__dict__, self.fBarOffset, self.fBarWidth, self.fEntries, self.fTsumw, self.fTsumw2, self.fTsumwx, self.fTsumwx2, self.fMaximum, self.fMinimum, self.fNormFactor, self.fContour, self.fSumw2, repr(self.fOption), self.fFunctions, self.fBufferSize, self.fBuffer, self.fBinStatErrOpt, list(self)

        _endcheck(start, cursor, cnt)
