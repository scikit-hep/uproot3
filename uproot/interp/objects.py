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

import awkward.type
import awkward.util
import awkward.array.virtual

import uproot.interp.interp
import uproot.interp.numerical
import uproot.interp.jagged

class ObjectArray(awkward.array.virtual.ObjectArray):
    pass

class STLVectorObjectArray(ObjectArray):
    pass

class STLVector(object):
    def __init__(self, cls):
        self.cls = cls

    def __repr__(self):
        return "STLVector({0})".format(self.cls)

    _indexdtype = awkward.util.numpy.dtype(">i4")

    def __call__(self, bytes):
        raise NotImplementedError

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
        return VirtualObjectArray(self.content.empty(), self.generator, *self.args, **self.kwargs)

    def compatible(self, other):
        return isinstance(other, asobj) and self.content.compatible(other) and self.generator == other.generator and self.args == other.args and self.kwargs == other.kwargs

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
        return ObjectArray(self.content.finalize(destination, branch), self.generator, *self.args, **self.kwargs)

class asobj(_variable):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (_variable.__metaclass__,), {})

    def __init__(self, cls):
        super(asobj, self).__init__(uproot.interp.jagged.asjagged(uproot.interp.numerical.asdtype(awkward.util.CHARTYPE)), cls)

    def __repr__(self):
        return "asobj({0})".format(self.generator)

class asstring(_variable):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (_variable.__metaclass__,), {})

    def __init__(self):
        super(asstring, self).__init__(uproot.interp.jagged.asjagged(uproot.interp.numerical.asdtype(awkward.util.CHARTYPE), skipbytes=1), bytes)

    def __repr__(self):
        return "asstring()"

class ascharstring(asstring):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (asstring.__metaclass__,), {})

    def __init__(self):
        super(asstring, self).__init__(uproot.interp.jagged.asjagged(uproot.interp.numerical.asdtype(awkward.util.CHARTYPE), skipbytes=4), bytes)

    def __repr__(self):
        return "ascharstring()"

class asstlstring(asstring):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (asstring.__metaclass__,), {})

    def __init__(self):
        super(asstring, self).__init__(uproot.interp.jagged.asjagged(uproot.interp.numerical.asdtype(awkward.util.CHARTYPE), skipbytes=7), bytes)

    def __repr__(self):
        return "asstlstring()"
