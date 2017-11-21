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
try:
    import numba
    import llvmlite
except ImportError:
    numba = None

from uproot.interp.interp import Interpretation
from uproot.interp.jagged import JaggedArray
from uproot.interp.jagged import sizes2offsets

CHARTYPE = numpy.dtype(numpy.uint8)

def _asstrings_fromroot(data, offsets, local_entrystart, local_entrystop):
    if local_entrystart < 0 or local_entrystop >= len(offsets) or local_entrystart > local_entrystop:
        raise ValueError("illegal local_entrystart or local_entrystop in asstrings.fromroot")

    contents = numpy.empty(offsets[local_entrystop] - offsets[local_entrystart] - (local_entrystop - local_entrystart), dtype=CHARTYPE)
    newoffsets  = numpy.empty(1 + local_entrystop - local_entrystart, dtype=offsets.dtype)
    newoffsets[0] = 0

    start = stop = 0
    for entry in range(local_entrystart, local_entrystop):
        datastart = offsets[entry]
        datastop = offsets[entry + 1]
        if data[datastart] == 255:
            datastart += 5
        else:
            datastart += 1

        stop = start + (datastop - datastart)

        contents[start:stop] = data[datastart:datastop]
        newoffsets[1 + entry - local_entrystart] = stop

        start = stop

    return contents[:stop], newoffsets[:-1], newoffsets[1:]

if numba is not None:
    _asstrings_fromroot = numba.njit(_asstrings_fromroot)

class _asstrings(Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (Interpretation.__metaclass__,), {})

    def empty(self):
        return Strings(JaggedArray(numpy.empty(0, dtype=CHARTYPE), numpy.empty(0, dtype=numpy.int64)))

    def compatible(self, other):
        return self is other

    def numitems(self, numbytes, numentries):
        return numbytes - numentries              # an overestimate if there are any individual strings with > 255 bytes

    def source_numitems(self, source):
        return len(source.jaggedarray.contents)   # not an overestimate; refines the above after opening the data

    def fromroot(self, data, offsets, local_entrystart, local_entrystop):
        return Strings(JaggedArray(*_asstrings_fromroot(data, offsets, local_entrystart, local_entrystop)))

    def destination(self, numitems, numentries):
        contents = numpy.empty(numitems, dtype=CHARTYPE)
        sizes = numpy.empty(numentries, dtype=numpy.int64)
        return JaggedArray._Prep(contents, sizes)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        destination.contents[itemstart:itemstop] = source.jaggedarray.contents
        destination.sizes[entrystart:entrystop] = source.jaggedarray.stops - source.jaggedarray.starts
        
    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        destination.contents = destination.contents[itemstart:itemstop]
        destination.sizes = destination.sizes[entrystart:entrystop]
        return destination

    def finalize(self, destination):
        contents = destination.contents
        offsets = sizes2offsets(destination.sizes)
        starts = offsets[:-1]
        stops  = offsets[1:]
        return Strings(JaggedArray(contents, starts, stops))

asstrings = _asstrings()

class Strings(object):
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

        contents = numpy.empty(offsets[-1], dtype=CHARTYPE)
        starts = offsets[:-1]
        stops = offsets[1:]

        if sys.version_info[0] <= 2:
            for i, x, in enumerate(strs):
                if isinstance(x, unicode):
                    x = x.encode("utf-8", "replace")
                contents[starts[i]:stops[i]] = map(ord, x)
        else:
            for i, x, in enumerate(strs):
                if isinstance(x, str):
                    x = x.encode("utf-8", "replace")
                contents[starts[i]:stops[i]] = memoryview(x)
            
        return Strings(uproot.types.jagged.JaggedArray(contents, starts, stops))

    def __init__(self, jaggedarray):
        assert jaggedarray.contents.dtype == CHARTYPE
        assert len(jaggedarray.contents.shape) == 1
        self.jaggedarray = jaggedarray

    def __len__(self):
        return len(self.jaggedarray)

    def __getitem__(self, index):
        if isinstance(index, numbers.Integral):
            return self.jaggedarray[index].tostring()

        elif isinstance(index, slice):
            return Strings(self.jaggedarray[slice])

        else:
            raise TypeError("Strings index must be an integer or a slice")

    def __iter__(self):
        for x in self.jaggedarray:
            yield x.tostring()

    def __repr__(self):
        return "strings({0})".format(str(self))

    def __str__(self):
        if len(self) > 6:
            return "[{0} ... {1}]".format(" ".join(repr(self[i]) for i in range(3)), " ".join(repr(self[i]) for i in range(-3, 0)))
        else:
            return "[{0}]".format(" ".join(repr(x) for x in self))

    def tolist(self):
        return list(self)

