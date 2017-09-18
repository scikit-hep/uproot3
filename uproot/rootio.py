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

from collections import namedtuple

import numpy

import uproot.const
import uproot._walker.arraywalker
import uproot._walker.lazyarraywalker

from zlib import decompress as zlib_decompress
try:
    from lz4.block import decompress as lz4_decompress
except ImportError:
    def lz4_decompress(*args, **kwds):
        raise ImportError("\n\nInstall lz4 package with:\n\n    pip install lz4 --user\nor\n    conda install -c anaconda lz4\n\nand restart Python.")

try:
    from lzma import decompress as lzma_decompress
except ImportError:
    try:
        from backports.lzma import decompress as lzma_decompress
    except ImportError:
        def lzma_decompress(*args, **kwds):
            raise ImportError("\n\nInstall lzma package with:\n\n    pip install backports.lzma --user\nor\n    conda install -c conda-forge backports.lzma\n\nand restart Python (or just use Python >= 3.3).")

Compression = namedtuple("Compression", ["algo", "level"])

def _interpret_compression(compression):
    if compression // 100 <= 1:
        return Compression("zlib", compression % 100)

    elif compression // 100 == 2:
        return Compression("lzma", compression % 100)

    elif compression // 100 == 3:
        return Compression("old", compression % 100)

    elif compression // 100 == 4:
        return Compression("lz4", compression % 100)

    else:
        return Compression("unknown", compression % 100)

def _decompressfcn(compression, objlen):
    algo, level = compression
    if algo == "zlib":
        # skip 9-byte header for ROOT's custom frame:
        # https://github.com/root-project/root/blob/master/core/zip/src/Bits.h#L646
        return lambda x: zlib_decompress(x[9:])

    elif algo == "lzma":
        # skip 9-byte header for LZMA, too:
        # https://github.com/root-project/root/blob/master/core/lzma/src/ZipLZMA.c#L81
        return lambda x: lzma_decompress(x[9:])

    elif algo == "lz4":
        # skip 9-byte header plus 8-byte hash: are there any official ROOT versions without the hash?
        # https://github.com/root-project/root/blob/master/core/lz4/src/ZipLZ4.cxx#L38
        return lambda x: lz4_decompress(x[9 + 8:], uncompressed_size=objlen)

    else:
        raise NotImplementedError("cannot decompress \"{0}\"".format(algo))

class TFile(object):
    """Represents a ROOT file; use to extract objects.

        * `file.get(name, cycle=None)` to extract an object (aware of '/' and ';' notations).
        * `file.contents` is a `{name: classname}` dict of objects in the top directory.
        * `file.allcontents` is a `{name: classname}` dict of all objects in the file.
        * `file.compression` is a Compression(algo, level) namedtuple describing the compression.
        * `file.dir` is the top directory.

    `file[name]` is a synonym for `file.get(name)`.

    TFile is iterable (iterate over keys) with a `len(file)` for the number of keys.
    """

    def __init__(self, walker):
        walker.startcontext()
        if walker.readfield("!4s") != b"root":
            raise IOError("not a ROOT file (wrong magic bytes)")

        version, begin = walker.readfields("!ii")

        if version < 1000000:  # small file
            end, seekfree, nbytesfree, nfree, nbytesname, units, compression, seekinfo, nbytesinfo = walker.readfields("!iiiiiBiii")
        else:                  # big file
            end, seekfree, nbytesfree, nfree, nbytesname, units, compression, seekinfo, nbytesinfo = walker.readfields("!qqiiiBiqi")
        version %= 1000000

        self.compression = _interpret_compression(compression)

        uuid = walker.readfield("!18s")

        recordSize = 2 + 4 + 4 + 4 + 4   # fVersion, ctime, mtime, nbyteskeys, nbytesname
        if version >= 40000:
            recordSize += 8 + 8 + 8      # seekdir, seekparent, seekkeys
        else:
            recordSize += 4 + 4 + 4      # seekdir, seekparent, seekkeys

        nbytes = nbytesname + recordSize

        if nbytes + begin > end:
            raise IOError("TDirectory header length")

        self.dir = TDirectory(walker.path, walker.copy(begin + nbytesname), self.compression)

    def __del__(self):
        del self.dir

    def __repr__(self):
        return "<TFile {0} at 0x{1:012x}>".format(repr(self.dir.name), id(self))

    def __getitem__(self, name):
        return self.get(name)

    def __len__(self):
        return len(self.dir.keys)

    def __iter__(self):
        return iter(self.dir.keys)

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

