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
    start, cnt, vers = StreamedObject._startcheck(source, cursor)
    _skiptobj(source, cursor)

    name = cursor.string(source)
    title = cursor.string(source)
    StreamedObject._endcheck(start, cursor, cnt)
    return name, title

class Collection(object):
    def __init__(self, source, cursor, classes):
        print "Collection"

        # TList, but can't use StreamedObject yet!
        start, cnt, vers = StreamedObject._startcheck(source, cursor)

        print "start, cnt, vers", start, cnt, vers

        _skiptobj(source, cursor)

        print cursor.hexdump(source)

        name = cursor.string(source)
        print "name", repr(name)
        size = cursor.field(source, struct.Struct("!i"))
        print "size", size

        print cursor.hexdump(source)

        # only TObjArray!
        low, last = cursor.fields(source, struct.Struct("!ii"))

        z = StreamedObject._read(source, cursor, classes)
        print "z", z

        
class File(object):
    """Represents a ROOT file; use to extract objects.

        * `file.get(name, cycle=None)` to extract an object (aware of '/' and ';' notations).
        * `file.contents` is a `{name: classname}` dict of objects in the top directory.
        * `file.allcontents` is a `{name: classname}` dict of all objects in the file.
        * `file.compression` (with `algo`, `level` and `algoname` attributes) describes the compression.
        * `file.dir` is the top directory.
        * `file.name` is the name of the file (as written inside the file).
        * `file.TFile` are the ROOT C++ private fields. See `https://root.cern/doc/master/classTFile.html`.

    `file[name]` is a synonym for `file.get(name)`.

    File is iterable (iterate over keys) with a `len(file)` for the number of keys.
    """

    _Private = namedtuple("TFile", ["magic", "fVersion", "fBEGIN", "fEND", "fSeekFree", "fNbytesFree", "nfree", "fNbytesName", "fUnits", "fCompress", "fSeekInfo", "fNbytesInfo", "fUUID"])
    _format_small = struct.Struct("!4siiiiiiiBiii18s")
    _format_big   = struct.Struct("!4siiqqiiiBiqi18s")

    def __init__(self, source):
        self.TFile = self._Private(*Cursor(0).fields(source, self._format_small))
        if self.TFile.magic != b"root":
            raise ValueError("not a ROOT file (does not start with 'root')")
        if self.TFile.fVersion >= 1000000:
            self.TFile = self._Private(*Cursor(0).fields(source, self._format_big))

        cursor = Cursor(self.TFile.fBEGIN)
        classes = {}
        compression = Compression(self.TFile.fCompress)

        self.dir = Directory(Key(source, cursor, classes, compression), source, cursor, classes, compression)



        print "TFile", self.TFile
        cursor = Cursor(self.TFile.fSeekInfo)

        key = Key(source, cursor, classes, compression)
        print "key", key.TKey

        source = key.source
        cursor = key.cursor

        print cursor.hexdump(source)

        # TList, but can't use StreamedObject yet!
        start, cnt, vers = StreamedObject._startcheck(source, cursor)

        print "start, cnt, vers", start, cnt, vers

        _skiptobj(source, cursor)

        print cursor.hexdump(source)

        name = cursor.string(source)
        size = cursor.field(source, struct.Struct("!i"))
        print "size", size

        x = StreamedObject._read(source, cursor, {b"TStreamerInfo": StreamerInfo, b"TObjArray": Collection, b"TStreamerBase": StreamerElement})
        print "x", x



        # StreamedObject._endcheck(start, cursor, cnt)




        source.dismiss()

    @property
    def name(self):
        return self.dir.name

    @property
    def compression(self):
        return self.dir.compression

    def __repr__(self):
        return "<File {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def __getitem__(self, name):
        return self.get(name)

    def __len__(self):
        return len(self.dir)

    def __iter__(self):
        return iter(self.dir)

    def __enter__(self, *args, **kwds):
        return self

    def __exit__(self, *args, **kwds):
        pass

    @property
    def contents(self):
        return self.dir.contents

    @property
    def allcontents(self):
        return self.dir.allcontents

    def get(self, name, cycle=None):
        """Get an object from the file, interpreting '/' as subdirectories and ';' to delimit cycle number.

        Synonym for `file[name]`.

        An explicit `cycle` overrides ';'.
        """
        return self.dir.get(name, cycle)

