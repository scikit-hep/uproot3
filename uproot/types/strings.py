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

import numpy
try:
    import numba
    import llvmlite
except ImportError:
    numba = None

import uproot.types.jagged

def _strings_flatten(data, offsets, contents, stops):
    start = stop = 0
    for i in range(len(offsets) - 1):
        if data[offsets[i]] == 255:
            instart = offsets[i] + 5
        else:
            instart = offsets[i] + 1
        instop = offsets[i + 1]

        stop = start + (instop - instart)

        contents[start:stop] = data[instart:instop]
        stops[i] = stop
        start = stop

if numba is not None:
    _strings_flatten = numba.njit(_strings_flatten)

class Strings(object):
    chartype = numpy.dtype(numpy.uint8)

    @staticmethod
    def fromstrs(*strs):
        stops = numpy.empty(len(strs), dtype=numpy.int64)
        stop = 0
        for i, x in enumerate(strs):
            if not isinstance(x, bytes) or hasattr(x, "encode"):
                x = x.encode("utf-8", "replace")
            stops[i] = stop = stop + len(x)

        if len(stops) == 0:
            contents = numpy.empty(0, dtype=Strings.chartype)
        else:
            contents = numpy.empty(stops[-1], dtype=Strings.chartype)

        for i, x, in enumerate(strs):
            if i == 0:
                start = 0
            else:
                start = stops[i - 1]
            stop = stops[i]

            if not isinstance(x, bytes) or hasattr(x, "encode"):
                x = x.encode("utf-8", "replace")
            contents[start:stop] = map(ord, x)

        return Strings(uproot.types.jagged.JaggedArray(contents, stops))

    @staticmethod
    def fromroot(data, offsets):
        contents = numpy.empty(len(data) - (len(offsets) - 1), dtype=Strings.chartype)
        stops = numpy.empty(len(offsets) - 1, dtype=offsets.dtype)
        _strings_flatten(data, offsets, contents, stops)
        return Strings(uproot.types.jagged.JaggedArray(contents, stops))

    def __init__(self, jaggedarray):
        assert jaggedarray.contents.dtype == Strings.chartype
        self.jaggedarray = jaggedarray

    def __len__(self):
        return len(self.jaggedarray)

    def __getitem__(self, index):
        return self.jaggedarray[index].tostring()

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
    def typer(jaggedarray):
        if isinstance(jaggedarray, uproot.types.jagged.JaggedArrayType):
            return StringsType(jaggedarray)
    return typer

# @numba.extending.register_model(StringsType)
# class StringsArrayModel(numba.datamodel.models.StructModel):
#     def __init__(self, dmm, fe_type):
#         members = [("jaggedarray", fe_type.jaggedarray)]
#         super(StringsArrayModel, self).__init__(dmm, fe_type, members)

# numba.extending.make_attribute_wrapper(StringsType, "jaggedarray", "jaggedarray")

@numba.extending.register_model(StringsType)
class StringsModel(numba.datamodel.models.TupleModel):
    def __init__(self, dmm, fe_type):
        super(StringsModel, self).__init__(dmm, fe_type.jaggedarray.tupletype())

class Stuff(Exception):
    def __init__(self, x):
        self.x = x

@numba.extending.unbox(StringsType)
def strings_unbox(typ, obj, c):
    print "ONE"
    jaggedarray_obj = c.pyapi.object_getattr_string(obj, "jaggedarray")
    print "TWO"
    out = uproot.types.jagged.jaggedarray_unbox(typ.jaggedarray, jaggedarray_obj, c)
    # c.pyapi.decref(jaggedarray_obj)
    print "THREE"
    return out

@numba.extending.box(StringsType)
def strings_box(typ, val, c):
    print "UNO"
    jaggedarray_obj = uproot.types.jagged.jaggedarray_box(typ.jaggedarray, val, c)
    print "DOS"
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Strings))
    print "TRES"
    out = c.pyapi.call_function_objargs(class_obj, [jaggedarray_obj])
    print "QUATRE"
    # c.pyapi.decref(jaggedarray_obj)
    # c.pyapi.decref(class_obj)
    return out




