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

import struct

import awkward
import awkward.type
import awkward.util

import uproot.interp.interp
import uproot.interp.numerical
import uproot.interp.jagged

class SimpleArray(object):
    def __init__(self, cls):
        self.cls = cls

    def __repr__(self):
        if isinstance(self.cls, type):
            return "SimpleArray({0})".format(self.cls.__name__)
        else:
            return "SimpleArray({0})".format(repr(self.cls))

    def read(self, source, cursor, context, parent):
        out = []
        while True:
            try:
                out.append(self.cls.read(source, cursor, context, parent))
            except IndexError:
                return out

class STLVector(object):
    def __init__(self, cls):
        self.cls = cls

    def __repr__(self):
        if isinstance(self.cls, type):
            return "STLVector({0})".format(self.cls.__name__)
        else:
            return "STLVector({0})".format(repr(self.cls))

    _format1 = struct.Struct(">i")

    def read(self, source, cursor, context, parent):
        numitems = cursor.field(source, self._format1)
        if isinstance(self.cls, uproot.interp.numerical.asdtype):
            out = cursor.array(source, numitems, self.cls.fromdtype)
            if out.dtype != self.cls.todtype:
                out = out.astype(self.cls.todtype)
            return list(out)
        else:
            out = [None] * numitems
            for i in range(numitems):
                out[i] = self.cls.read(source, cursor, context, parent)
            return out

class STLString(object):
    def __init__(self):
        pass

    def __repr__(self):
        return "STLString()"

    _format1 = struct.Struct("B")

    def read(self, source, cursor, context, parent):
        numitems = cursor.field(source, self._format1)
        return cursor.array(source, numitems, awkward.util.CHARTYPE).tostring()

class astable(uproot.interp.interp.Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.interp.interp.Interpretation.__metaclass__,), {})

    def __init__(self, content):
        if not isinstance(content, uproot.interp.numerical.asdtype) or content.todtype.names is None or len(content.todtype.names) == 0:
            raise TypeError("astable must be given a recarray dtype")
        self.content = content

    @property
    def itemsize(self):
        return self.content.itemsize

    def __repr__(self):
        dtype, shape = uproot.interp.numerical._dtypeshape(self.content.todtype)
        return "astable({0})".format(repr(self.content.to(awkward.util.numpy.dtype([(n, dtype[n]) for n in dtype.names if not n.startswith(" ")]), shape)))

    def tonumpy(self):
        return self.content

    @property
    def identifier(self):
        dtype, shape = uproot.interp.numerical._dtypeshape(self.content.todtype)
        return "astable({0})".format(self.content.to(awkward.util.numpy.dtype([(n, dtype[n]) for n in dtype.names if not n.startswith(" ")]), shape).identifier)

    @property
    def type(self):
        dtype, shape = uproot.interp.numerical._dtypeshape(self.content.todtype)
        fields = None
        for n in dtype.names:
            if fields is None:
                fields = awkward.type.ArrayType(n, dtype[n])
            else:
                fields = fields & awkward.type.ArrayType(n, dtype[n])
        if shape == ():
            return fields
        else:
            return awkward.type.ArrayType(*(shape + (fields,)))

    def empty(self):
        return awkward.Table.fromrec(self.content.empty())

    def compatible(self, other):
        return isinstance(other, astable) and self.content.compatible(other.content)

    def numitems(self, numbytes, numentries):
        return self.content.numitems(numbytes, numentries)

    def source_numitems(self, source):
        return self.content.source_numitems(source)

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        return self.content.fromroot(data, byteoffsets, local_entrystart, local_entrystop)

    def destination(self, numitems, numentries):
        return self.content.destination(numitems, numentries)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.fill(source, destination, itemstart, itemstop, entrystart, entrystop)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.clip(destination, itemstart, itemstop, entrystart, entrystop)

    def finalize(self, destination, branch):
        return awkward.Table.fromrec(self.content.finalize(destination, branch))

class asobj(uproot.interp.interp.Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.interp.interp.Interpretation.__metaclass__,), {})

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
        return self.content.compatible(other)

    def numitems(self, numbytes, numentries):
        return self.content.numitems(numbytes, numentries)

    def source_numitems(self, source):
        return self.content.source_numitems(source)

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        return self.content.fromroot(data, byteoffsets, local_entrystart, local_entrystop)

    def destination(self, numitems, numentries):
        return self.content.destination(numitems, numentries)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.fill(source, destination, itemstart, itemstop, entrystart, entrystop)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.clip(destination, itemstart, itemstop, entrystart, entrystop)

    def finalize(self, destination, branch):
        if self.cls._arraymethods is None:
            return awkward.ObjectArray(self.content.finalize(destination, branch), self.cls._fromrow)
        else:
            cls = awkward.Methods.mixin(self.cls._arraymethods, awkward.ObjectArray)
            out = cls.__new__(cls)
            out._initObjectArray(self.content.finalize(destination, branch))
            return out
            
class _variable(uproot.interp.interp.Interpretation):
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
        return awkward.ObjectArray(self.content.empty(), self.generator, *self.args, **self.kwargs)

    def compatible(self, other):
        return isinstance(other, _variable) and self.content.compatible(other) and self.generator == other.generator and self.args == other.args and self.kwargs == other.kwargs

    def numitems(self, numbytes, numentries):
        return self.content.numitems(numbytes, numentries)

    def source_numitems(self, source):
        return self.content.source_numitems(source)

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        return self.content.fromroot(data, byteoffsets, local_entrystart, local_entrystop)

    def destination(self, numitems, numentries):
        return self.content.destination(numitems, numentries)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.fill(source, destination, itemstart, itemstop, entrystart, entrystop)

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        return self.content.clip(destination, itemstart, itemstop, entrystart, entrystop)

    def finalize(self, destination, branch):
        return awkward.ObjectArray(self.content.finalize(destination, branch), self.generator, *self.args, **self.kwargs)

class asgenobj(_variable):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (_variable.__metaclass__,), {})

    class _Wrapper(object):
        def __init__(self, cls, context):
            self.cls = cls
            self.context = context
        def __call__(self, bytes):
            source = uproot.source.source.Source(bytes)
            cursor = uproot.source.cursor.Cursor(0)
            return self.cls.read(source, cursor, self.context, None)
        def __repr__(self):
            if isinstance(self.cls, type):
                return self.cls.__name__
            else:
                return repr(self.cls)

    def __init__(self, cls, context, skipbytes):
        super(asgenobj, self).__init__(uproot.interp.jagged.asjagged(uproot.interp.numerical.asdtype(awkward.util.CHARTYPE), skipbytes=skipbytes), asgenobj._Wrapper(cls, context))

    def __repr__(self):
        return "asgenobj({0})".format(self.generator)

class asstring(_variable):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (_variable.__metaclass__,), {})

    def __init__(self, skipbytes=1):
        super(asstring, self).__init__(uproot.interp.jagged.asjagged(uproot.interp.numerical.asdtype(awkward.util.CHARTYPE), skipbytes=skipbytes), lambda array: array.tostring())

    def __repr__(self):
        return "asstring({0})".format("" if self.content.skipbytes == 1 else repr(self.content.skipbytes))

    def compatible(self, other):
        return isinstance(other, asstring)
