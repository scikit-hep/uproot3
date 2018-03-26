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

import numbers
import sys
from types import MethodType

import numpy

from uproot.interp.interp import Interpretation
from uproot.interp.jagged import asvar
from uproot.interp.jagged import JaggedArray
from uproot.interp.jagged import sizes2offsets
from uproot.interp.jagged import VariableLength

CHARTYPE = numpy.dtype(numpy.uint8)

def _asstrings_fromroot(data, offsets, local_entrystart, local_entrystop, skip_bytes, skip4_if_255):
    if local_entrystart < 0 or local_entrystop >= len(offsets) or local_entrystart > local_entrystop:
        raise ValueError("illegal local_entrystart or local_entrystop in asstrings.fromroot")

    content = numpy.empty(offsets[local_entrystop] - offsets[local_entrystart] - (local_entrystop - local_entrystart), dtype=CHARTYPE)
    newoffsets  = numpy.empty(1 + local_entrystop - local_entrystart, dtype=offsets.dtype)
    newoffsets[0] = 0

    start = stop = 0
    for entry in range(local_entrystart, local_entrystop):
        datastart = offsets[entry] + skip_bytes
        datastop = offsets[entry + 1]
        if skip4_if_255 and data[datastart - 1] == 255:
            datastart += 4

        stop = start + (datastop - datastart)

        content[start:stop] = data[datastart:datastop]
        newoffsets[1 + entry - local_entrystart] = stop

        start = stop

    return content[:stop], newoffsets[:-1], newoffsets[1:]

try:
    import numba
except ImportError:
    pass
else:
    _asstrings_fromroot = numba.njit(_asstrings_fromroot)

class asstrings(asvar):
    def __init__(self, skip_bytes=1, skip4_if_255=True):
        super(asstrings, self).__init__(Strings, skip_bytes=skip_bytes)
        self.skip4_if_255 = skip4_if_255

    @property
    def identifier(self):
        args = []
        if self.skip_bytes != 1:
            args.append("skip_bytes={0}".format(self.skip_bytes))
        if self.skip4_if_255 is not True:
            args.append("skip4_if_255={0}".format(self.skip4_if_255))
        return "asstrings({0})".format(", ".join(args))

    @property
    def dtype(self):
        return numpy.dtype(str)

    def compatible(self, other):
        return isinstance(other, asstrings) and self.skip4_if_255 == other.skip4_if_255 and super(asstrings, self).compatible(other)

    def fromroot(self, data, offsets, local_entrystart, local_entrystop):
        return Strings(JaggedArray(*_asstrings_fromroot(data, offsets, local_entrystart, local_entrystop, self.skip_bytes, self.skip4_if_255)))

class Strings(VariableLength):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    @staticmethod
    def fromstrs(strs):
        offsets = numpy.empty(len(strs) + 1, dtype=numpy.int64)
        offsets[0] = 0
        stop = 0
        for i, x in enumerate(strs):
            if not isinstance(x, bytes) or hasattr(x, "encode"):
                x = x.encode("utf-8", "replace")
            offsets[i + 1] = stop = stop + len(x)

        content = numpy.empty(offsets[-1], dtype=CHARTYPE)
        starts = offsets[:-1]
        stops = offsets[1:]

        if sys.version_info[0] <= 2:
            for i, x, in enumerate(strs):
                if isinstance(x, unicode):
                    x = x.encode("utf-8", "replace")
                content[starts[i]:stops[i]] = map(ord, x)
        else:
            for i, x, in enumerate(strs):
                if isinstance(x, str):
                    x = x.encode("utf-8", "replace")
                content[starts[i]:stops[i]] = memoryview(x)
            
        return Strings(uproot.types.jagged.JaggedArray(content, starts, stops))

    @staticmethod
    def interpret(item):
        return item.tostring()

    def __repr__(self):
        return "strings({0})".format(str(self))

def asstlvecstrings():
    return asvar(ListStrings, skip_bytes=10)

class ListStrings(VariableLength):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    indexdtype = numpy.dtype(">i4")

    @staticmethod
    def interpret(item):
        i = 0
        out = []
        while i < len(item):
            if item[i] < 255:
                size = item[i]
                i += 1
            else:
                i += 1
                size, = item[i : i + 4].view(ListStrings.indexdtype)
                i += 4
            out.append(item[i : i + size].tostring())
            i += size
        return out

    def __repr__(self):
        return "liststrings({0})".format(str(self))

    @classmethod
    def _dtype(cls, args):
        return numpy.dtype((object, (0,)))
