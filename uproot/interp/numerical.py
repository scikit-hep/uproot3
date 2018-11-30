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

import awkward.type
import awkward.util

import uproot.interp.interp

if sys.version_info[0] <= 2:
    string_types = (unicode, str)
else:
    string_types = (str, bytes)

def _dtypeshape(obj):
    out = ()
    while obj.subdtype is not None:
        obj, shape = obj.subdtype
        out = out + shape
    return obj, out

def _flatlen(obj):
    if isinstance(obj, awkward.util.numpy.dtype):
        dtype, shape = _dtypeshape(obj)
        return int(awkward.util.numpy.prod(shape))
    else:
        return int(awkward.util.numpy.prod(obj.shape))

class _asnumeric(uproot.interp.interp.Interpretation):
    @property
    def todtypeflat(self):
        return _dtypeshape(self.todtype)[0]

    @property
    def todims(self):
        return _dtypeshape(self.todtype)[1]

    @property
    def type(self):
        dtype, shape = _dtypeshape(self.todtype)
        if shape == ():
            return dtype
        else:
            return awkward.type.ArrayType(*(shape + (dtype,)))

    def empty(self):
        return awkward.util.numpy.empty(0, self.todtype)

    def source_numitems(self, source):
        return _flatlen(source)

    def destination(self, numitems, numentries):
        quotient, remainder = divmod(numitems, _flatlen(self.todtype))
        if remainder != 0:
            raise ValueError("cannot reshape {0} items as {1} (i.e. groups of {2})".format(numitems, self.todtype.shape, _flatlen(self.todtype)))
        return awkward.util.numpy.empty(quotient, dtype=self.todtype)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        destination.reshape(-1)[itemstart:itemstop] = source.reshape(-1)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        length = _flatlen(self.todtype)
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
        if isinstance(fromdtype, awkward.util.numpy.dtype):
            self.fromdtype = fromdtype
        elif isinstance(fromdtype, string_types) and len(fromdtype) > 0 and fromdtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.fromdtype = awkward.util.numpy.dtype(fromdtype)
        else:
            self.fromdtype = awkward.util.numpy.dtype(fromdtype).newbyteorder(">")

        if todtype is None:
            self.todtype = self.fromdtype.newbyteorder("=")
        elif isinstance(todtype, awkward.util.numpy.dtype):
            self.todtype = todtype
        elif isinstance(todtype, string_types) and len(todtype) > 0 and todtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.todtype = awkward.util.numpy.dtype(todtype)
        else:
            self.todtype = awkward.util.numpy.dtype(todtype).newbyteorder("=")

    @property
    def itemsize(self):
        return self.fromdtype.itemsize

    def to(self, todtype=None, todims=None):
        if todtype is None:
            dtype, shape = _dtypeshape(self.todtype)
            if todims is not None:
                shape = todims
        else:
            dtype, shape = _dtypeshape(todtype)
            if todims is not None:
                shape = todims + shape

        return asdtype(self.fromdtype, awkward.util.numpy.dtype((dtype, shape)))

    def toarray(self, array):
        return asarray(self.fromdtype, array)

    def __repr__(self):
        args = [repr(str(self.fromdtype))]
        if self.fromdtype.newbyteorder(">") != self.todtype.newbyteorder(">"):
            args.append(repr(str(self.todtype)))
        return "asdtype({0})".format(", ".join(args))

    @property
    def identifier(self):
        _byteorder = {"!": "B", ">": "B", "<": "L", "|": "L", "=": "B" if awkward.util.numpy.dtype(">f8").isnative else "L"}
        dtype, shape = _dtypeshape(self.fromdtype)
        fromdtype = "{0}{1}{2}({3})".format(_byteorder[dtype.byteorder], dtype.kind, dtype.itemsize, ",".join(repr(x) for x in shape))
        dtype, shape = _dtypeshape(self.todtype)
        todtype = "{0}{1}{2}({3})".format(_byteorder[dtype.byteorder], dtype.kind, dtype.itemsize, ",".join(repr(x) for x in shape))
        return "asdtype({0},{1})".format(fromdtype, todtype)

    def compatible(self, other):
        return isinstance(other, asdtype) and self.todtype == other.todtype

    def numitems(self, numbytes, numentries):
        dtype, shape = _dtypeshape(self.fromdtype)
        quotient, remainder = divmod(numbytes, dtype.itemsize)
        assert remainder == 0
        return quotient

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        dtype, shape = _dtypeshape(self.fromdtype)
        return data.view(dtype).reshape((-1,) + shape)[local_entrystart:local_entrystop]

