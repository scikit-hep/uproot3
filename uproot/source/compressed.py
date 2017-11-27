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

import numpy

import uproot.const
import uproot.source.source

class Compression(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    def __init__(self, fCompress):
        self.algo = max(fCompress // 100, uproot.const.kZLIB)
        self.level = fCompress % 100
        if not uproot.const.kZLIB <= self.algo < uproot.const.kUndefinedCompressionAlgorithm:
            raise ValueError("unrecognized compression algorithm: {0} (from fCompress {1})".format(self.algo, fCompress))
        if not 0 <= self.level <= 9:
            raise ValueError("unrecognized compression level: {0} (from fCompress {1})".format(self.level, fCompress))

    def copy(self, algo=None, level=None):
        out = Compression.__new__(Compression)
        if algo is None:
            out.algo = self.algo
        else:
            out.algo = algo
        if level is None:
            out.level = self.level
        else:
            out.level = level
        return out

    @property
    def algoname(self):
        if self.algo == uproot.const.kZLIB:
            return "zlib"
        elif self.algo == uproot.const.kLZMA:
            return "lzma"
        elif self.algo == uproot.const.kOldCompressionAlgo:
            return "old"
        elif self.algo == uproot.const.kLZ4:
            return "lz4"
        else:
            raise ValueError("unrecognized compression algorithm: {0}".format(self.algo))

    def __repr__(self):
        return "<Compression {0} {1}>".format(repr(self.algoname), self.level)

    def decompress(self, source, cursor, compressedbytes, uncompressedbytes=None):
        if self.algo == uproot.const.kZLIB:
            from zlib import decompress as zlib_decompress
            return zlib_decompress(cursor.bytes(source, compressedbytes))

        elif self.algo == uproot.const.kLZMA:
            try:
                from lzma import decompress as lzma_decompress
            except ImportError:
                try:
                    from backports.lzma import decompress as lzma_decompress
                except ImportError:
                    raise ImportError("\n\nInstall lzma package with:\n\n    pip install backports.lzma --user\nor\n    conda install -c conda-forge backports.lzma\n\n(or just use Python >= 3.3).")
            return lzma_decompress(cursor.bytes(source, compressedbytes))

        elif self.algo == uproot.const.kOldCompressionAlgo:
            raise NotImplementedError("ROOT's \"old\" algorithm (fCompress 300) is not supported")

        elif self.algo == uproot.const.kLZ4:
            try:
                from lz4.block import decompress as lz4_decompress
            except ImportError:
                raise ImportError("\n\nInstall lz4 package with:\n\n    pip install lz4 --user\nor\n    conda install -c anaconda lz4")

            if uncompressedbytes is None:
                raise ValueError("lz4 needs to know the uncompressed number of bytes")
            return lz4_decompress(cursor.bytes(source, compressedbytes), uncompressed_size=uncompressedbytes)

        else:
            raise ValueError("unrecognized compression algorithm: {0}".format(self.algo))

class CompressedSource(uproot.source.source.Source):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.source.source.Source.__metaclass__,), {})

    def __init__(self, compression, source, cursor, compressedbytes, uncompressedbytes):
        self.compression = compression
        self._compressed = source
        self._uncompressed = None
        self._cursor = cursor
        self._compressedbytes = compressedbytes
        self._uncompressedbytes = uncompressedbytes

    def parent(self):
        return self._compressed

    def threadlocal(self):
        return self

    def data(self, start, stop, dtype=None):
        if self._uncompressed is None:
            cursor = self._cursor.copied()
            algo = self._compressed.data(cursor.index, cursor.index + 2).tostring()

            if algo == b"ZL":
                compression = self.compression.copy(uproot.const.kZLIB)
                skip = 9        # https://github.com/root-project/root/blob/master/core/zip/src/Bits.h#L646

            elif algo == b"XZ":
                compression = self.compression.copy(uproot.const.kLZMA)
                skip = 9        # https://github.com/root-project/root/blob/master/core/lzma/src/ZipLZMA.c#L81

            elif algo == b"L4":
                compression = self.compression.copy(uproot.const.kLZ4)
                skip = 9 + 8    # https://github.com/root-project/root/blob/master/core/lz4/src/ZipLZ4.cxx#L38

            else:
                raise ValueError("unrecognized compression algorithm: {0}".format(algo))

            self._uncompressed = numpy.frombuffer(compression.decompress(self._compressed, cursor.skipped(skip), self._compressedbytes - skip, self._uncompressedbytes), dtype=numpy.uint8)

        # assert start >= 0
        # assert stop >= 0
        # assert stop >= start

        if dtype is None:
            return self._uncompressed[start:stop]
        else:
            return self._uncompressed[start:stop].view(dtype)

    def dismiss(self):
        self._uncompressed = None