class Key(object):
    """Represents a key; for seeking to an object in a ROOT file.

        * `key.get()` to extract an object (initiates file-reading and possibly decompression).
        * `key.classname` for the class name.
        * `key.name` for the object name.
        * `key.title` for the object title.
        * `key.cycle` for the object cycle.
        * `key.TKey` are the ROOT C++ private fields. See `https://root.cern/doc/master/classTKey.html`.
    """

    _Private = namedtuple("TKey", ["fNbytes", "fVersion", "fObjlen", "fDatime", "fKeylen", "fCycle", "fSeekKey", "fSeekPdir", "fClassName", "fName", "fTitle"])
    _format_small = struct.Struct("!ihiIhhii")
    _format_big   = struct.Struct("!ihiIhhqq")

    def __init__(self, source, cursor, classes, compression):
        vars1 = cursor.fields(source, self._format_small)
        if vars1[1] > 1000:
            vars1 = cursor.fields(source, self._format_big)

        classname = cursor.string(source)

        name = cursor.string(source)
        if vars1[7] == 0:
            assert source.data(cursor.index, cursor.index + 1)[0] == 0
            cursor.skip(1)     # Top TDirectory fName and fTitle...

        title = cursor.string(source)
        if vars1[7] == 0:
            assert source.data(cursor.index, cursor.index + 1)[0] == 0
            cursor.skip(1)     # ...are prefixed *and* null-terminated! Both!

        self.TKey = self._Private(*(vars1 + (classname, name, title)))
        self.classes = classes
        self.compression = compression

        #  object size != compressed size means it's compressed
        if self.TKey.fObjlen != self.TKey.fNbytes - self.TKey.fKeylen:
            self.source = CompressedSource(compression, source, Cursor(self.TKey.fSeekKey + self.TKey.fKeylen), self.TKey.fNbytes - self.TKey.fKeylen, self.TKey.fObjlen)
            self.cursor = Cursor(0, origin=-self.TKey.fKeylen)

        # otherwise, it's uncompressed
        else:
            self.source = source
            self.cursor = Cursor(self.TKey.fSeekKey + self.TKey.fKeylen)

    @property
    def classname(self):
        return self.TKey.fClassName

    @property
    def name(self):
        return self.TKey.fName

    @property
    def title(self):
        return self.TKey.fTitle

    @property
    def cycle(self):
        return self.TKey.fCycle

    def __repr__(self):
        return "<TKey {0} at 0x{1:012x}>".format(repr(self.name + b";" + repr(self.cycle).encode("ascii")), id(self))

    def get(self):
        """Extract the object this key points to.

        Objects are not read or decompressed until this function is explicitly called.
        """
        if self.classname == b"TDirectory":
            return Directory(self, self.source, self.cursor.copied(), self.classes, self.compression)
        else:
            return Undefined(self.source, self.cursor.copied(), self.classes)

