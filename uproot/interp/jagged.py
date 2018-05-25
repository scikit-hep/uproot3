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

import numpy

import uproot.source.source
import uproot.source.cursor
from uproot.interp.interp import Interpretation
from uproot.interp.numerical import asdtype
from uproot.interp.numerical import _dimsprod

def sizes2offsets(sizes):
    out = numpy.empty(len(sizes) + 1, dtype=sizes.dtype)
    out[0] = 0
    sizes.cumsum(out=out[1:])
    return out

def _compactify(fromdata, fromstarts, fromstops, todata, tostarts, tostops):
    for i in range(len(fromstarts)):
        todata[tostarts[i]:tostops[i]] = fromdata[fromstarts[i]:fromstops[i]]

try:
    import numba
except ImportError:
    pass
else:
    _compactify = numba.njit(_compactify)

class asjagged(Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (Interpretation.__metaclass__,), {})

    def __init__(self, asdtype, skip_bytes=0):
        self.asdtype = asdtype
        self.skip_bytes = skip_bytes

    def __repr__(self):
        if self.skip_bytes == 0:
            return "asjagged({0})".format(repr(self.asdtype))
        else:
            return "asjagged({0}, skip_bytes={1})".format(repr(self.asdtype), self.skip_bytes)

    def to(self, todtype=None, todims=None, skip_bytes=None):
        if skip_bytes is None:
            skip_bytes = self.skip_bytes
        return asjagged(self.asdtype.to(todtype, todims), skip_bytes)

    @property
    def identifier(self):
        if self.skip_bytes == 0:
            return "asjagged({0})".format(self.asdtype.identifier)
        else:
            return "asjagged({0}, {1})".format(self.asdtype.identifier, self.skip_bytes)

    @property
    def dtype(self):
        subshape = self.asdtype.dtype.shape
        sub = self.asdtype.dtype.subdtype
        if sub is None:
            tpe = self.asdtype.dtype
        else:
            tpe = sub[0]
        return numpy.dtype((tpe, (0,) + subshape))

    def empty(self):
        return JaggedArray(self.asdtype.empty(), numpy.empty(0, dtype=numpy.int64), numpy.empty(0, dtype=numpy.int64))

    def compatible(self, other):
        return isinstance(other, asjagged) and self.asdtype.compatible(other.asdtype)

    def numitems(self, numbytes, numentries):
        return self.asdtype.numitems(numbytes - numentries*self.skip_bytes, numentries)

    def source_numitems(self, source):
        return self.asdtype.source_numitems(source.content)

    def fromroot(self, data, offsets, local_entrystart, local_entrystop):
        if local_entrystart == local_entrystop:
            content = self.asdtype.fromroot(data, None, 0, 0)
        else:
            itemsize = self.asdtype.fromdtype.itemsize * _dimsprod(self.asdtype.fromdims)
            if self.skip_bytes == 0:
                numpy.floor_divide(offsets, itemsize, offsets)
                starts = offsets[local_entrystart     : local_entrystop    ]
                stops  = offsets[local_entrystart + 1 : local_entrystop + 1]
                content = self.asdtype.fromroot(data, None, starts[0], stops[-1])
            else:
                fromstarts = offsets[local_entrystart     : local_entrystop  ] + self.skip_bytes
                fromstops  = offsets[local_entrystart + 1 : local_entrystop + 1]
                newoffsets = numpy.empty(1 + local_entrystop - local_entrystart, dtype=offsets.dtype)
                newoffsets[0] = 0
                numpy.cumsum(fromstops - fromstarts, out=newoffsets[1:])
                newdata = numpy.empty(newoffsets[-1], dtype=data.dtype)
                _compactify(data, fromstarts, fromstops, newdata, newoffsets[:-1], newoffsets[1:])
                numpy.floor_divide(newoffsets, itemsize, newoffsets)
                starts = newoffsets[:-1]
                stops = newoffsets[1:]
                content = self.asdtype.fromroot(newdata, None, 0, stops[-1])
            return JaggedArray(content, starts, stops)

    def destination(self, numitems, numentries):
        content = self.asdtype.destination(numitems, numentries)
        sizes = numpy.empty(numentries, dtype=numpy.int64)
        return JaggedArray._Prep(content, sizes)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        destination.sizes[entrystart:entrystop] = source.stops - source.starts
        self.asdtype.fill(source.content, destination.content, itemstart, itemstop, entrystart, entrystop)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        destination.content = self.asdtype.clip(destination.content, itemstart, itemstop, entrystart, entrystop)
        destination.sizes = destination.sizes[entrystart:entrystop]
        return destination

    def finalize(self, destination, branch):
        offsets = sizes2offsets(destination.sizes)
        starts = offsets[:-1]
        stops  = offsets[1:]
        content = self.asdtype.finalize(destination.content, branch)
        leafcount = None
        if len(branch.fLeaves) == 1:
            leafcount = branch.fLeaves[0].fLeafCount
        return JaggedArray(content, starts, stops, leafcount=leafcount)

