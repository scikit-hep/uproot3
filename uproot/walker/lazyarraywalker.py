#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy

import uproot.walker.arraywalker

class LazyArrayWalker(uproot.walker.arraywalker.ArrayWalker):
    def __init__(self, walker, function, length, index, origin=None):
        self._original_walker   = walker
        self._original_function = function
        self._original_length   = length
        self._original_index    = index
        self._original_origin   = origin
        self._evaluated         = False

        self.index = 0

    def _evaluate(self):
        walker   = self._original_walker
        function = self._original_function
        length   = self._original_length
        index    = self._original_index
        origin   = self._original_origin
        
        string = self._original_function(walker.bytes(length, index))
        uproot.walker.arraywalker.ArrayWalker.__init__(self, numpy.frombuffer(string, dtype=numpy.uint8), 0, origin=origin)
        self._evaluated = True

    def _unevaluate(self):
        del self.data
        del self.index
        del self.refs
        if hasattr(self, "origin"):
            del self.origin
        self._evaluated = False

    def copy(self, index=None, origin=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).copy(index, origin)

    def skip(self, format):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).skip(format)

    def fields(self, format, index=None, read=False):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).fields(format, index, read)

    def readfields(self, format, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readfields(format, index)

    def field(self, format, index=None, read=False):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).field(format, index, read)

    def readfield(self, format, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readfield(format, index)

    def bytes(self, length, index=None, read=False):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).bytes(length, index, read)

    def readbytes(self, length, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readbytes(length, index)

    def array(self, dtype, length, index=None, read=False):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).array(dtype, length, index, read)

    def readarray(self, dtype, length, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readarray(dtype, length, index)

    def string(self, index=None, length=None, read=False):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).string(index, length, read)

    def readstring(self, index=None, length=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readstring(index, length)

    def cstring(self, index=None, read=False):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).cstring(index, read)

    def readcstring(self, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readcstring(index)

    def readversion(self):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readversion()

    def skipversion(self):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).skipversion()

    def skiptobject(self):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).skiptobject()

