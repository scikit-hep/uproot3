#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import math
import struct

import numpy

class TFree(object):
    def __init__(self, fEND):
        self.fFirst = fEND
        self.fLast = int(math.ceil(fEND / 2000000000.0)) * 2000000000

    _format_big = struct.Struct(">hqq")
    _format_small = struct.Struct(">hii")

    def write(self, cursor, sink):
        if self.fLast > numpy.iinfo(numpy.int32).max:
            cursor.write_fields(sink, self._format_big, 1001, self.fFirst, self.fLast)
        else:
            cursor.write_fields(sink, self._format_small, 1, self.fFirst, self.fLast)

    def size(self):
        if self.fLast > numpy.iinfo(numpy.int32).max:
            return TFree._format_big.size
        else:
            return TFree._format_small.size
