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
except ImportError:
    numba = None

class JaggedArray(object):
    starts_dtype = numpy.dtype(numpy.int64)
    sizes_dtype = numpy.dtype(numpy.int64)

    def __init__(self, contents, starts, sizes):
        assert isinstance(contents, numpy.ndarray)
        assert isinstance(starts, numpy.ndarray) and starts.dtype == JaggedArray.starts_dtype
        assert isinstance(sizes, numpy.ndarray) and sizes.dtype == JaggedArray.sizes_dtype
        assert starts.shape == sizes.shape
        assert len(starts.shape) == 1
        self.contents = contents
        self.starts = starts
        self.sizes = sizes

    def __getitem__(self, index):
        if index < 0:
            index += len(self.starts)
        start = self.starts[index]
        stop  = start + self.sizes[index]
        return self.contents[start:stop]

a = JaggedArray(numpy.array([1.1, 1.1, 1.1, 3.3, 3.3]), numpy.array([0, 3, 3]), numpy.array([3, 0, 2]))
print a[0], a[1], a[2]

class JaggedArrayType(numba.types.Type):
    concrete = {}

    def __init__(self, contents, starts, sizes):
        assert isinstance(contents, numba.types.Array)
        assert isinstance(starts, numba.types.Array) and starts.dtype == numba.numpy_support.from_dtype(JaggedArray.starts_dtype) and starts.ndim == 1
        assert isinstance(sizes, numba.types.Array) and sizes.dtype == numba.numpy_support.from_dtype(JaggedArray.sizes_dtype) and starts.ndim == 1
        self.contents = contents
        self.starts = starts
        self.sizes = sizes
        if contents.name.startswith("array"):
            name = "jagged" + contents.name
        else:
            name = "jaggedarray({0})".format(contents.name)
        super(JaggedArrayType, self).__init__(name=name)

        @numba.extending.lower_getattr(JaggedArrayType, "contents")
        def jaggedarray_getattr_contents_impl(context, builder, typ, val):
            @numba.njit([typ.contents(typ.tupletype())])
            def get_field(astuple):
                return astuple[0]
            cres = get_field.overloads.values()[0]
            get_field_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
            del cres.target_context._defns[cres.entry_point]
            return get_field_imp(context, builder, cres.signature, (val,))

        @numba.extending.lower_getattr(JaggedArrayType, "starts")
        def jaggedarray_getattr_starts_impl(context, builder, typ, val):
            @numba.njit([typ.starts(typ.tupletype())])
            def get_field(astuple):
                return astuple[1]
            cres = get_field.overloads.values()[0]
            get_field_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
            del cres.target_context._defns[cres.entry_point]
            return get_field_imp(context, builder, cres.signature, (val,))

        @numba.extending.lower_getattr(JaggedArrayType, "sizes")
        def jaggedarray_getattr_sizes_impl(context, builder, typ, val):
            @numba.njit([typ.sizes(typ.tupletype())])
            def get_field(astuple):
                return astuple[2]
            cres = get_field.overloads.values()[0]
            get_field_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
            del cres.target_context._defns[cres.entry_point]
            return get_field_imp(context, builder, cres.signature, (val,))

    @staticmethod
    def get(contents, starts, sizes):
        key = (contents, starts, sizes)
        try:
            return JaggedArrayType.concrete[key]
        except KeyError:
            JaggedArrayType.concrete[key] = JaggedArrayType(contents, starts, sizes)
            return JaggedArrayType.concrete[key]

    def tupletype(self):
        return numba.types.Tuple((self.contents, self.starts, self.sizes))

@numba.extending.typeof_impl.register(JaggedArray)
def jaggedarray_typeof(val, c):
    assert isinstance(val, JaggedArray)
    return JaggedArrayType.get(numba.typing.typeof._typeof_ndarray(val.contents, c),
                               numba.typing.typeof._typeof_ndarray(val.starts, c),
                               numba.typing.typeof._typeof_ndarray(val.sizes, c))

@numba.extending.type_callable(JaggedArray)
def jaggedarray_type(context):
    def typer(contents, starts, sizes):
        raise TypeError("cannot create JaggedArray objects in compiled code (pass them into the function)")
    return typer

@numba.typing.templates.infer
class JaggedArray_getitem(numba.typing.templates.AbstractTemplate):
    key = "getitem"
    def generic(self, args, kwds):
        objtyp, idxtyp = args
        if isinstance(objtyp, JaggedArrayType):
            idxtyp = numba.typing.builtins.normalize_1d_index(idxtyp)
            if isinstance(idxtyp, numba.types.Integer):
                return numba.typing.templates.signature(objtyp.contents, objtyp, idxtyp)

@numba.extending.lower_builtin("getitem", JaggedArrayType, numba.types.Integer)
def jaggedarray_getitem(context, builder, sig, args):
    @numba.njit([sig])
    def getitem(jaggedarray, index):
        start = jaggedarray.starts[index]
        stop  = start + jaggedarray.sizes[index]
        return jaggedarray.contents[start:stop]

    cres = getitem.overloads.values()[0]
    getitem_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
    return getitem_imp(context, builder, sig, args)

@numba.extending.register_model(JaggedArrayType)
class JaggedArrayModel(numba.datamodel.models.TupleModel):
    def __init__(self, dmm, fe_type):
        super(JaggedArrayModel, self).__init__(dmm, fe_type.tupletype())

@numba.extending.infer_getattr
class StructAttribute(numba.typing.templates.AttributeTemplate):
    key = JaggedArrayType
    def generic_resolve(self, typ, attr):
        if attr == "contents":
            return typ.contents
        elif attr == "starts":
            return typ.starts
        elif attr == "sizes":
            return typ.sizes

@numba.extending.unbox(JaggedArrayType)
def jaggedarray_unbox(typ, obj, c):
    contents_obj = c.pyapi.object_getattr_string(obj, "contents")
    starts_obj = c.pyapi.object_getattr_string(obj, "starts")
    sizes_obj = c.pyapi.object_getattr_string(obj, "sizes")
    tuple_obj = c.pyapi.tuple_new(3)
    c.pyapi.tuple_setitem(tuple_obj, 0, contents_obj)
    c.pyapi.tuple_setitem(tuple_obj, 1, starts_obj)
    c.pyapi.tuple_setitem(tuple_obj, 2, sizes_obj)
    out = c.unbox(typ.tupletype(), tuple_obj)
    c.pyapi.decref(tuple_obj)
    return out

@numba.extending.box(JaggedArrayType)
def jaggedarray_box(typ, val, c):
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(JaggedArray))
    args = [c.box(typ.contents, c.builder.extract_value(val, 0)),
            c.box(typ.starts, c.builder.extract_value(val, 1)),
            c.box(typ.sizes, c.builder.extract_value(val, 2))]
    res = c.pyapi.call_function_objargs(class_obj, args)
    c.pyapi.decref(class_obj)
    return res

import time

startTime = time.time()
@numba.njit
def test1(a, i):
    return a[i]
print test1(a, 0)
print test1(a, 1)
print test1(a, 2)
print time.time() - startTime
