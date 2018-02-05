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

if numba is not None:
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

    @staticmethod
    def interpret(data):
        i = 0
        out = []
        while i < len(data):
            if data[i] < 255:
                size = data[i]
                i += 1
            else:
                i += 1
                size = data[i : i + 4].view(">i4")
                i += 4
            out.append(data[i : i + size].tostring())
            i += size
        return out

    def __repr__(self):
        return "liststrings({0})".format(str(self))

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
                    return numba.typing.templates.signature(objtyp.jaggedarray.content, objtyp, idxtyp)

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
