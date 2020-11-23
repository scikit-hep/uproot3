#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

from __future__ import absolute_import

import copy
import struct
import numbers

import numpy

import uproot3.rootio
import uproot3.interp.interp
import uproot3.interp.numerical
import uproot3.interp.jagged

from uproot3._util import _tobytes

class SimpleArray(object):
    def __init__(self, cls):
        self.cls = cls

    @property
    def __name__(self):
        return "SimpleArray"

    def __repr__(self):
        if isinstance(self.cls, type):
            return "SimpleArray({0})".format(self.cls.__name__)
        else:
            return "SimpleArray({0})".format(repr(self.cls))

    def read(self, source, cursor, context, parent):
        out = []
        while True:
            if hasattr(source, "_source") and cursor.index >= len(source._source):
                return out
            try:
                out.append(self.cls.read(source, cursor, context, parent))
            except IndexError:
                return out

class STLVector(object):
    def __init__(self, cls):
        self.cls = cls

    @property
    def __name__(self):
        return "STLVector"

    def __repr__(self):
        if isinstance(self.cls, type):
            return "STLVector({0})".format(self.cls.__name__)
        else:
            return "STLVector({0})".format(repr(self.cls))

    _format1 = struct.Struct(">i")

    def read(self, source, cursor, context, parent):
        if hasattr(source, "_source") and len(source._source) == 0:
            return []
        numitems = cursor.field(source, self._format1)
        if isinstance(self.cls, uproot3.interp.numerical.asdtype):
            out = cursor.array(source, numitems, self.cls.fromdtype)
            if out.dtype != self.cls.todtype:
                out = out.astype(self.cls.todtype)
            return list(out)
        else:
            out = [None] * numitems
            for i in range(numitems):
                out[i] = self.cls.read(source, cursor, context, parent)
            return out

class STLMap(object):
    def __init__(self, keycls, valcls):
        self.keycls = keycls
        self.valcls = valcls

    @property
    def __name__(self):
        return "STLMap"

    def __repr__(self):
        key = self.keycls.__name__ if isinstance(self.keycls, type) else repr(self.keycls)
        val = self.valcls.__name__ if isinstance(self.valcls, type) else repr(self.valcls)
        return "STLMap({0}, {1})".format(key, val)

    _format1 = struct.Struct(">i")

    def read(self, source, cursor, context, parent):
        numitems = cursor.field(source, self._format1)

        out = {}
        for i in range(numitems):
            if isinstance(self.keycls, uproot3.interp.numerical.asdtype):
                key = cursor.array(source, 1, self.keycls.fromdtype)
                if key.dtype != self.keycls.todtype:
                    key = key.astype(self.keycls.todtype)
                key = key[0]
            else:
                key = self.keycls.read(source, cursor, context, parent)

            if isinstance(self.valcls, uproot3.interp.numerical.asdtype):
                val = cursor.array(source, 1, self.valcls.fromdtype)
                if val.dtype != self.valcls.todtype:
                    val = val.astype(self.valcls.todtype)
                val = val[0]
            else:
                val = self.valcls.read(source, cursor, context, parent)

            out[key] = val

        return out

class STLString(object):
    def __init__(self, awkward0=None):
        if awkward0 is None:
            awkward0 = uproot3.interp.interp.Interpretation.awkward0
        self.awkward0 = awkward0

    @property
    def __name__(self):
        return "STLString"

    def __repr__(self):
        return "STLString()"

    _format1 = struct.Struct("B")
    _format2 = struct.Struct(">i")

    def read(self, source, cursor, context, parent):
        numitems = cursor.field(source, self._format1)
        if numitems == 255:
            numitems = cursor.field(source, self._format2)
        return _tobytes(cursor.array(source, numitems, self.awkward0.ObjectArray.CHARTYPE))

class Pointer(object):
    def __init__(self, cls):
        self.cls = cls

    @property
    def __name__(self):
        return "Pointer"

    def __repr__(self):
        if isinstance(self.cls, type):
            return "Pointer({0})".format(self.cls.__name__)
        else:
            return "Pointer({0})".format(repr(self.cls))

    def read(self, source, cursor, context, parent):
        return uproot3.rootio._readobjany(source, cursor, context, parent)

    _format1 = struct.Struct(">II")

