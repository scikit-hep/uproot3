#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from __future__ import absolute_import

import struct
from copy import copy

import numpy

import uproot.const
import uproot.write.compress
import uproot.write.sink.cursor

class TObjString(object):
    def __init__(self, string):
        if isinstance(string, bytes):
            self.value = string
        else:
            self.value = string.encode("utf-8")

    fClassName = b"TObjString"
    fTitle = b"Collectable string class"

    _format = struct.Struct(">IHHII")

    def write(self, context, cursor, name, compression, key, keycursor):
        write_cursor = copy(cursor)
        cnt = numpy.int64(self.length(name) - 4) | uproot.const.kByteCountMask
        vers = 1
        givenbytes = cursor.return_fields(self._format, cnt, vers, 1, 0, uproot.const.kNotDeleted) + cursor.return_string(self.value)
        uproot.write.compress.write(context, write_cursor, givenbytes, compression, key, keycursor)

    def length(self, name):
        return self._format.size + uproot.write.sink.cursor.Cursor.length_string(self.value)