class asarray(asdtype):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (asdtype.__metaclass__,), {})

    def __init__(self, fromdtype, toarray):
        if isinstance(fromdtype, awkward.util.numpy.dtype):
            self.fromdtype = fromdtype
        elif isinstance(fromdtype, string_types) and len(fromdtype) > 0 and fromdtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.fromdtype = awkward.util.numpy.dtype(fromdtype)
        else:
            self.fromdtype = awkward.util.numpy.dtype(fromdtype).newbyteorder(">")
        self.toarray = toarray

    @property
    def todtype(self):
        return awkward.util.numpy.dtype((self.toarray.dtype, self.toarray.shape[1:]))

    def __repr__(self):
        return "asarray({0}, <array {1} {2} at 0x{3:012x}>)".format(repr(str(self.fromdtype)), self.toarray.dtype, self.toarray.shape, id(self.toarray))

    @property
    def identifier(self):
        return "asarray" + super(asarray, self).identifier[7:]

    def destination(self, numitems, numentries):
        quotient, remainder = divmod(numitems, _flatlen(self.todtype))
        if remainder != 0:
            raise ValueError("cannot reshape {0} items as {1} (i.e. groups of {2})".format(numitems, self.todtype.shape, _flatlen(self.todtype)))
        if _flatlen(self.toarray) < numitems:
            raise ValueError("cannot put {0} items into an array of {1} items".format(numitems, _flatlen(self.toarray)))
        return self.toarray, quotient

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        array, stop = destination
        super(asarray, self).fill(source, array, itemstart, itemstop, entrystart, entrystop)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        array, stop = destination
        return super(asarray, self).clip(array, itemstart, itemstop, entrystart, entrystop), stop

    def finalize(self, destination, branch):
        array, stop = destination
        return array[:stop]

class asdouble32(_asnumeric):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (_asnumeric.__metaclass__,), {})

    def __init__(self, low, high, numbits, fromdims=(), todims=None):
        if not isinstance(numbits, numbers.Integral) or not 2 <= numbits <= 32:
            raise TypeError("numbits must be an integer between 2 and 32 (inclusive)")
        if low == 0.0 and high == 0.0:
            raise NotImplementedError("Double32_t with dropped mantissa bits not yet implemented")
        if high <= low:
            raise ValueError("high ({0}) must be strictly greater than low ({1})".format(high, low))

        self.low = low
        self.high = high
        self.numbits = numbits

        self.fromdims = fromdims

        if todims is None:
            self._todims = todims
        else:
            self._todims = fromdims

    @property
    def todtype(self):
        return awkward.util.numpy.dtype((awkward.util.numpy.float64, self.todims))

    @property
    def todtypeflat(self):
        return awkward.util.numpy.dtype(awkward.util.numpy.float64)

    @property
    def todims(self):
        return self._todims

    @property
    def itemsize(self):
        return 4

    def __repr__(self):
        args = [repr(self.low), repr(self.high), repr(self.numbits)]

        if self.fromdims != ():
            args.append(repr(self.fromdims))

        if self.todims != self.fromdims:
            args.append(repr(self.todims))

        return "asdouble32(" + ", ".join(args) + ")"

    @property
    def identifier(self):
        fromdims = "(" + ",".join(repr(x) for x in self.fromdims) + ")"
        todims = "(" + ",".join(repr(x) for x in self.todims) + ")"
        return "asdouble32({0},{1},{2},{3},{4})".format(self.low, self.high, self.numbits, fromdims, todims)

    def compatible(self, other):
        return isinstance(other, asdouble32) and self.low == other.low and self.high == other.high and self.numbits == other.numbits and self.todtype == other.dtype

    def numitems(self, numbytes, numentries):
        quotient, remainder = divmod(numbytes, 4)
        assert remainder == 0
        return quotient

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        array = data.view(">u4")
        if self.fromdims != ():
            product = int(awkward.util.numpy.prod(self.fromdims))
            quotient, remainder = divmod(len(array), product)
            assert remainder == 0, "{0} % {1} == {2} != 0".format(len(array), product, len(array) % product)
            array = array.reshape((quotient,) + self.fromdims)

        array = array[local_entrystart:local_entrystop].astype(self.todtype)
        awkward.util.numpy.multiply(array, float(self.high - self.low) / (1 << self.numbits), out=array)
        awkward.util.numpy.add(array, self.low, out=array)
        return array

class asstlbitset(uproot.interp.interp.Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.interp.interp.Interpretation.__metaclass__,), {})

    todtype = awkward.util.numpy.dtype(awkward.util.numpy.bool_)

    def __init__(self, numbytes):
        self.numbytes = numbytes

    def __repr__(self):
        return self.identifier

    @property
    def identifier(self):
        return "asstlbitset({0})".format(self.numbytes)

    @property
    def type(self):
        return awkward.type.ArrayType(self.numbytes, self.todtype)

    def empty(self):
        return awkward.util.numpy.empty((0, self.numbytes), dtype=self.todtype)

    def compatible(self, other):
        return (isinstance(other, asstlbitset) and self.numbytes == other.numbytes) or \
               (isinstance(other, (asdtype, asarray)) and self.todtype == other.todtype and (self.numbytes,) == other.todims)

    def numitems(self, numbytes, numentries):
        return max(0, numbytes // (self.numbytes + 4))

    def source_numitems(self, source):
        return int(awkward.util.numpy.prod(source.shape))

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        return data.view(self.todtype).reshape((-1, self.numbytes + 4))[:, 4:]

    def destination(self, numitems, numentries):
        return awkward.util.numpy.empty((numitems, self.numbytes), dtype=self.todtype)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        destination[itemstart:itemstop] = source

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        return destination[itemstart:itemstop]

    def finalize(self, destination, branch):
        return destination
