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
try:
    import numba
    import llvmlite
except ImportError:
    numba = None

from uproot.interp.interp import Interpretation

def sizes2offsets(sizes):
    out = numpy.empty(len(sizes) + 1, dtype=sizes.dtype)
    out[0] = 0
    sizes.cumsum(out=out[1:])
    return out

def _compactify(fromdata, fromstarts, fromstops, todata, tostarts, tostops):
    for i in range(len(fromstarts)):
        todata[tostarts[i]:tostops[i]] = fromdata[fromstarts[i]:fromstops[i]]

if numba is not None:
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

    def empty(self):
        return JaggedArray._Prep(self.asdtype.empty(), numpy.empty(0, dtype=numpy.int64))

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
            if self.skip_bytes == 0:
                numpy.floor_divide(offsets, self.asdtype.fromdtype.itemsize, offsets)
                starts = offsets[local_entrystart     : local_entrystop    ]
                stops  = offsets[local_entrystart + 1 : local_entrystop + 1]
                content = self.asdtype.fromroot(data, None, starts[0], stops[-1])
            else:
                fromstarts = offsets[local_entrystart     : local_entrystop    ] + self.skip_bytes
                fromstops  = offsets[local_entrystart + 1 : local_entrystop + 1]
                newoffsets = numpy.empty(1 + local_entrystop - local_entrystart, dtype=offsets.dtype)
                newoffsets[0] = 0
                numpy.cumsum(fromstops - fromstarts, out=newoffsets[1:])
                newdata = numpy.empty(newoffsets[-1], dtype=data.dtype)
                _compactify(data, fromstarts, fromstops, newdata, newoffsets[:-1], newoffsets[1:])
                numpy.floor_divide(newoffsets, self.asdtype.fromdtype.itemsize, newoffsets)
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

    def finalize(self, destination):
        offsets = sizes2offsets(destination.sizes)
        starts = offsets[:-1]
        stops  = offsets[1:]
        content = self.asdtype.finalize(destination.content)
        return JaggedArray(content, starts, stops)

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

    def __init__(self, content, starts, stops):
        assert isinstance(content, numpy.ndarray)
        assert isinstance(starts, numpy.ndarray) and issubclass(starts.dtype.type, numpy.integer)
        assert isinstance(stops, numpy.ndarray) and issubclass(stops.dtype.type, numpy.integer)
        assert len(stops.shape) == 1
        assert starts.shape == stops.shape
        self.content = content
        self.starts = starts
        self.stops = stops

    def __len__(self):
        return len(self.stops)

    def __getitem__(self, index):
        if isinstance(index, numbers.Integral):
            return _jaggedarray_getitem(self, index)

        elif isinstance(index, slice):
            if index.step is not None and index.step != 1:
                raise NotImplementedError("cannot slice a JaggedArray with step != 1")
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

class VariableLength(object):
    def __init__(self, jaggedarray):
        assert jaggedarray.content.dtype.itemsize == 1
        assert len(jaggedarray.content.shape) == 1
        self.jaggedarray = jaggedarray

    def __len__(self):
        return len(self.jaggedarray)

    def __getitem__(self, index):
        if isinstance(index, numbers.Integral):
            return self.interpret(self.jaggedarray[index])

        elif isinstance(index, slice):
            return self.__class__(self.jaggedarray[slice])

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

