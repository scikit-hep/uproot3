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

import uproot._walker.arraywalker

class LazyArrayWalker(uproot._walker.arraywalker.ArrayWalker):
    def __init__(self, walker, function, length, origin=None):
        self._original_walker   = walker
        self._original_function = function
        self._original_length   = length
        self._original_origin   = origin
        self._evaluated         = False
        self.index = 0

    def _evaluate(self, parallel=False):
        walker   = self._original_walker
        function = self._original_function
        length   = self._original_length
        origin   = self._original_origin

        walker._evaluate(parallel)
        walker.startcontext()
        start = walker.index
        try:
            string = self._original_function(walker.readbytes(length))
        finally:
            walker.index = start
            walker._unevaluate()

        uproot._walker.arraywalker.ArrayWalker.__init__(self, numpy.frombuffer(string, dtype=numpy.uint8), 0, origin=origin)
        self._evaluated = True

    def _unevaluate(self):
        del self.data
        del self.index
        del self.refs
        if hasattr(self, "origin"):
            del self.origin
        self._evaluated = False

    def __del__(self):
        if hasattr(self, "data"):
            del self.data
        if hasattr(self, "refs"):
            del self.refs
        del self._original_walker

    def copy(self, index=None, origin=None, parallel=False):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).copy(index, origin)

    def skip(self, format):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).skip(format)

    def readfields(self, format, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readfields(format, index)

    def readfield(self, format, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readfield(format, index)

    def readbytes(self, length, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readbytes(length, index)

    def readarray(self, dtype, length, index=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readarray(dtype, length, index)

    def readstring(self, index=None, length=None):
        if not self._evaluated: self._evaluate()
        return super(LazyArrayWalker, self).readstring(index, length)

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

