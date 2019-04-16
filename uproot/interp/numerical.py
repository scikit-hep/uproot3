#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import sys
import numbers
import math

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

def _flatlen(obj, awkward):
    if isinstance(obj, awkward.numpy.dtype):
        dtype, shape = _dtypeshape(obj)
        return int(awkward.numpy.prod(shape))
    else:
        return int(awkward.numpy.prod(obj.shape))

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
            return self.awkward.type.ArrayType(*(shape + (dtype,)))

    def empty(self):
        return self.awkward.numpy.empty(0, self.todtype)

    def source_numitems(self, source):
        return _flatlen(source, self.awkward)

    def destination(self, numitems, numentries):
        quotient, remainder = divmod(numitems, _flatlen(self.todtype, self.awkward))
        if remainder != 0:
            raise ValueError("cannot reshape {0} items as {1} (i.e. groups of {2})".format(numitems, self.todtype.shape, _flatlen(self.todtype, self.awkward)))
        return self.awkward.numpy.empty(quotient, dtype=self.todtype)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        destination.reshape(-1)[itemstart:itemstop] = source.reshape(-1)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        length = _flatlen(self.todtype, self.awkward)
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
        if isinstance(fromdtype, self.awkward.numpy.dtype):
            self.fromdtype = fromdtype
        elif isinstance(fromdtype, string_types) and len(fromdtype) > 0 and fromdtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.fromdtype = self.awkward.numpy.dtype(fromdtype)
        else:
            self.fromdtype = self.awkward.numpy.dtype(fromdtype).newbyteorder(">")

        if todtype is None:
            self.todtype = self.fromdtype.newbyteorder("=")
        elif isinstance(todtype, self.awkward.numpy.dtype):
            self.todtype = todtype
        elif isinstance(todtype, string_types) and len(todtype) > 0 and todtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.todtype = self.awkward.numpy.dtype(todtype)
        else:
            self.todtype = self.awkward.numpy.dtype(todtype).newbyteorder("=")

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

        return asdtype(self.fromdtype, self.awkward.numpy.dtype((dtype, shape)))

    def toarray(self, array):
        return asarray(self.fromdtype, array)

    def __repr__(self):
        args = [repr(str(self.fromdtype))]
        if self.fromdtype.newbyteorder(">") != self.todtype.newbyteorder(">"):
            args.append(repr(str(self.todtype)))
        return "asdtype({0})".format(", ".join(args))

    @property
    def identifier(self):
        _byteorder = {"!": "B", ">": "B", "<": "L", "|": "L", "=": "B" if self.awkward.numpy.dtype(">f8").isnative else "L"}
        def form(dt, n):
            dtype, shape = _dtypeshape(dt)
            return "{0}{1}{2}({3}{4})".format(_byteorder[dtype.byteorder], dtype.kind, dtype.itemsize, ",".join(repr(x) for x in shape), n)

        if self.fromdtype.names is None:
            fromdtype = form(self.fromdtype, "")
        else:
            fromdtype = "[" + ",".join(form(self.fromdtype[n], "," + repr(n)) for n in self.fromdtype.names) + "]"

        if self.todtype.names is None:
            todtype = form(self.todtype, "")
        else:
            todtype = "[" + ",".join(form(self.todtype[n], "," + repr(n)) for n in self.todtype.names) + "]"

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
        if isinstance(fromdtype, self.awkward.numpy.dtype):
            self.fromdtype = fromdtype
        elif isinstance(fromdtype, string_types) and len(fromdtype) > 0 and fromdtype[0] in (">", "<", "=", "|", b">", b"<", b"=", b"|"):
            self.fromdtype = self.awkward.numpy.dtype(fromdtype)
        else:
            self.fromdtype = self.awkward.numpy.dtype(fromdtype).newbyteorder(">")
        self.toarray = toarray

    @property
    def todtype(self):
        return self.awkward.numpy.dtype((self.toarray.dtype, self.toarray.shape[1:]))

    def __repr__(self):
        return "asarray({0}, <array {1} {2} at 0x{3:012x}>)".format(repr(str(self.fromdtype)), self.toarray.dtype, self.toarray.shape, id(self.toarray))

    @property
    def identifier(self):
        return "asarray" + super(asarray, self).identifier[7:]

    def destination(self, numitems, numentries):
        quotient, remainder = divmod(numitems, _flatlen(self.todtype, self.awkward))
        if remainder != 0:
            raise ValueError("cannot reshape {0} items as {1} (i.e. groups of {2})".format(numitems, self.todtype.shape, _flatlen(self.todtype, self.awkward)))
        if _flatlen(self.toarray, self.awkward) < numitems:
            raise ValueError("cannot put {0} items into an array of {1} items".format(numitems, _flatlen(self.toarray, self.awkward)))
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
        self.truncated = low == 0.0 and high == 0.0
        if high <= low and not self.truncated:
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
        return self.awkward.numpy.dtype((self.awkward.numpy.float64, self.todims))

    @property
    def fromdtype(self):
        if self.truncated:
            return self.awkward.numpy.dtype(({'exponent': ('>u1', 0), 'mantissa': ('>u2', 1)}, self.fromdims))
        else:
            return self.awkward.numpy.dtype(('>u4', self.fromdims))

    @property
    def fromdtypeflat(self):
        return _dtypeshape(self.fromdtype)[0]

    @property
    def todims(self):
        if self._todims is None:
            return self.fromdims
        else:
            return self._todims

    @property
    def itemsize(self):
        return self.fromdtype.itemsize

    def __repr__(self):
        args = [repr(self.low), repr(self.high), repr(self.numbits), repr(self.fromdtype), repr(self.todtype)]
        return "asdouble32(" + ", ".join(args) + ")"

    @property
    def identifier(self):
        fromdims = "(" + ",".join(repr(x) for x in self.fromdims) + ")"
        todims = "(" + ",".join(repr(x) for x in self.todims) + ")"
        return "asdouble32({0},{1},{2},{3},{4})".format(self.low, self.high, self.numbits, fromdims, todims)

    def compatible(self, other):
        return isinstance(other, asdouble32) and self.low == other.low and self.high == other.high and self.numbits == other.numbits and self.fromdtype == other.fromdtype and self.todtype == other.todtype

    def numitems(self, numbytes, numentries):
        quotient, remainder = divmod(numbytes, self.fromdtypeflat.itemsize)
        assert remainder == 0
        return quotient

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        # Interpret input data using proper type
        array = data.view(dtype=self.fromdtypeflat)
        # Make sure the interpreted data has correct shape
        if self.fromdims != ():
            product = int(self.awkward.numpy.prod(self.fromdims))
            quotient, remainder = divmod(len(array), product)
            assert remainder == 0, "{0} % {1} == {2} != 0".format(len(array), product, len(array) % product)
            array = array.reshape((quotient,) + self.fromdims)

        if self.truncated:
            array = array[local_entrystart:local_entrystop]
            # We have to make copies to work with contiguous arrays
            unpacked = array['exponent'].astype(self.awkward.numpy.int32)
            mantissa = array['mantissa'].astype(self.awkward.numpy.int32)

            unpacked <<= 23
            unpacked |= (mantissa & ((1 << (self.numbits + 1)) - 1)) << (23 - self.numbits)
            sign = ((1 << (self.numbits + 1)) & mantissa != 0) * -2 + 1

            array = unpacked.view(dtype=self.awkward.numpy.float32) * sign
            array = array.astype(self.todtypeflat)
        else:
            array = array[local_entrystart:local_entrystop].astype(self.todtypeflat)
            self.awkward.numpy.multiply(array, float(self.high - self.low) / (1 << self.numbits), out=array)
            self.awkward.numpy.add(array, self.low, out=array)

        return array