class astable(uproot3.interp.interp.Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot3.interp.interp.Interpretation.__metaclass__,), {})

    def __init__(self, content):
        if not isinstance(content, uproot3.interp.numerical.asdtype) or content.todtype.names is None or len(content.todtype.names) == 0:
            raise TypeError("astable must be given a recarray dtype")
        self.content = content

    @property
    def itemsize(self):
        return self.content.itemsize

    def __repr__(self):
        dtype, shape = uproot3.interp.numerical._dtypeshape(self.content.todtype)
        return "astable({0})".format(repr(self.content.to(self.awkward0.util.numpy.dtype([(n, dtype[n]) for n in dtype.names if not n.startswith(" ")]), shape)))

    def tonumpy(self):
        return self.content

    @property
    def identifier(self):
        dtype, shape = uproot3.interp.numerical._dtypeshape(self.content.todtype)
        return "astable({0})".format(self.content.identifier)

    @property
    def type(self):
        dtype, shape = uproot3.interp.numerical._dtypeshape(self.content.todtype)
        fields = None
        for n in dtype.names:
            if fields is None:
                fields = self.awkward0.type.ArrayType(n, dtype[n])
            else:
                fields = fields & self.awkward0.type.ArrayType(n, dtype[n])
        if shape == ():
            return fields
        else:
            return self.awkward0.type.ArrayType(*(shape + (fields,)))

    def empty(self):
        return self.awkward0.Table.fromrec(self.content.empty())

    def compatible(self, other):
        return isinstance(other, astable) and self.content.compatible(other.content)

    def numitems(self, numbytes, numentries):
        return self.content.numitems(numbytes, numentries)

    def source_numitems(self, source):
        return self.content.source_numitems(source)

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop, keylen):
        return self.content.fromroot(data, byteoffsets, local_entrystart, local_entrystop, keylen)

    def destination(self, numitems, numentries):
        return self.content.destination(numitems, numentries)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.fill(source, destination, itemstart, itemstop, entrystart, entrystop)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.clip(destination, itemstart, itemstop, entrystart, entrystop)

    def finalize(self, destination, branch):
        out = self.awkward0.Table.fromrec(self.content.finalize(destination, branch))
        if self.debug_reading:
            print("reading {0}".format(repr(out)))
        return out

class asobj(uproot3.interp.interp.Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot3.interp.interp.Interpretation.__metaclass__,), {})

    def __init__(self, content, cls):
        self.content = content
        self.cls = cls

    @property
    def itemsize(self):
        return self.content.itemsize

    def __repr__(self):
        return "asobj(<{0}.{1}>)".format(self.cls.__module__, self.cls.__name__)

    @property
    def identifier(self):
        return "asobj({0},{1}.{2})".format(self.content.identifier, self.cls.__module__, self.cls.__name__)

    @property
    def type(self):
        return self.cls

    def empty(self):
        return self.content.empty()

    def compatible(self, other):
        return isinstance(other, asobj) and self.cls.__name__ == other.cls.__name__

    def numitems(self, numbytes, numentries):
        return self.content.numitems(numbytes, numentries)

    def source_numitems(self, source):
        return self.content.source_numitems(source)

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop, keylen):
        return self.content.fromroot(data, byteoffsets, local_entrystart, local_entrystop, keylen)

    def destination(self, numitems, numentries):
        return self.content.destination(numitems, numentries)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.fill(source, destination, itemstart, itemstop, entrystart, entrystop)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.clip(destination, itemstart, itemstop, entrystart, entrystop)

    def finalize(self, destination, branch):
        if self.cls._arraymethods is None:
            out = self.awkward0.ObjectArray(self.content.finalize(destination, branch), self.cls._fromrow)
        else:
            cls = self.awkward0.Methods.mixin(self.cls._arraymethods, self.awkward0.ObjectArray)
            out = cls.__new__(cls)
            out._initObjectArray(self.content.finalize(destination, branch))
        if self.debug_reading:
            print("reading {0}".format(repr(out)))
        return out

