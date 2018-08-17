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

import sys
import numbers
import math

import numpy

import awkward.type

from uproot.interp.interp import Interpretation

if sys.version_info[0] <= 2:
    string_types = (unicode, str)
else:
    string_types = (str, bytes)

_byteorder = {"!": "B", ">": "B", "<": "L", "|": "L", "=": "B" if numpy.dtype(">f8").isnative else "L"}

def flatlen(obj):
    if isinstance(obj, numpy.dtype):
        return flatlen(numpy.empty((), obj))
    else:
        return int(numpy.prod(obj.shape))

class _asnumeric(Interpretation):
    @property
    def type(self):
        tmp = numpy.empty((), self.todtype)
        return awkward.type.ArrayType(*((numpy.inf,) + tmp.shape + (tmp.dtype,)))

    def empty(self):
        return numpy.empty(0, self.todtype)

    def source_numitems(self, source):
        return flatlen(source)

    def destination(self, numitems, numentries):
        quotient, remainder = divmod(numitems, flatlen(self.todtype))
        if remainder != 0:
            raise ValueError("cannot reshape {0} items as {1} (i.e. groups of {2})".format(numitems, self.todtype.shape, flatlen(self.todtype)))
        return numpy.empty(quotient, dtype=self.todtype)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        destination.reshape(-1)[itemstart:itemstop] = source.reshape(-1)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        length = flatlen(self.todtype)
        startquotient, startremainder = divmod(itemstart, length)
        stopquotient, stopremainder = divmod(itemstop, length)
        assert startremainder == 0
        assert stopremainder == 0
        return destination[startquotient:stopquotient]
        # FIXME: isn't the above equivalent to the following?
        #     return destination[entrystart:entrystop]

    def finalize(self, destination, branch):
        return destination

class asdtype(_asnumeric):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (_asnumeric.__metaclass__,), {})

    def __init__(self, fromdtype, todtype=None):
        if isinstance(fromdtype, numpy.dtype):
            self.fromdtype = fromdtype
        elif isinstance(fromdtype, string_types) and len(fromdtype) > 0 and fromdtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.fromdtype = numpy.dtype(fromdtype)
        else:
            self.fromdtype = numpy.dtype(fromdtype).newbyteorder(">")

        if todtype is None:
            self.todtype = self.fromdtype.newbyteorder("=")
        elif isinstance(todtype, numpy.dtype):
            self.todtype = todtype
        elif isinstance(todtype, string_types) and len(todtype) > 0 and todtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.todtype = numpy.dtype(todtype)
        else:
            self.todtype = numpy.dtype(todtype).newbyteorder("=")

    def to(self, todtype, toshape=()):
        return asdtype(self.fromdtype, numpy.dtype((todtype, toshape)))

    def toarray(self, array):
        return asarray(self.fromdtype, array)

    def __repr__(self):
        args = [repr(str(self.fromdtype))]
        if self.fromdtype.newbyteorder(">") != self.todtype.newbyteorder(">"):
            args.append(repr(str(self.todtype)))
        return "asdtype({0})".format(", ".join(args))

    @property
    def identifier(self):
        tmp = numpy.empty((), self.fromdtype)
        fromdtype = "{0}{1}{2}({3})".format(_byteorder[tmp.dtype.byteorder], tmp.dtype.kind, tmp.dtype.itemsize, ",".join(repr(x) for x in tmp.shape))
        tmp = numpy.empty((), self.todtype)
        todtype = "{0}{1}{2}({3})".format(_byteorder[tmp.dtype.byteorder], tmp.dtype.kind, tmp.dtype.itemsize, ",".join(repr(x) for x in tmp.shape))
        return "asdtype({0},{1})".format(fromdtype, todtype)

    def compatible(self, other):
        return isinstance(other, asdtype) and self.todtype == other.todtype

    def numitems(self, numbytes, numentries):
        quotient, remainder = divmod(numbytes, flatlen(self.todtype))
        assert remainder == 0
        return quotient

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        return data.view(self.fromdtype)[local_entrystart:local_entrystop]

class asarray(asdtype):
    pass

class asdouble32(_asnumeric):
    def compatible(self, other):
        return isinstance(other, asdouble32) and self.low == other.low and self.high == other.high and self.numbits == other.numbits and self.todtype == other.dtype

class asstlbitset(Interpretation):
    def compatible(self, other):
        return isinstance(other, asstlbitset) and self.numbytes == other.numbytes