class asfloat16(asdouble32):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (asdouble32.__metaclass__,), {})

    def __init__(self, low, high, numbits, fromdims=(), todims=None):
        super(asfloat16, self).__init__(low, high, numbits, fromdims, todims)
        if self.truncated and not 2 <= numbits <= 16:
            raise TypeError("numbits must be an integer between 2 and 16 (inclusive).")

    @property
    def todtype(self):
        return self.awkward.numpy.dtype((self.awkward.numpy.float32, self.todims))

    def __repr__(self):
        args = [repr(self.low), repr(self.high), repr(self.numbits), repr(self.fromdtype), repr(self.todtype)]
        return "asfloat16(" + ", ".join(args) + ")"

    @property
    def identifier(self):
        fromdims = "(" + ",".join(repr(x) for x in self.fromdims) + ")"
        todims = "(" + ",".join(repr(x) for x in self.todims) + ")"
        return "asfloat16({0},{1},{2},{3},{4})".format(self.low, self.high, self.numbits, fromdims, todims)

    def compatible(self, other):
        return isinstance(other, asfloat16) and self.low == other.low and self.high == other.high and self.numbits == other.numbits and self.fromdtype == other.fromdtype and self.todtype == other.todtype

class asstlbitset(uproot.interp.interp.Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.interp.interp.Interpretation.__metaclass__,), {})

    @property
    def todtype(self):
        return self.awkward.numpy.dtype(self.awkward.numpy.bool_)

    def __init__(self, numbytes):
        self.numbytes = numbytes

    def __repr__(self):
        return self.identifier

    @property
    def identifier(self):
        return "asstlbitset({0})".format(self.numbytes)

    @property
    def type(self):
        return self.awkward.type.ArrayType(self.numbytes, self.todtype)

    def empty(self):
        return self.awkward.numpy.empty((0, self.numbytes), dtype=self.todtype)

    def compatible(self, other):
        return (isinstance(other, asstlbitset) and self.numbytes == other.numbytes) or \
               (isinstance(other, (asdtype, asarray)) and self.todtype == other.todtype and (self.numbytes,) == other.todims)

    def numitems(self, numbytes, numentries):
        return max(0, numbytes // (self.numbytes + 4))

    def source_numitems(self, source):
        return int(self.awkward.numpy.prod(source.shape))

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        return data.view(self.todtype).reshape((-1, self.numbytes + 4))[:, 4:]

    def destination(self, numitems, numentries):
        return self.awkward.numpy.empty((numitems, self.numbytes), dtype=self.todtype)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        destination[itemstart:itemstop] = source

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        return destination[itemstart:itemstop]

    def finalize(self, destination, branch):
        return destination
