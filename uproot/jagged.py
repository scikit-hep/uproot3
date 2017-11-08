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

def _jaggedarray_getitem(jaggedarray, index):
    stopslen = len(jaggedarray.stops)
    if index < 0:
        index += stopslen
    if 0 <= index < stopslen:
        if index == 0:
            start = 0
        else:
            start = jaggedarray.stops[index - 1]
        stop = jaggedarray.stops[index]
        return jaggedarray.contents[start:stop]
    else:
        raise IndexError("index out of range for JaggedArray")

class JaggedArray(object):
    @staticmethod
    def fromlists(*lists):
        stops = numpy.empty(len(lists), dtype=numpy.int64)

        stop = 0
        anybool = False
        anyint = False
        anyfloat = False
        anycomplex = False
        for i, x in enumerate(lists):
            stops[i] = stop = stop + len(x)
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

        if len(stops) == 0:
            contents = numpy.empty(0, dtype=dtype)
        else:
            contents = numpy.empty(stops[-1], dtype=dtype)

        for i, x in enumerate(lists):
            if i == 0:
                start = 0
            else:
                start = stops[i - 1]
            stop = stops[i]

            contents[start:stop] = x

        return JaggedArray(contents, stops)

    def __init__(self, contents, stops):
        assert isinstance(contents, numpy.ndarray)
        assert isinstance(stops, numpy.ndarray) and issubclass(stops.dtype.type, numpy.integer)
        assert len(stops.shape) == 1
        self.contents = contents
        self.stops = stops

    def __len__(self):
        return len(self.stops)

    def __getitem__(self, index):
        return _jaggedarray_getitem(self, index)

    def __iter__(self):
        for i, stop in enumerate(self.stops):
            if i == 0:
                start = 0
            else:
                start = self.stops[i - 1]
            yield self.contents[start:stop]

    def __repr__(self, indent="", linewidth=None):
        if linewidth is None:
            linewidth = numpy.get_printoptions()["linewidth"]
        dtypestr = repr(self.contents.dtype).replace("(", "=").rstrip(")")
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
            contents = [single(self[i]) for i in range(3)] + ["..."] + [single(self[i]) for i in range(-3, 0)]
        else:
            contents = [single(x) for x in self]

        if sum(len(x) for x in contents) + 2*(len(contents) - 1) + 2 <= linewidth:
            return "[" + ", ".join(contents) + "]"
        else:
            return "[" + (",\n " + indent).join(contents) + "]"

