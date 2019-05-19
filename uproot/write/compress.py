#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct
import uproot

def write_compressed(context, cursor, givenbytes, algorithm, level, key, keycursor):
    if level > 9:
        level = 9
    if algorithm == 0 or level == 0:
        cursor.write_data(context._sink, givenbytes)
        return
    _header = struct.Struct("2sBBBBBBB")
    uncompressedbytes = len(givenbytes)
    u1 = (uncompressedbytes >> 0) & 0xff
    u2 = (uncompressedbytes >> 8) & 0xff
    u3 = (uncompressedbytes >> 16) & 0xff
    if algorithm == uproot.const.kZLIB:
        algo = b"ZL"
        import zlib
        compressedbytes = len(zlib.compress(givenbytes, level))
        if compressedbytes < uncompressedbytes:
            c1 = (compressedbytes >> 0) & 0xff
            c2 = (compressedbytes >> 8) & 0xff
            c3 = (compressedbytes >> 16) & 0xff
            method = 8
            cursor.write_fields(context._sink, _header, algo, method, c1, c2, c3, u1, u2, u3)
            cursor.write_data(context._sink, zlib.compress(givenbytes, level))
            key.fNbytes = compressedbytes + key.fKeylen + 9
            key.write(keycursor, context._sink)
        else:
            cursor.write_data(context._sink, givenbytes)
    elif algorithm == uproot.const.kLZ4:
        raise NotImplementedError
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
        compressedbytes = len(lzma.compress(givenbytes, preset=level))
        if compressedbytes < uncompressedbytes:
            c1 = (compressedbytes >> 0) & 0xff
            c2 = (compressedbytes >> 8) & 0xff
            c3 = (compressedbytes >> 16) & 0xff
            method = 0
            cursor.write_fields(context._sink, _header, algo, method, c1, c2, c3, u1, u2, u3)
            cursor.write_data(context._sink, lzma.compress(givenbytes, preset=level))
            key.fNbytes = compressedbytes + key.fKeylen + 9
            key.write(keycursor, context._sink)
        else:
            cursor.write_data(context._sink, givenbytes)
    elif algorithm == uproot.const.kOldCompressionAlgo:
        raise ValueError("unsupported compression algorithm: 'old' (according to ROOT comments, hasn't been used in 20+ years!)")
    else:
        raise ValueError("Unrecognized compression algorithm: {0}".format(algorithm))