class Directory(object):
    """Represents a ROOT directory; use to extract objects.

        * `dir.get(name, cycle=None)` to extract an object (aware of '/' and ';' notations).
        * `dir.contents` is a `{name: classname}` dict of objects in this directory.
        * `dir.allcontents` is a `{name: classname}` dict of all objects under this directory.
        * `dir.keys` is the keys (a list of Key objects).
        * `dir.name` is the name of the subdirectory or the file as a whole (as written inside the file).
        * `dir.TDirectory` are the ROOT C++ private fields. See `https://root.cern/doc/master/classTDirectoryFile.html`.

    `dir[name]` is a synonym for `dir.get(name)`.

    Directory is iterable (iterate over keys) with a `len(dir)` for the number of keys.
    """

    _Private = namedtuple("TDirectory", ["fVersion", "fDatimeC", "fDatimeM", "fNbytesKeys", "fNbytesName", "fSeekDir", "fSeekParent", "fSeekKeys"])
    _format1       = struct.Struct("!hIIii")
    _format2_small = struct.Struct("!iii")
    _format2_big   = struct.Struct("!qqq")
    _format3       = struct.Struct("!i")

    def __init__(self, key, source, cursor, classes, compression):
        self.key = key

        vars1 = cursor.fields(source, self._format1)
        if vars1[0] <= 1000:
            vars2 = cursor.fields(source, self._format2_small)
        else:
            vars2 = cursor.fields(source, self._format2_big)

        self.TDirectory = self._Private(*(vars1 + vars2))

        cursor.index = self.TDirectory.fSeekKeys
        self.header = Key(source, cursor, classes, compression)

        nkeys = cursor.field(source, self._format3)
        self.keys = [Key(source, cursor, classes, compression) for i in range(nkeys)]

    @property
    def name(self):
        return self.key.name

    @property
    def compression(self):
        return self.header.compression

    def __repr__(self):
        return "<Directory {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def __getitem__(self, name):
        return self.get(name)

    def __len__(self):
        return len(self.keys)

    def __iter__(self):
        return iter(self.keys)

    @property
    def contents(self):
        return dict(("{0};{1}".format(x.name.decode("ascii"), x.cycle).encode("ascii"), x.classname) for x in self.keys)

    @property
    def allcontents(self):
        out = {}
        for name, classname in self.contents.items():
            out[name] = classname
            if classname == b"TDirectory":
                for name2, classname2 in self.get(name).allcontents.items():
                    out["{0}/{1}".format(name[:name.rindex(b";")].decode("ascii"), name2.decode("ascii")).encode("ascii")] = classname2
        return out

    def get(self, name, cycle=None):
        """Get an object from the directory, interpreting '/' as subdirectories and ';' to delimit cycle number.

        Synonym for `dir[name]`.

        An explicit `cycle` overrides ';'.
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

            for key in self.keys:
                if key.name == name:
                    if cycle is None or key.cycle == cycle:
                        return key.get()
            raise KeyError("not found: {0}".format(repr(name)))

class StreamerInfo(object):
    def __init__(self, source, cursor, classes):
        print "HERE"

        start, cnt, vers = StreamedObject._startcheck(source, cursor)
        print "start, cnt, vers", start, cnt, vers

        name, title = _nametitle(source, cursor)

        print "name", repr(name), "title", repr(title)

        checksum, classvers = cursor.fields(source, struct.Struct("!Ii"))

        print "checksum", checksum, "classvers", classvers

        y = StreamedObject._read(source, cursor, classes)
        print "y", y

class StreamerElement(object):
    def __init__(self, source, cursor, classes):    
        start1, cnt1, vers1 = StreamedObject._startcheck(source, cursor)
        start2, cnt2, vers2 = StreamedObject._startcheck(source, cursor)
        
        self.name, self.title = _nametitle(source, cursor)

        self.etype, self.esize, self.arrlen, self.arrdim = cursor.fields(source, struct.Struct("!iiii"))

        if vers2 == 1:
            n = cursor.field(source, struct.Struct("!i"))
            self.maxidx = cursor.array(source, n, ">i4")
        else:
            self.maxidx = cursor.array(source, 5, ">i4")

        self.ename = cursor.string(source)

        # CHECK:
	# if tse.etype == 11 && (tse.ename == "Bool_t" || tse.ename == "bool") {
	# 	tse.etype = 18
	# }

        StreamedObject._endcheck(start2, cursor, cnt2)

        if vers1 > 2:
            self.vbase = cursor.field(source, struct.Struct("!i"))

        StreamedObject._endcheck(start1, cursor, cnt1)

class StreamedObject(object):
    """Base class for all objects extracted from a ROOT file using streamers.
    """

    def __init__(self, source, cursor, classes):
        pass

    def __repr__(self):
        if hasattr(self, "name"):
            return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, repr(self.name), id(self))
        else:
            return "<{0} at 0x{1:012x}>".format(self.__class__.__name__, id(self))

    _format_cntvers = struct.Struct("!IH")
    @staticmethod
    def _startcheck(source, cursor):
        start = cursor.index
        cnt, vers = cursor.fields(source, StreamedObject._format_cntvers)
        cnt = int(numpy.int64(cnt) & ~uproot.const.kByteCountMask)
        return start, cnt, vers

    @staticmethod
    def _endcheck(start, cursor, cnt):
        observed = cursor.index - start
        if observed != cnt + 4:
            raise ValueError("object has {0} bytes; expected {1}".format(observed, cnt + 4))

    @staticmethod
    def _read(source, cursor, classes):
        beg = cursor.index - cursor.origin
        bcnt = cursor.field(source, struct.Struct("!I"))

        print "beg", beg

        if numpy.int64(bcnt) & uproot.const.kByteCountMask == 0 or numpy.int64(bcnt) == uproot.const.kNewClassTag:
            vers = 0
            start = 0
            tag = bcnt
            bcnt = 0

            print "0 ->", tag, bcnt

        else:
            vers = 1
            start = cursor.index - cursor.origin
            tag = cursor.field(source, struct.Struct("!I"))

            print "1 ->", vers, start, tag

        if numpy.int64(tag) & uproot.const.kClassMask == 0:
            print "ONE", tag

            # reference object
            if tag == 0:
                return None                     # return null

            elif tag == 1:
                raise NotImplementedError("tag == 1 means self; not implemented yet")

            elif tag not in cursor.refs:
                # jump past this object
                cursor.index = cursor.origin + beg + bcnt + 4
                return None                     # return null

            else:
                return cursor.refs[tag]         # return object
            
        elif tag == uproot.const.kNewClassTag:
            print "TWO"

            # new class and object
            cname = cursor.cstring(source)

            print "cname", repr(cname)

            fct = classes.get(cname, Undefined)

            if vers > 0:
                cursor.refs[start + uproot.const.kMapOffset] = fct
            else:
                cursor.refs[len(cursor.refs) + 1] = fct

            obj = fct(source, cursor, classes)

            if vers > 0:
                cursor.refs[beg + uproot.const.kMapOffset] = obj
            else:
                cursor.refs[len(cursor.refs) + 1] = obj

            print "obj", obj
            return obj                          # return object

        else:
            print "THREE"

            # reference class, new object
            ref = int(numpy.int64(tag) & ~uproot.const.kClassMask)

            if ref not in cursor.refs:
                raise IOError("invalid class-tag reference")

            print "ref", ref, "cursor.refs", cursor.refs

            fct = cursor.refs[ref]              # reference class

            if fct not in Deserialized.classes.values():
                raise IOError("invalid class-tag reference (not a factory)")

            obj = fct(source, cursor, classes)  # new object

            if vers > 0:
                cursor.refs[beg + uproot.const.kMapOffset] = obj
            else:
                cursor.refs[len(cursor.refs) + 1] = obj

            print "obj", obj

            return obj                          # return object

class Undefined(StreamedObject):
    """Represents a ROOT class that we have no deserializer for (and therefore skip over).
    """
    def __init__(self, source, cursor, classes):
        start, cnt, vers = self._startcheck(source, cursor)
        cursor.skip(cnt - 2)
        self._endcheck(start, cursor, cnt)
