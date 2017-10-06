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