class TDirectory(object):
    """Represents a ROOT directory; use to extract objects.

        * `dir.get(name, cycle=None)` to extract an object (aware of '/' and ';' notations).
        * `dir.contents` is a `{name: classname}` dict of objects in this directory.
        * `dir.allcontents` is a `{name: classname}` dict of all objects under this directory.
        * `dir.keys` is the keys.

    `dir[name]` is a synonym for `dir.get(name)`.

    TDirectory is iterable (iterate over keys) with a `len(dir)` for the number of keys.
    """
    def __init__(self, name, walker, compression):
        self.name = name

        walker.startcontext()
        version, ctime, mtime = walker.readfields("!hII")
        nbyteskeys, nbytesname = walker.readfields("!ii")

        if version <= 1000:
            seekdir, seekparent, seekkeys = walker.readfields("!iii")
        else:
            seekdir, seekparent, seekkeys = walker.readfields("!qqq")

        self.keys = TKeys(walker.copy(seekkeys), compression)

    def __del__(self):
        del self.keys

    def __repr__(self):
        return "<TDirectory {0} at 0x{1:012x}>".format(repr(self.name), id(self))

    def __getitem__(self, name):
        return self.get(name)

    def __len__(self):
        return len(self.keys)

    def __iter__(self):
        return iter(self.keys)

    @property
    def contents(self):
        return self.keys.contents

    @property
    def allcontents(self):
        return self.keys.allcontents

    def get(self, name, cycle=None):
        """Get an object from the directory, interpreting '/' as subdirectories and ';' to delimit cycle number.

        Synonym for `dir[name]`.

        An explicit `cycle` overrides ';'.
        """
        out = self
        for n in name.split("/"):
            out = out.keys.get(n, cycle)
        return out

class TKeys(object):
    """Represents a collection of keys.

        * `keys.get(name, cycle=None)` to extract an object (aware of ';' notation).
        * `keys.contents` is a `{name: classname}` dict of objects directly in this set of TKeys.
        * `keys.allcontents` is a `{name: classname}` dict of all objects under this set of TKeys.

    `keys[name]` is a synonym for `keys.get(name)`.

    TKeys is iterable (iterate over keys) with a `len(keys)` for the number of keys.
    """
    def __init__(self, walker, compression):
        start = walker.index
        self._header = TKey(walker, compression)
        walker.index = start + self._header._keylen

        walker.startcontext()
        nkeys = walker.readfield("!i")

        self.keys = [TKey(walker, compression) for i in range(nkeys)]

    def __del__(self):
        del self.keys

    def __repr__(self):
        return "<TKeys len={0} at 0x{1:012x}>".format(len(self.keys), id(self))

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
        """Get a `{name: classname}` dict of objects directly in this set of TKeys.
        """
        out = {}
        for name, classname in self.contents.items():
            out[name] = classname
            if classname == b"TDirectory":
                for name2, classname2 in self.get(name).allcontents.items():
                    out["{0}/{1}".format(name[:name.rindex(b";")].decode("ascii"), name2.decode("ascii")).encode("ascii")] = classname2
        return out

    def get(self, name, cycle=None):
        """Get an object from the keys, interpreting ';' to delimit cycle number.

        An explicit `cycle` overrides ';'.
        """
        if isinstance(name, str):
            name = name.encode("ascii")

        if cycle is None and b";" in name:
            at = name.rindex(b";")
            name, cycle = name[:at], name[at + 1:]
            cycle = int(cycle)

        for key in self.keys:
            if key.name == name:
                if cycle is None or key.cycle == cycle:
                    return key.get()
        raise KeyError("not found: {0}".format(repr(name)))