if numba is not None:
    class StringsType(numba.types.Type):
        def __init__(self, jaggedarray):
            self.jaggedarray = jaggedarray
            super(StringsType, self).__init__("strings({0})".format(jaggedarray.name))

    @numba.extending.typeof_impl.register(Strings)
    def strings_typeof(val, c):
        assert isinstance(val, Strings)
        return StringsType(uproot.types.jagged.jaggedarray_typeof(val.jaggedarray, c))

    @numba.extending.type_callable(Strings)
    def strings_type(context):
        def typer(strings):
            raise TypeError("cannot create Strings object in compiled code (pass it into the function)")
        return typer

    @numba.extending.register_model(StringsType)
    class StringsModel(numba.datamodel.models.TupleModel):
        def __init__(self, dmm, fe_type):
            super(StringsModel, self).__init__(dmm, fe_type.jaggedarray.tupletype())

    @numba.extending.unbox(StringsType)
    def strings_unbox(typ, obj, c):
        jaggedarray_obj = c.pyapi.object_getattr_string(obj, "jaggedarray")
        out = uproot.types.jagged.jaggedarray_unbox(typ.jaggedarray, jaggedarray_obj, c)
        c.pyapi.decref(jaggedarray_obj)
        return out

    @numba.extending.box(StringsType)
    def strings_box(typ, val, c):
        jaggedarray_obj = uproot.types.jagged.jaggedarray_box(typ.jaggedarray, val, c)
        class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Strings))
        out = c.pyapi.call_function_objargs(class_obj, [jaggedarray_obj])
        c.pyapi.decref(jaggedarray_obj)
        c.pyapi.decref(class_obj)
        return out

    @numba.extending.type_callable(len)
    def strings_len_type(context):
        return uproot.types.jagged.jaggedarray_len_type(context)

    @numba.extending.lower_builtin(len, StringsType)
    def strings_len(context, builder, sig, args):
        return uproot.types.jagged.jaggedarray_len(context, builder, sig.return_type(sig.args[0].jaggedarray), args)

    @numba.extending.overload(len)
    def strings_len(obj):
        if isinstance(obj, StringsType):
            def len_impl(strings):
                return len(strings.jaggedarray)
            return len_impl

    @numba.typing.templates.infer
    class Strings_getitem(numba.typing.templates.AbstractTemplate):
        key = "getitem"
        def generic(self, args, kwds):
            objtyp, idxtyp = args
            if isinstance(objtyp, StringsType):
                idxtyp = numba.typing.builtins.normalize_1d_index(idxtyp)
                if isinstance(idxtyp, numba.types.Integer):
                    return numba.typing.templates.signature(objtyp.jaggedarray.contents, objtyp, idxtyp)

    @numba.extending.lower_builtin("getitem", StringsType, numba.types.Integer)
    def strings_getitem(context, builder, sig, args):
        return uproot.types.jagged.jaggedarray_getitem(context, builder, sig.return_type(sig.args[0].jaggedarray, sig.args[1]), args)

    @numba.typing.templates.infer
    class Strings_getiter(numba.typing.templates.AbstractTemplate):
        key = "getiter"
        def generic(self, args, kwds):
            objtyp, = args
            if isinstance(objtyp, StringsType):
                return numba.typing.templates.signature(uproot.types.jagged.JaggedArrayIteratorType(objtyp.jaggedarray), objtyp)

    @numba.extending.lower_builtin("getiter", StringsType)
    def strings_getiter(context, builder, sig, args):
        return uproot.types.jagged.jaggedarray_getiter(context, builder, sig.return_type(sig.args[0].jaggedarray), args)