def asstlvector(asdtype):
    return asjagged(asdtype, skip_bytes=10)

def _jaggedarray_getitem(jaggedarray, index):
    stopslen = len(jaggedarray.stops)
    if index < 0:
        index += stopslen
    if 0 <= index < stopslen:
        start = jaggedarray.starts[index]
        stop  = jaggedarray.stops[index]
        return jaggedarray.content[start:stop]
    else:
        raise IndexError("index out of range for JaggedArray")

class JaggedArray(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    class _Prep(object):
        def __init__(self, content, sizes):
            self.content = content
            self.sizes = sizes

    @staticmethod
    def fromlists(lists):
        offsets = numpy.empty(len(lists) + 1, dtype=numpy.int64)
        offsets[0] = 0

        stop = 0
        anybool = False
        anyint = False
        anyfloat = False
        anycomplex = False
        for i, x in enumerate(lists):
            offsets[i + 1] = stop = stop + len(x)
            if isinstance(x, numpy.ndarray):
                if issubclass(x.dtype.type, (numpy.bool, numpy.bool_)):
                    anybool = True
                elif issubclass(x.dtype.type, numpy.integer):
                    anyint = True
                elif issubclass(x.dtype.type, numpy.floating):
                    anyfloat = True
                elif issubclass(x.dtype.type, numpy.complexfloating):
                    anycomplex = True
            else:
                if not anybool and not anyint and not anyfloat and not anycomplex and any(isinstance(y, bool) for y in x):
                    anybool = True
                if not anyint and not anyfloat and not anycomplex and any(isinstance(y, int) for y in x):
                    anyint = True
                if not anyfloat and not anycomplex and any(isinstance(y, float) for y in x):
                    anyfloat = True
                if not anycomplex and any(isinstance(y, complex) for y in x):
                    anycomplex = True

        if anycomplex:
            dtype = numpy.dtype(numpy.complex)
        elif anyfloat:
            dtype = numpy.dtype(numpy.float64)
        elif anyint:
            dtype = numpy.dtype(numpy.int64)
        elif anybool:
            dtype = numpy.dtype(numpy.bool)
        else:
            raise TypeError("no numerical types found in lists")

        starts = offsets[:-1]
        stops  = offsets[1:]
        content = numpy.empty(offsets[-1], dtype=dtype)

        for i, x in enumerate(lists):
            content[starts[i]:stops[i]] = x

        return JaggedArray(content, starts, stops)

    def __init__(self, content, starts, stops, leafcount=None):
        assert isinstance(content, numpy.ndarray)
        assert isinstance(starts, numpy.ndarray) and issubclass(starts.dtype.type, numpy.integer)
        assert isinstance(stops, numpy.ndarray) and issubclass(stops.dtype.type, numpy.integer)
        assert len(stops.shape) == 1
        assert starts.shape == stops.shape
        self.content = content
        self.starts = starts
        self.stops = stops
        self.leafcount = leafcount

    def __getstate__(self):
        state = self.__dict__.copy()
        state["leafcount"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __eq__(self, other):
        return isinstance(other, JaggedArray) and numpy.array_equal(self.content, other.content) and self.aligned(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def _offsets_aliased(self):
        return (self.starts.base is not None and self.stops.base is not None and self.starts.base is self.stops.base and
                self.starts.ctypes.data == self.starts.base.ctypes.data and
                self.stops.ctypes.data == self.stops.base.ctypes.data + self.starts.dtype.itemsize and
                len(self.starts) == len(self.starts.base) - 1 and
                len(self.stops) == len(self.starts.base) - 1)

    @property
    def offsets(self):
        if self._offsets_aliased():
            return self.starts.base
        elif numpy.array_equal(self.starts[1:], self.stops[:-1]):
            return numpy.append(self.starts, self.stops[-1])
        else:
            raise ValueError("starts and stops are not compatible; cannot express as offsets")

    def aligned(self, other):
        if self.leafcount is not None and other.leafcount is not None and self.leafcount is other.leafcount:
            return True
        else:
            return numpy.array_equal(self.starts, other.starts) and numpy.array_equal(self.stops, other.stops)

    def __len__(self):
        return len(self.stops)

    def __getitem__(self, index):
        if isinstance(index, numbers.Integral):
            return _jaggedarray_getitem(self, index)

        elif isinstance(index, slice):
            if index.step is not None and index.step != 1:
                raise NotImplementedError("cannot yet slice a JaggedArray with step != 1 (FIXME: this is possible, should be implemented)")
            else:
                return JaggedArray(self.content, self.starts[index], self.stops[index])

        else:
            raise TypeError("JaggedArray index must be an integer or a slice")

    def __iter__(self):
        content = self.content
        starts = self.starts
        stops = self.stops
        for i in range(len(stops)):
            yield content[starts[i]:stops[i]]

    def __repr__(self, indent="", linewidth=None):
        if linewidth is None:
            linewidth = numpy.get_printoptions()["linewidth"]
        dtypestr = repr(self.content.dtype).replace("(", "=").rstrip(")")
        linewidth = linewidth - 12 - 2 - len(dtypestr)
        return "jaggedarray({0})".format(self.__str__(indent=" " * 12, linewidth=linewidth))

    def __str__(self, indent="", linewidth=None):
        if linewidth is None:
            linewidth = numpy.get_printoptions()["linewidth"]

        def single(a):
            if len(a) > 6:
                return numpy.array_str(a[:3], max_line_width=numpy.inf).rstrip("]") + " ... " + numpy.array_str(a[-3:], max_line_width=numpy.inf).lstrip("[")
            else:
                return numpy.array_str(a, max_line_width=numpy.inf)

        if len(self) > 10:
            content = [single(self[i]) for i in range(3)] + ["..."] + [single(self[i]) for i in range(-3, 0)]
        else:
            content = [single(x) for x in self]

        if sum(len(x) for x in content) + 2*(len(content) - 1) + 2 <= linewidth:
            return "[" + ", ".join(content) + "]"
        else:
            return "[" + (",\n " + indent).join(content) + "]"

    def tolist(self):
        return [x.tolist() for x in self]

    def __array__(self, dtype=None, copy=False, order="K", subok=False, ndmin=0):
        if dtype is None:
            dtype = self.content.dtype
        elif not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)

        if dtype == self.content.dtype and not copy and not subok and ndmin == 0:
            return self.content
        else:
            return numpy.array(self.content, dtype=dtype, copy=copy, order=order, subok=subok, ndmin=ndmin)

    @property
    def nbytes(self):
        if self._offsets_aliased():
            return self.content.nbytes + self.starts.base.nbytes
        else:
            return self.content.nbytes + self.starts + self.stops

class asvar(asjagged):
    def __init__(self, genclass, skip_bytes=0, args=()):
        self.genclass = genclass
        super(asvar, self).__init__(asdtype(numpy.dtype(numpy.uint8)), skip_bytes=skip_bytes)
        self.args = args

    def __repr__(self):
        return self.identifier

    @property
    def identifier(self):
        args = []
        if self.skip_bytes != 0:
            args.append(", skip_bytes={0}".format(self.skip_bytes))
        return "asvar({0}{1})".format(self.genclass.__name__, "".join(args))

    @property
    def dtype(self):
        return self.genclass._dtype(self.args)

    def empty(self):
        return self.genclass(*((super(asvar, self).empty(),) + self.args))

    def compatible(self, other):
        return isinstance(other, asvar) and self.genclass is other.genclass and super(asvar, self).compatible(other) and self.args == other.args

    def source_numitems(self, source):
        return super(asvar, self).source_numitems(source.jaggedarray)

    def fromroot(self, data, offsets, local_entrystart, local_entrystop):
        return self.genclass(*((super(asvar, self).fromroot(data, offsets, local_entrystart, local_entrystop),) + self.args))

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        return super(asvar, self).fill(source.jaggedarray, destination, itemstart, itemstop, entrystart, entrystop)

    def finalize(self, destination, branch):
        return self.genclass(*((super(asvar, self).finalize(destination, branch),) + self.args))

class VariableLength(object):
    def __init__(self, *args):
        self.jaggedarray = args[0]
        assert self.jaggedarray.content.dtype.itemsize == 1
        assert len(self.jaggedarray.content.shape) == 1
        self.args = args[1:]

    def __len__(self):
        return len(self.jaggedarray)

    def __getitem__(self, index):
        if isinstance(index, numbers.Integral):
            return self.interpret(self.jaggedarray[index])

        elif isinstance(index, slice):
            return self.__class__(*((self.jaggedarray[index],) + self.args))

        else:
            raise TypeError("{0} index must be an integer or a slice".format(self.__class__.__name__))

    def __iter__(self):
        for x in self.jaggedarray:
            yield self.interpret(x)

    def __str__(self):
        if len(self) > 6:
            return "[{0} ... {1}]".format(" ".join(repr(self[i]) for i in range(3)), " ".join(repr(self[i]) for i in range(-3, 0)))
        else:
            return "[{0}]".format(" ".join(repr(x) for x in self))

    def tolist(self):
        return list(self)

    @staticmethod
    def interpret(item):
        raise NotImplementedError

class asobjs(asvar):
    def __init__(self, cls, context=None):
        super(asobjs, self).__init__(JaggedObjects, skip_bytes=0, args=(cls, context))
        self.cls = cls
        self.context = context

    @property
    def identifier(self):
        return "asobjs({0})".format(self.cls.__name__)

    @property
    def dtype(self):
        return numpy.dtype((object, (0,)))

class asobj(asvar):
    def __init__(self, cls, context=None):
        super(asobj, self).__init__(JaggedObject, skip_bytes=0, args=(cls, context))
        self.cls = cls
        self.context = context

    @property
    def identifier(self):
        return "asobj({0})".format(self.cls.__name__)

    @property
    def dtype(self):
        return numpy.dtype((object, (0,)))

class JaggedObjects(VariableLength):
    indexdtype = numpy.dtype(">i4")

    def __init__(self, jaggedarray, cls, context):
        super(JaggedObjects, self).__init__(jaggedarray, cls)
        self._class = cls
        self._context = context

    def interpret(self, item):
        size, = item[6:10].view(JaggedObjects.indexdtype)
        source = uproot.source.source.Source(item)
        cursor = uproot.source.cursor.Cursor(10)
        out = [None] * size
        for i in range(size):
            out[i] = self._class.read(source, cursor, self._context, None)
        return out

    def __str__(self):
        if len(self) > 6:
            return "[{0}\n ...\n{1}]".format(",\n".join(("" if i == 0 else " ") + repr(self[i]) for i in range(3)), ",\n".join(" " + repr(self[i]) for i in range(-3, 0)))
        else:
            return "[{0}]".format(", ".join(repr(x) for x in self))

    def __repr__(self):
        return "<JaggedObjects of {0} at {1:012x}>".format(self._class.__name__, id(self))

    def __getitem__(self, index):
        if isinstance(index, numbers.Integral):
            return self.interpret(self.jaggedarray[index])

        elif isinstance(index, slice):
            return JaggedObjects(self.jaggedarray[index], self._class, self._context)

        else:
            raise TypeError("{0} index must be an integer or a slice".format(self.__class__.__name__))

class JaggedObject(VariableLength):

    def __init__(self, jaggedarray, cls, context):
        super(JaggedObject, self).__init__(jaggedarray, cls)
        self._class = cls
        self._context = context

    def interpret(self, item):
        source = uproot.source.source.Source(item)
        cursor = uproot.source.cursor.Cursor(0)
        return self._class.read(source, cursor, self._context, None)

    def __str__(self):
        if len(self) > 6:
            return "[{0}\n ...\n{1}]".format(",\n".join(("" if i == 0 else " ") + repr(self[i]) for i in range(3)), ",\n".join(" " + repr(self[i]) for i in range(-3, 0)))
        else:
            return "[{0}]".format(", ".join(repr(x) for x in self))

    def __repr__(self):
        return "<JaggedObject of {0} at {1:012x}>".format(self._class.__name__, id(self))

    def __getitem__(self, index):
        if isinstance(index, numbers.Integral):
            return self.interpret(self.jaggedarray[index])

        elif isinstance(index, slice):
            return JaggedObject(self.jaggedarray[index], self._class, self._context)

        else:
            raise TypeError("{0} index must be an integer or a slice".format(self.__class__.__name__))


def asstlvectorvector(fromdtype):
    return asvar(JaggedJaggedArray, skip_bytes=6, args=(numpy.dtype(fromdtype),))

class JaggedJaggedArray(VariableLength):
    def __init__(self, jaggedarray, fromdtype):
        super(JaggedJaggedArray, self).__init__(jaggedarray, fromdtype)
        self.fromdtype = fromdtype

    @classmethod
    def _dtype(cls, args):
        dtype, = args
        return numpy.dtype((dtype, (0, 0)))

    indexdtype = numpy.dtype(">i4")

    def interpret(self, item):
        i = 0
        size, = item[i : i + 4].view(JaggedJaggedArray.indexdtype)
        i += 4
        out = []
        while i < len(item):
            size, = item[i : i + 4].view(JaggedJaggedArray.indexdtype)
            i += 4
            numbytes = size * self.fromdtype.itemsize
            out.append(item[i : i + numbytes].view(self.fromdtype))
            i += numbytes
        return out

    def __str__(self):
        if len(self) > 6:
            return "[{0} ... {1}]".format(", ".join(repr([y.tolist() for y in self[i]]) for i in range(3)), ", ".join(repr([y.tolist() for y in self[i]]) for i in range(-3, 0)))
        else:
            return "[{0}]".format(", ".join(repr([y.tolist() for y in x]) for x in self))

    def __repr__(self):
        return "jaggedjaggedarray({0})".format(str(self))

    def tolist(self):
        return [[y.tolist() for y in x] for x in self]