# @numba.extending.unbox(StringsType)
# def strings_unbox(typ, obj, c):
#     print "ONE"
#     jaggedarray_obj = c.pyapi.object_getattr_string(obj, "jaggedarray")
#     print "TWO"
#     out = uproot.types.jagged.jaggedarray_unbox(typ.jaggedarray, jaggedarray_obj, c)
#     # c.pyapi.decref(jaggedarray_obj)
#     print "THREE"
#     out.value.type = llvmlite.ir.types.LiteralStructType([out.value.type])
#     print "FOUR"
#     return out

# @numba.extending.box(StringsType)
# def strings_box(typ, val, c):
#     # raise Stuff((typ, val, c))
#     val.value.type = val.value.type.elements[0]
#     print "UNO", val.value
#     jaggedarray_obj = uproot.types.jagged.jaggedarray_box(typ.jaggedarray, val, c)
#     print "DOS"
#     class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Strings))
#     print "TRES"
#     out = c.pyapi.call_function_objargs(class_obj, [jaggedarray_obj])
#     print "QUATRE"
#     # c.pyapi.decref(jaggedarray_obj)
#     # c.pyapi.decref(class_obj)
#     return out


    
# @numba.extending.unbox(StringsType)
# def strings_unbox(typ, obj, c):
#     print "ONE"
#     jaggedarray_obj = c.pyapi.object_getattr_string(obj, "jaggedarray")
#     print "TWO"
#     strings = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)
#     print "THREE"
#     tmp = uproot.types.jagged.jaggedarray_unbox(typ.jaggedarray, jaggedarray_obj, c)
#     print "THREE.five", tmp
#     tmp.type = typ.jaggedarray
#     strings.jaggedarray = tmp
#     # c.pyapi.decref(jaggedarray_obj)
#     print "FOUR"
#     is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
#     print "FIVE"
#     out = numba.extending.NativeValue(strings._getvalue(), is_error=is_error)
#     print "SIX"
#     return out

# @numba.extending.box(StringsType)
# def strings_box(typ, val, c):
#     print "UNO"
#     strings = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
#     print "DOS"
#     jaggedarray_obj = uproot.types.jagged.jaggedarray_box(typ.jaggedarray, strings.jaggedarray, c)
#     print "TRES"
#     class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Strings))
#     print "QUATRO"
#     out = c.pyapi.call_function_objargs(class_obj, [jaggedarray_obj])
#     # c.pyapi.decref(jaggedarray_obj)
#     # c.pyapi.decref(class_obj)
#     print "CINQO"
#     return out


# @numba.typing.templates.infer_getattr
# class StructAttribute(numba.typing.templates.AttributeTemplate):
#     key = StringsType
#     def generic_resolve(self, typ, attr):
#         if attr == "jaggedarray":
#             return typ.jaggedarray

# @numba.extending.lower_getattr(StringsType, "jaggedarray")
# def strings_getattr_jaggedarray_impl(context, builder, typ, val):
#     return val

# @numba.extending.unbox(StringsType)
# def strings_unbox(typ, obj, c):
#     jaggedarray_obj = c.pyapi.object_getattr_string(obj, "jaggedarray")
#     out = uproot.types.jagged.jaggedarray_unbox(typ, jaggedarray_obj, c)
#     # c.pyapi.decref(jaggedarray_obj)
#     return out

# @numba.extending.box(StringsType)
# def strings_box(typ, val, c):
#     class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(Strings))
#     args = [c.box(typ.jaggedarray, val)]
#     out = c.pyapi.call_function_objargs(class_obj, args)
#     # c.pyapi.decref(class_obj)
#     return out



import numpy
data = numpy.array([5] + map(ord, "hello") + [5] + map(ord, "there"), dtype=numpy.uint8)
offsets = numpy.array([0, 6, 12])
a = Strings.fromroot(data, offsets)
print a

@numba.njit
def test1(x):
    return x

try:
    print test1(a)
except Stuff as stuff:
    pass
