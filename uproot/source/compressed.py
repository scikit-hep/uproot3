#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct

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
                    raise ImportError("Install lzma package with:\n    pip install backports.lzma\nor\n    conda install -c conda-forge backports.lzma\n(or just use Python >= 3.3).")
            return lzma_decompress(cursor.bytes(source, compressedbytes))

        elif self.algo == uproot.const.kOldCompressionAlgo:
            raise NotImplementedError("ROOT's \"old\" algorithm (fCompress 300) is not supported")

        elif self.algo == uproot.const.kLZ4:
            try:
                from lz4.block import decompress as lz4_decompress
            except ImportError:
                raise ImportError("Install lz4 package with:\n    pip install lz4\nor\n    conda install -c anaconda lz4")

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

    @property
    def path(self):
        return "(decompressed data)"

    def parent(self):
        return self._compressed

    def threadlocal(self):
        return self

    _header = struct.Struct("2sBBBBBBB")

    def _prepare(self):
        if self._uncompressed is None:
            cursor = self._cursor.copied()

            start = cursor.index
            filled = 0
            numblocks = 0
            while cursor.index - start < self._compressedbytes:
                # https://github.com/root-project/root/blob/master/core/zip/src/RZip.cxx#L217
                # https://github.com/root-project/root/blob/master/core/lzma/src/ZipLZMA.c#L81
                # https://github.com/root-project/root/blob/master/core/lz4/src/ZipLZ4.cxx#L38
                algo, method, c1, c2, c3, u1, u2, u3 = cursor.fields(self._compressed, self._header)
                compressedbytes = c1 + (c2 << 8) + (c3 << 16)
                uncompressedbytes = u1 + (u2 << 8) + (u3 << 16)

                if algo == b"ZL":
                    compression = self.compression.copy(uproot.const.kZLIB)
                elif algo == b"XZ":
                    compression = self.compression.copy(uproot.const.kLZMA)
                elif algo == b"L4":
                    compression = self.compression.copy(uproot.const.kLZ4)
                    cursor.skip(8)        # FIXME: use this checksum!
                    compressedbytes -= 8
                elif algo == b"CS":
                    raise ValueError("unsupported compression algorithm: 'old' (according to ROOT comments, hasn't been used in 20+ years!)")
                else:
                    raise ValueError("unrecognized compression algorithm: {0}".format(algo))

                asstr = compression.decompress(self._compressed, cursor, compressedbytes, uncompressedbytes)
                numblocks += 1

                if len(asstr) != uncompressedbytes:
                    raise ValueError("block with header {0} ({1}) decompressed to {2} bytes, but the object key says the decompressed size should be {3} bytes".format(repr(header), compression.algoname, len(asstr), self._uncompressedbytes))
                if filled + uncompressedbytes > self._uncompressedbytes:
                    raise ValueError("uncompressed {0} bytes in {1} blocks so far, but expected only {2} bytes".format(filled + uncompressedbytes, numblocks, self._uncompressedbytes))

                if filled == 0:
                    if uncompressedbytes == self._uncompressedbytes:  # usual case: only one block
                        self._uncompressed = numpy.frombuffer(asstr, dtype=numpy.uint8)
                        return
                    else:
                        self._uncompressed = numpy.empty(self._uncompressedbytes, dtype=numpy.uint8)

                self._uncompressed[filled : filled + uncompressedbytes] = numpy.frombuffer(asstr, dtype=numpy.uint8)
                filled += uncompressedbytes

    def size(self):
        self._prepare()
        return len(self._uncompressed)

    def data(self, start, stop, dtype=None):
        # assert start >= 0
        # assert stop >= 0
        # assert stop >= start

        self._prepare()
        if dtype is None:
            return self._uncompressed[start:stop]
        else:
            return self._uncompressed[start:stop].view(dtype)

    def dismiss(self):
        self._uncompressed = None