if numba is not None:
    class JaggedArrayType(numba.types.Type):
        concrete = {}

        def __init__(self, content, starts, stops):
            assert isinstance(content, numba.types.Array)
            assert isinstance(starts, numba.types.Array)
            assert isinstance(stops, numba.types.Array)
            assert starts.ndim == 1
            assert stops.ndim == 1
            self.content = content
            self.starts = starts
            self.stops = stops
            if content.name.startswith("array"):
                name = "jagged" + content.name
            else:
                name = "jaggedarray({0})".format(content.name)
            super(JaggedArrayType, self).__init__(name=name)

            @numba.extending.lower_getattr(JaggedArrayType, "content")
            def jaggedarray_getattr_content_impl(context, builder, typ, val):
                res = builder.extract_value(val, 0)
                return numba.targets.imputils.impl_ret_borrowed(context, builder, typ.content, res)

            @numba.extending.lower_getattr(JaggedArrayType, "starts")
            def jaggedarray_getattr_starts_impl(context, builder, typ, val):
                res = builder.extract_value(val, 1)
                return numba.targets.imputils.impl_ret_borrowed(context, builder, typ.starts, res)

            @numba.extending.lower_getattr(JaggedArrayType, "stops")
            def jaggedarray_getattr_stops_impl(context, builder, typ, val):
                res = builder.extract_value(val, 2)
                return numba.targets.imputils.impl_ret_borrowed(context, builder, typ.stops, res)

        @staticmethod
        def get(content, starts, stops):
            key = (content, starts, stops)
            try:
                return JaggedArrayType.concrete[key]
            except KeyError:
                JaggedArrayType.concrete[key] = JaggedArrayType(content, starts, stops)
                return JaggedArrayType.concrete[key]

        def tupletype(self):
            return numba.types.Tuple((self.content, self.starts, self.stops))

    @numba.extending.typeof_impl.register(JaggedArray)
    def jaggedarray_typeof(val, c):
        assert isinstance(val, JaggedArray)
        return JaggedArrayType.get(numba.typing.typeof._typeof_ndarray(val.content, c),
                                   numba.typing.typeof._typeof_ndarray(val.starts, c),
                                   numba.typing.typeof._typeof_ndarray(val.stops, c))

    @numba.extending.type_callable(JaggedArray)
    def jaggedarray_type(context):
        def typer(content, starts, stops):
            raise TypeError("cannot create JaggedArray object in compiled code (pass it into the function)")
        return typer

    @numba.extending.register_model(JaggedArrayType)
    class JaggedArrayModel(numba.datamodel.models.TupleModel):
        def __init__(self, dmm, fe_type):
            super(JaggedArrayModel, self).__init__(dmm, fe_type.tupletype())

    @numba.extending.infer_getattr
    class StructAttribute(numba.typing.templates.AttributeTemplate):
        key = JaggedArrayType
        def generic_resolve(self, typ, attr):
            if attr == "content":
                return typ.content
            elif attr == "starts":
                return typ.starts
            elif attr == "stops":
                return typ.stops

    @numba.extending.unbox(JaggedArrayType)
    def jaggedarray_unbox(typ, obj, c):
        content_obj = c.pyapi.object_getattr_string(obj, "content")
        starts_obj = c.pyapi.object_getattr_string(obj, "starts")
        stops_obj = c.pyapi.object_getattr_string(obj, "stops")
        tuple_obj = c.pyapi.tuple_new(3)
        c.pyapi.tuple_setitem(tuple_obj, 0, content_obj)
        c.pyapi.tuple_setitem(tuple_obj, 1, starts_obj)
        c.pyapi.tuple_setitem(tuple_obj, 2, stops_obj)
        out = c.unbox(typ.tupletype(), tuple_obj)
        c.pyapi.decref(tuple_obj)
        return out

    @numba.extending.box(JaggedArrayType)
    def jaggedarray_box(typ, val, c):
        class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(JaggedArray))
        args = [c.box(typ.content, c.builder.extract_value(val, 0)),
                c.box(typ.starts, c.builder.extract_value(val, 1)),
                c.box(typ.stops, c.builder.extract_value(val, 2))]
        out = c.pyapi.call_function_objargs(class_obj, args)
        c.pyapi.decref(class_obj)
        return out

    @numba.extending.type_callable(len)
    def jaggedarray_len_type(context):
        def typer(jaggedarray):
            return numba.types.int64  # verified len type
        return typer

    @numba.extending.lower_builtin(len, JaggedArrayType)
    def jaggedarray_len(context, builder, sig, args):
        try:
            len_imp = jaggedarray_len.cache[sig.args]
        except KeyError:
            @numba.njit([sig])
            def _jaggedarray_len(jaggedarray):
                return len(jaggedarray.stops)
            cres, = _jaggedarray_len.overloads.values()
            len_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
            del cres.target_context._defns[cres.entry_point]
            jaggedarray_len.cache[sig.args] = len_imp
        return len_imp(context, builder, sig, args)
    jaggedarray_len.cache = {}

    @numba.typing.templates.infer
    class JaggedArray_getitem(numba.typing.templates.AbstractTemplate):
        key = "getitem"
        def generic(self, args, kwds):
            objtyp, idxtyp = args
            if isinstance(objtyp, JaggedArrayType):
                idxtyp = numba.typing.builtins.normalize_1d_index(idxtyp)
                if isinstance(idxtyp, numba.types.Integer):
                    return numba.typing.templates.signature(objtyp.content, objtyp, idxtyp)

    @numba.extending.lower_builtin("getitem", JaggedArrayType, numba.types.Integer)
    def jaggedarray_getitem(context, builder, sig, args):
        try:
            getitem_imp = jaggedarray_getitem.cache[sig.args]
        except KeyError:
            getitem = numba.njit([sig])(_jaggedarray_getitem)
            cres, = getitem.overloads.values()
            getitem_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
            del cres.target_context._defns[cres.entry_point]
            jaggedarray_getitem.cache[sig.args] = getitem_imp
        return getitem_imp(context, builder, sig, args)
    jaggedarray_getitem.cache = {}

    class JaggedArrayIteratorType(numba.types.common.SimpleIteratorType):
        def __init__(self, jaggedarraytype):
            self.jaggedarray = jaggedarraytype
            name = "iter({0})".format(jaggedarraytype.name)
            super(JaggedArrayIteratorType, self).__init__(name, jaggedarraytype.content)

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
            @numba.njit([jaggedarraytype.content(jaggedarraytype, JaggedArrayIteratorModel.integertype)])
            def _jaggedarray_getitem(a, i):
                return a.content[a.starts[i]:a.stops[i]]
            cres, = _jaggedarray_getitem.overloads.values()
            getitem_imp = cres.target_context.get_function(cres.entry_point, cres.signature)._imp
            del cres.target_context._defns[cres.entry_point]
            jaggedarray_getitem_foriter.cache = getitem_imp
        return jaggedarray_getitem_foriter.cache(context, builder, jaggedarraytype.content(jaggedarraytype, JaggedArrayIteratorModel.integertype), (jaggedarray, index))
    jaggedarray_getitem_foriter.cache = None

    @numba.extending.lower_builtin("iternext", JaggedArrayIteratorType)
    @numba.targets.imputils.iternext_impl
    def jaggedarray_iternext(context, builder, sig, args, result):
        jaggedarraytype = sig.args[0].jaggedarray
        iterobj = context.make_helper(builder, sig.args[0], value=args[0])

        stops = builder.extract_value(iterobj.jaggedarray, 2)
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