if numba is not None:
    class JaggedArrayType(numba.types.Type):
        concrete = {}

        def __init__(self, contents, stops):
            assert isinstance(contents, numba.types.Array)
            assert isinstance(stops, numba.types.Array)
            assert stops.ndim == 1
            self.contents = contents
            self.stops = stops
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

            @numba.extending.lower_getattr(JaggedArrayType, "stops")
            def jaggedarray_getattr_stops_impl(context, builder, typ, val):
                @numba.njit([typ.stops(typ.tupletype())])
                def get_field(astuple):
                    return astuple[1]
                cres = get_field.overloads.values()[0]
                get_field_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
                del cres.target_context._defns[cres.entry_point]
                return get_field_imp(context, builder, cres.signature, (val,))

        @staticmethod
        def get(contents, stops):
            key = (contents, stops)
            try:
                return JaggedArrayType.concrete[key]
            except KeyError:
                JaggedArrayType.concrete[key] = JaggedArrayType(contents, stops)
                return JaggedArrayType.concrete[key]

        def tupletype(self):
            return numba.types.Tuple((self.contents, self.stops))

    @numba.extending.typeof_impl.register(JaggedArray)
    def jaggedarray_typeof(val, c):
        assert isinstance(val, JaggedArray)
        return JaggedArrayType.get(numba.typing.typeof._typeof_ndarray(val.contents, c),
                                   numba.typing.typeof._typeof_ndarray(val.stops, c))

    @numba.extending.type_callable(JaggedArray)
    def jaggedarray_type(context):
        def typer(contents, stops):
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
        try:
            getitem_imp = jaggedarray_getitem.cache[sig.args]
        except KeyError:
            getitem = numba.njit([sig])(_jaggedarray_getitem)
            cres = getitem.overloads.values()[0]
            getitem_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
            jaggedarray_getitem.cache[sig.args] = getitem_imp
        return getitem_imp(context, builder, sig, args)
    jaggedarray_getitem.cache = {}

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
            elif attr == "stops":
                return typ.stops

    @numba.extending.unbox(JaggedArrayType)
    def jaggedarray_unbox(typ, obj, c):
        contents_obj = c.pyapi.object_getattr_string(obj, "contents")
        stops_obj = c.pyapi.object_getattr_string(obj, "stops")
        tuple_obj = c.pyapi.tuple_new(2)
        c.pyapi.tuple_setitem(tuple_obj, 0, contents_obj)
        c.pyapi.tuple_setitem(tuple_obj, 1, stops_obj)
        out = c.unbox(typ.tupletype(), tuple_obj)
        c.pyapi.decref(tuple_obj)
        return out

    @numba.extending.box(JaggedArrayType)
    def jaggedarray_box(typ, val, c):
        class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(JaggedArray))
        args = [c.box(typ.contents, c.builder.extract_value(val, 0)),
                c.box(typ.stops, c.builder.extract_value(val, 1))]
        res = c.pyapi.call_function_objargs(class_obj, args)
        c.pyapi.decref(class_obj)
        return res

    @numba.extending.overload(len)
    def jaggedarray_len(obj):
        if isinstance(obj, JaggedArrayType):
            def len_impl(jaggedarray):
                return len(jaggedarray.stops)
            return len_impl

    class JaggedArrayIteratorType(numba.types.common.SimpleIteratorType):
        def __init__(self, jaggedarraytype):
            self.jaggedarray = jaggedarraytype
            name = "iter({0})".format(jaggedarraytype.name)
            super(JaggedArrayIteratorType, self).__init__(name, jaggedarraytype.contents)

    @numba.datamodel.registry.register_default(JaggedArrayIteratorType)
    class JaggedArrayIteratorModel(numba.datamodel.models.StructModel):
        integertype = numba.types.int64

        def __init__(self, dmm, fe_type):
            members = [("index", numba.types.EphemeralPointer(JaggedArrayIteratorModel.integertype)),
                       ("jaggedarray", fe_type.jaggedarray)]
            super(JaggedArrayIteratorModel, self).__init__(dmm, fe_type, members)

    @numba.typing.templates.infer
    class JaggedArray_getiter(numba.typing.templates.AbstractTemplate):
        key = "getiter"
        def generic(self, args, kwds):
            objtyp, = args
            if isinstance(objtyp, JaggedArrayType):
                return numba.typing.templates.signature(JaggedArrayIteratorType(objtyp), objtyp)

    @numba.extending.lower_builtin("getiter", JaggedArrayType)
    def jaggedarray_getiter(context, builder, sig, args):
        arrayty, = sig.args
        array, = args

        iterobj = context.make_helper(builder, sig.return_type)

        zero = context.get_constant(JaggedArrayIteratorModel.integertype, 0)
        indexptr = numba.cgutils.alloca_once_value(builder, zero)
        iterobj.index = indexptr
        iterobj.jaggedarray = array

        # incref array
        if context.enable_nrt:
            context.nrt.incref(builder, arrayty, array)

        res = iterobj._getvalue()
        return numba.targets.imputils.impl_ret_new_ref(context, builder, sig.return_type, res)

    def jaggedarray_getitem_foriter(context, builder, jaggedarraytype, jaggedarray, index):
        if jaggedarray_getitem_foriter.cache is None:
            @numba.njit([jaggedarraytype.contents(jaggedarraytype, JaggedArrayIteratorModel.integertype)])
            def getitem(a, i):
                if i == 0:
                    start = 0
                else:
                    start = a.stops[i - 1]
                stop = a.stops[i]
                return a.contents[start:stop]
            cres = getitem.overloads.values()[0]
            jaggedarray_getitem_foriter.cache = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
        return jaggedarray_getitem_foriter.cache(context, builder, jaggedarraytype.contents(jaggedarraytype, JaggedArrayIteratorModel.integertype), (jaggedarray, index))
    jaggedarray_getitem_foriter.cache = None

    @numba.extending.lower_builtin("iternext", JaggedArrayIteratorType)
    @numba.targets.imputils.iternext_impl
    def jaggedarray_iternext(context, builder, sig, args, result):
        jaggedarraytype = sig.args[0].jaggedarray
        iterobj = context.make_helper(builder, sig.args[0], value=args[0])

        stops = builder.extract_value(iterobj.jaggedarray, 1)
        stopsary = numba.targets.arrayobj.make_array(jaggedarraytype.stops)(context, builder, value=stops)
        nitems, = numba.cgutils.unpack_tuple(builder, stopsary.shape, count=1)

        index = builder.load(iterobj.index)
        is_valid = builder.icmp(llvmlite.llvmpy.core.ICMP_SLT, index, nitems)  # http://llvm.org/doxygen/classllvm_1_1CmpInst.html
        result.set_valid(is_valid)

        with builder.if_then(is_valid):
            value = jaggedarray_getitem_foriter(context, builder, jaggedarraytype, iterobj.jaggedarray, index)
            result.yield_(value)
            nindex = numba.cgutils.increment_index(builder, index)
            builder.store(nindex, iterobj.index)
