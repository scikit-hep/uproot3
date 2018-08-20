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

import awkward.array.virtual

import uproot.interp.interp

class aswrapped(uproot.interp.interp.Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.interp.interp.Interpretation.__metaclass__,), {})

    def __init__(self, content, cls):
        self.content = content
        self.cls = type("{0}.{1}".format(cls.__module__, cls.__name__), (awkward.array.virtual.WrappedArray, cls), {})

    def __repr__(self):
        return "aswrapped({0})".format(repr(self.cls))

    def identifier(self):
        return "aswrapped({0},{1})".format(repr(self.content), repr(self.cls))

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
        return awkward.array.virtual.WrappedArray(self.content.finalize(destination, branch), self.cls)
