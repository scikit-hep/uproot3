#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct

import numpy

import uproot.const
import uproot.write.sink.cursor
from uproot.write.compress import write_compressed

class TObjString(object):
    def __init__(self, string):
        if isinstance(string, bytes):
            self.value = string
        else:
            self.value = string.encode("utf-8")

    fClassName = b"TObjString"
    fTitle = b"Collectable string class"

    _format = struct.Struct(">IHHII")

    def write(self, context, cursor, name, algorithm, level, key, keycursor):
        sink = context._sink
        cnt = numpy.int64(self.length(name) - 4) | uproot.const.kByteCountMask
        vers = 1
        givenbytes = cursor.return_fields(self._format, cnt, vers, 1, 0, uproot.const.kNotDeleted) + cursor.return_string(self.value)
        _ = write_compressed(context, cursor, givenbytes, algorithm, level, key, keycursor)

    def length(self, name):
        return self._format.size + uproot.write.sink.cursor.Cursor.length_string(self.value)
