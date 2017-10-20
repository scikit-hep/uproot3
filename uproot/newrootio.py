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
        self.compression = Compression(self.TFile.fCompress)

        self.dir = Directory(source, Cursor(self.TFile.fBEGIN), self.compression)

        source.dismiss()

    @property
    def name(self):
        return self.dir.name

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
    _format1       = struct.Struct("!ihiIhh")
    _format2_small = struct.Struct("!ii")
    _format2_big   = struct.Struct("!qq")

    def __init__(self, source, cursor, compression):
        vars1 = cursor.fields(source, self._format1)
        if vars1[1] <= 1000:
            vars2 = cursor.fields(source, self._format2_small)
        else:
            vars2 = cursor.fields(source, self._format2_big)

        vars3 = cursor.string(source)
        vars4 = cursor.string(source)
        if vars2[1] == 0:
            cursor.index += 1            # top TDirectory fName and fTitle
        vars5 = cursor.string(source)
        if vars2[1] == 0:
            cursor.index += 1            # are prefixed *and* null-terminated, both!

        self.compression = compression

        self.TKey = self._Private(*(vars1 + vars2 + (vars3, vars4, vars5)))

        if self.TKey.fObjlen != self.TKey.fNbytes - self.TKey.fKeylen:
            self.source = CompressedSource(compression, source, Cursor(self.TKey.fSeekKey + self.TKey.fKeylen), self.TKey.fNbytes - self.TKey.fKeylen, self.TKey.fObjlen)
            self.cursor = Cursor(0)
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
            return Directory(self.source, self.cursor.copied(), self.compression)
        else:
            return Undefined(self.source, self.cursor.copied())

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

    def __init__(self, source, cursor, compression):
        self.key = Key(source, cursor, compression)

        vars1 = cursor.fields(source, self._format1)
        if vars1[0] <= 1000:
            vars2 = cursor.fields(source, self._format2_small)
        else:
            vars2 = cursor.fields(source, self._format2_big)

        self.TDirectory = self._Private(*(vars1 + vars2))

        self.compression = compression

        cursor.index = self.TDirectory.fSeekKeys
        self.header = Key(source, cursor, compression)

        nkeys = cursor.field(source, self._format3)
        self.keys = [Key(source, cursor, compression) for i in range(nkeys)]

    @property
    def name(self):
        return self.key.name

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