class TKey(object):
    """Represents a key; for seeking to an object in a ROOT file.

        * `key.get()` to extract an object (initiates file-reading and possibly decompression).
        * `key.classname` for the class name.
        * `key.name` for the object name.
        * `key.title` for the object title.
    """
    def __init__(self, walker, compression):
        walker.startcontext()
        bytes, version, objlen, datetime, self._keylen, self.cycle = walker.readfields("!ihiIhh")
        
        if version > 1000:
            seekkey, seekpdir = walker.readfields("!qq")
        else:
            seekkey, seekpdir = walker.readfields("!ii")

        self.classname = walker.readstring()
        self.name = walker.readstring()
        self.title = walker.readstring()

        self._filewalker = walker
        self._compression = compression

        #  object size != compressed size means it's compressed
        if objlen != bytes - self._keylen:
            function = _decompressfcn(self._compression, objlen)
            self._walker = uproot._walker.lazyarraywalker.LazyArrayWalker(walker.copy(seekkey + self._keylen), function, bytes - self._keylen, origin=-self._keylen)

        # otherwise, it's uncompressed
        else:
            self._walker = walker.copy(seekkey + self._keylen, seekkey)

    def __del__(self):
        del self._filewalker
        del self._walker

    def __repr__(self):
        return "<TKey {0} at 0x{1:012x}>".format(repr(self.name + b";" + repr(self.cycle).encode("ascii")), id(self))

    def get(self):
        """Extract the object this key points to.

        Objects are not read or decompressed until this function is explicitly called.
        """
        start = self._walker.index

        try:
            if self.classname == b"TDirectory":
                out = TDirectory(self.name, self._walker, self._compression)
            elif self.classname in Deserialized.classes:
                out = Deserialized.classes[self.classname](self._filewalker, self._walker)
            else:
                raise NotImplementedError("class not recognized: {0}".format(self.classname))
        finally:
            self._walker.index = start

        return out

class Deserialized(object):
    """Superclass for all types that can be deserialized from a ROOT file.

        * `Deserialized.classes` is a dictionary from class names (as written in the file) to Python classes that can hold their data.

    This is an abstract base class; it can't be instantiated.
    """

    classes = {}

    def __init__(self, *args, **kwds):
        raise TypeError("Deserialized is an abstract class")

    @staticmethod
    def _deserialize(filewalker, walker):
        walker.startcontext()
        beg = walker.index - walker.origin
        bcnt = walker.readfield("!I")

        if numpy.int64(bcnt) & uproot.const.kByteCountMask == 0 or numpy.int64(bcnt) == uproot.const.kNewClassTag:
            vers = 0
            start = 0
            tag = bcnt
            bcnt = 0
        else:
            vers = 1
            start = walker.index - walker.origin
            tag = walker.readfield("!I")

        if numpy.int64(tag) & uproot.const.kClassMask == 0:
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
            
        elif tag == uproot.const.kNewClassTag:
            # new class and object
            cname = walker.readcstring()

            if cname not in Deserialized.classes:
                raise NotImplementedError("class not recognized: {0}".format(cname))

            fct = Deserialized.classes[cname]

            if vers > 0:
                walker.refs[start + uproot.const.kMapOffset] = fct
            else:
                walker.refs[len(walker.refs) + 1] = fct

            obj = fct(filewalker, walker)

            if vers > 0:
                walker.refs[beg + uproot.const.kMapOffset] = obj
            else:
                walker.refs[len(walker.refs) + 1] = obj

            return obj                     # return object

        else:
            # reference class, new object
            ref = int(numpy.int64(tag) & ~uproot.const.kClassMask)

            if ref not in walker.refs:
                raise IOError("invalid class-tag reference")

            fct = walker.refs[ref]         # reference class

            if fct not in Deserialized.classes.values():
                raise IOError("invalid class-tag reference (not a factory)")

            obj = fct(filewalker, walker)  # new object

            if vers > 0:
                walker.refs[beg + uproot.const.kMapOffset] = obj
            else:
                walker.refs[len(walker.refs) + 1] = obj

            return obj                     # return object

    def _checkbytecount(self, observed, expected):
        if observed != expected + 4:
            raise IOError("{0} byte count".format(self.__class__.__name__))

    def __repr__(self):
        if hasattr(self, "name"):
            return "<{0} at 0x{1:012x}>".format(self.__class__.__name__, id(self))
        else:
            return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, repr(self.name), id(self))
