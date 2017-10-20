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

class Cursor(object):
    def __init__(self, index, origin=0, refs=None):
        self.index = index
        self.origin = origin
        if refs is None:
            self.refs = {}
        else:
            self.refs = refs

    def copied(self, index=None, origin=None, refs=None):
        if index is None:
            index = self.index
        if origin is None:
            origin = self.origin
        if refs is None:
            refs = self.refs
        return Cursor(index, origin, refs)

    def skipped(self, numbytes, origin=None, refs=None):
        if origin is None:
            origin = self.origin
        if refs is None:
            refs = self.refs
        return Cursor(self.index + numbytes, origin, refs)

    def skip(self, numbytes):
        self.index += numbytes

    def fields(self, source, format):
        start = self.index
        stop = self.index = start + format.size
        return format.unpack(source.data(start, stop))

    def field(self, source, format):
        return self.readfields(source, format)[0]

    def bytes(self, source, length):
        start = self.index
        stop = self.index = start + length
        return source.data(start, stop)

    def array(self, source, length, dtype):
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        start = self.index
        stop = self.index = start + length*dtype.itemsize
        return source.data(start, stop, dtype)

    def string(self, source):
        start = self.index
        stop = self.index = start + 1
        length = source.data(start, stop)[0]
        if length == 255:
            start = self.index
            stop = self.index = start + 4
            length = source.data(start, stop, numpy.dtype(">u4"))[0]
        start = self.index
        stop = self.index = start + length
        return source.data(start, stop).tostring()

    def cstring(self, source):
        char = None
        chars = []
        while char != 0:
            char = source.data(self.index, self.index + 1)
            chars.append(char)
            self.index += 1
        return "".join(chars)