class _variable(uproot3.interp.interp.Interpretation):
    def __init__(self, content, generator, *args, **kwargs):
        self.content = content
        self.generator = generator
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return "_variable({0}, {1}{2}{3})".format(repr(self.content), self.generator, "".join(", " + repr(x) for x in self.args), "".join(", {0}={1}".format(n, repr(x)) for n, x in self.kwargs.items()))

    @property
    def identifier(self):
        return "_variable({0},{1}{2}{3})".format(self.content.identifier, self.generator, "".join("," + repr(x) for x in self.args), "".join(",{0}={1}".format(n, repr(self.kwargs[n])) for n in sorted(self.kwargs)))

    @property
    def type(self):
        return self.generator

    def empty(self):
        return self.awkward0.ObjectArray(self.content.empty(), self.generator, *self.args, **self.kwargs)

    def compatible(self, other):
        return isinstance(other, _variable) and self.content.compatible(other) and self.generator == other.generator and self.args == other.args and self.kwargs == other.kwargs

    def numitems(self, numbytes, numentries):
        return self.content.numitems(numbytes, numentries)

    def source_numitems(self, source):
        return self.content.source_numitems(source)

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop, keylen):
        return self.content.fromroot(data, byteoffsets, local_entrystart, local_entrystop, keylen)

    def destination(self, numitems, numentries):
        return self.content.destination(numitems, numentries)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        self.content.fill(source, destination, itemstart, itemstop, entrystart, entrystop)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.clip(destination, itemstart, itemstop, entrystart, entrystop)

    def finalize(self, destination, branch):
        out = self.awkward0.ObjectArray(self.content.finalize(destination, branch), self.generator, *self.args, **self.kwargs)
        if self.debug_reading:
            print("reading {0}".format(repr(out)))
        return out

class _variable_withoffsets(_variable):
    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop, keylen):
        out = self.content.fromroot(data, byteoffsets, local_entrystart, local_entrystop, keylen)
        out.byteoffsets = byteoffsets[local_entrystart:local_entrystop] + keylen + self.content.skipbytes
        return out

    def destination(self, numitems, numentries):
        out = self.content.destination(numitems, numentries)
        out.byteoffsets = self.awkward0.numpy.empty(numentries, dtype=self.awkward0.numpy.int32)
        return out

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        self.content.fill(source, destination, itemstart, itemstop, entrystart, entrystop)
        destination.byteoffsets[entrystart:entrystop] = source.byteoffsets

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        out = self.content.clip(destination, itemstart, itemstop, entrystart, entrystop)
        out.byteoffsets = destination.byteoffsets[entrystart:entrystop]
        return out

    def finalize(self, destination, branch):
        out = self.awkward0.ObjectArray(JaggedWithByteOffsets(self.content.finalize(destination, branch), destination.byteoffsets), self.generator, *self.args, **self.kwargs)
        if self.debug_reading:
            print("reading {0}".format(repr(out)))
        return out

class JaggedWithByteOffsets(object):
    def __init__(self, jagged, byteoffsets):
        self.jagged = jagged
        self.byteoffsets = byteoffsets

    def __len__(self):
        return len(self.jagged)

    def __getitem__(self, where):
        return self.jagged[where], -self.byteoffsets[where]

class asgenobj(_variable_withoffsets):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (_variable.__metaclass__,), {})

    class _Wrapper(object):
        def __init__(self, cls, context):
            self.cls = cls
            self.context = context
        def __call__(self, arg):
            bytes, origin = arg
            source = uproot3.source.source.Source(bytes)
            cursor = uproot3.source.cursor.Cursor(0, origin=origin)
            return self.cls.read(source, cursor, self.context, None)
        def __repr__(self):
            if isinstance(self.cls, type):
                return self.cls.__name__
            else:
                return repr(self.cls)

    def __init__(self, cls, context, skipbytes):
        super(asgenobj, self).__init__(uproot3.interp.jagged.asjagged(uproot3.interp.numerical.asdtype(self.awkward0.ObjectArray.CHARTYPE), skipbytes=skipbytes), asgenobj._Wrapper(cls, context))

    def speedbump(self, value):
        out = copy.copy(self)
        out.generator = copy.copy(self.generator)
        out.generator.context = copy.copy(out.generator.context)
        out.generator.context.speedbump = value
        return out

    def compatible(self, other):
        return isinstance(other, asgenobj) and self.generator.cls.__name__ == other.generator.cls.__name__

    def __repr__(self):
        return "asgenobj({0})".format(self.generator)

class asstring(_variable):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (_variable.__metaclass__,), {})

    def __init__(self, skipbytes=1):
        super(asstring, self).__init__(uproot3.interp.jagged.asjagged(uproot3.interp.numerical.asdtype(self.awkward0.ObjectArray.CHARTYPE), skipbytes=skipbytes), lambda array: _tobytes(array))

    def __repr__(self):
        return "asstring({0})".format("" if self.content.skipbytes == 1 else repr(self.content.skipbytes))
    @property
    def identifier(self):
        return "asstring({0})".format("" if self.content.skipbytes == 1 else repr(self.content.skipbytes))

    def compatible(self, other):
        return isinstance(other, asstring)
