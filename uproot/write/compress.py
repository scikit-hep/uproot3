#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from __future__ import absolute_import

import numbers
import struct
import copy

import numpy

import uproot
import uproot.const

class Compression(object):
    def __init__(self, level):
        self.level = level

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, self.level)

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        if not isinstance(value, (numbers.Integral, numpy.integer)):
            raise TypeError("Compression level must be an integer")
        if not 0 <= value <= 9:
            raise ValueError("Compression level must be between 0 and 9 (inclusive)")
        self._level = int(value)
    
    @property
    def pair(self):
        for const, cls in algo.items():
            if type(self) is cls:
                return const, self.level
        else:
            raise AssertionError(type(self))

    @property
    def code(self):
        algorithm, level = self.pair
        return algorithm * 100 + level

class ZLIB(Compression): pass
class LZMA(Compression): pass
class LZ4(Compression): pass

algo = {uproot.const.kZLIB: ZLIB,
        uproot.const.kLZMA: LZMA,
        uproot.const.kLZ4: LZ4}

def write(context, cursor, givenbytes, compression, key, keycursor):
    retaincursor = copy.copy(keycursor)
    if compression is None:
        algorithm, level = 0, 0
    else:
        algorithm, level = compression.pair

    _header = struct.Struct("2sBBBBBBB")
    uncompressedbytes = len(givenbytes)

    if algorithm == 0 or level == 0:
        key.fObjlen = uncompressedbytes
        key.fNbytes = key.fObjlen + key.fKeylen
        key.write(keycursor, context._sink)
        cursor.write_data(context._sink, givenbytes)
        return

    if uncompressedbytes > 2**24:
        uncompressedbytes = 2**24 - 1
        remainingbytes = givenbytes[2**24 - 1:]
        givenbytes = givenbytes[:2**24 - 1]

    key.fObjlen += uncompressedbytes

    u1 = (uncompressedbytes >> 0) & 0xff
    u2 = (uncompressedbytes >> 8) & 0xff
    u3 = (uncompressedbytes >> 16) & 0xff

    if algorithm == uproot.const.kZLIB:
        algo = b"ZL"
        import zlib
        after_compressed = zlib.compress(givenbytes, level)
        compressedbytes = len(after_compressed)
        if (compressedbytes + 9) < uncompressedbytes:
            c1 = (compressedbytes >> 0) & 0xff
            c2 = (compressedbytes >> 8) & 0xff
            c3 = (compressedbytes >> 16) & 0xff
            method = 8
            cursor.write_fields(context._sink, _header, algo, method, c1, c2, c3, u1, u2, u3)
            cursor.write_data(context._sink, after_compressed)
            key.fNbytes += compressedbytes + 9
            key.write(keycursor, context._sink)
        else:
            key.fNbytes += uncompressedbytes
            key.write(keycursor, context._sink)
            cursor.write_data(context._sink, givenbytes)

    elif algorithm == uproot.const.kLZ4:
        algo = b"L4"
        try:
            import xxhash
        except ImportError:
            raise ImportError("Install xxhash package with:\n    pip install xxhash\nor\n    conda install -c conda-forge python-xxhash")
        try:
            import lz4.block
        except ImportError:
            raise ImportError("Install lz4 package with:\n    pip install lz4\nor\n    conda install -c anaconda lz4")
        if level >= 4:
            after_compressed = lz4.block.compress(givenbytes, compression=level, mode="high_compression", store_size=False)
        else:
            after_compressed = lz4.block.compress(givenbytes, store_size=False)
        compressedbytes = len(after_compressed) + 8
        checksum = xxhash.xxh64(after_compressed).digest()
        if (compressedbytes + 9) < uncompressedbytes:
            c1 = (compressedbytes >> 0) & 0xff
            c2 = (compressedbytes >> 8) & 0xff
            c3 = (compressedbytes >> 16) & 0xff
            method = lz4.library_version_number() // (100 * 100)
            cursor.write_fields(context._sink, _header, algo, method, c1, c2, c3, u1, u2, u3)
            cursor.write_data(context._sink, checksum)
            cursor.write_data(context._sink, after_compressed)
            key.fNbytes += compressedbytes + 9
            key.write(keycursor, context._sink)
        else:
            key.fNbytes += uncompressedbytes
            key.write(keycursor, context._sink)
            cursor.write_data(context._sink, givenbytes)

    elif algorithm == uproot.const.kLZMA:
        algo = b"XZ"
        try:
            import lzma
        except ImportError:
            try:
                from backports import lzma
            except ImportError:
                raise ImportError(
                    "Install lzma package with:\n    pip install backports.lzma\nor\n    conda install -c conda-forge backports.lzma\n(or just use Python >= 3.3).")
        after_compressed = lzma.compress(givenbytes, preset=level)
        compressedbytes = len(after_compressed)
        if (compressedbytes + 9) < uncompressedbytes:
            c1 = (compressedbytes >> 0) & 0xff
            c2 = (compressedbytes >> 8) & 0xff
            c3 = (compressedbytes >> 16) & 0xff
            method = 0
            cursor.write_fields(context._sink, _header, algo, method, c1, c2, c3, u1, u2, u3)
            cursor.write_data(context._sink, after_compressed)
            key.fNbytes += compressedbytes + 9
            key.write(keycursor, context._sink)
        else:
            key.fNbytes += uncompressedbytes
            key.write(keycursor, context._sink)
            cursor.write_data(context._sink, givenbytes)

    elif algorithm == uproot.const.kOldCompressionAlgo:
        raise ValueError("unsupported compression algorithm: 'old' (according to ROOT comments, hasn't been used in 20+ years!)")
    else:
        raise ValueError("Unrecognized compression algorithm: {0}".format(algorithm))

    if "remainingbytes" in locals() and len(remainingbytes)>0:
        uproot.write.compress.write(context, cursor, remainingbytes, compression, key, retaincursor)
