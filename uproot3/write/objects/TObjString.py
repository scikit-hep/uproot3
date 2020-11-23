#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

from __future__ import absolute_import

import struct
from copy import copy

import numpy

import uproot3.const
import uproot3.write.compress
import uproot3.write.sink.cursor

class TObjString(object):
    def __init__(self, string):
        if isinstance(string, bytes):
            self.value = string
        else:
            self.value = string.encode("utf-8")

    _fClassName = b"TObjString"
    _fTitle = b"Collectable string class"

    _format = struct.Struct(">IHHII")

    def _write(self, context, cursor, name, compression, key, keycursor, util):
        copy_cursor = copy(cursor)
        write_cursor = copy(cursor)
        cursor.skip(self._format.size)
        vers = 1
        buff = cursor.put_string(self.value)
        length = len(buff) + self._format.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        givenbytes = copy_cursor.put_fields(self._format, cnt, vers, 1, 0, uproot3.const.kNotDeleted) + buff
        uproot3.write.compress.write(context, write_cursor, givenbytes, compression, key, keycursor)
