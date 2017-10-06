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
import os.path

import numpy

import uproot._walker.walker

class ArrayWalker(uproot._walker.walker.Walker):
    @staticmethod
    def memmap(localpath, index=0):
        out = ArrayWalker(numpy.memmap(os.path.expanduser(localpath), dtype=numpy.uint8, mode="r"), index)
        out.path = localpath
        return out

    def __init__(self, data, index=None, origin=None):
        self.data = data
        if index is None:
            self.index = 0
        else:
            self.index = index
        self.refs = {}
        if origin is not None:
            self.origin = origin

    def __del__(self):
        del self.data
        del self.refs

    def copy(self, index=None, origin=None, parallel=False):
        if index is None:
            index = self.index
        out = ArrayWalker(self.data, index, origin)
        return out

    def skip(self, format):
        if isinstance(format, int):
            self.index += format
        else:
            self.index += self.size(format)

    def readfields(self, format, index=None):
        if index is None:
            index = self.index
        start = index
        end = index + self.size(format)
        self.index = end
        return struct.unpack(format, self.data[start:end])

    def readfield(self, format, index=None):
        out, = self.readfields(format, index)
        return out

    def readbytes(self, length, index=None):
        if index is None:
            index = self.index
        start = index
        end = index + length
        self.index = end
        return self.data[start:end]

    def readarray(self, dtype, length, index=None):
        if index is None:
            index = self.index
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        start = index
        end = index + length * dtype.itemsize
        self.index = end
        return self.data[start:end].view(dtype)

    def readstring(self, index=None, length=None):
        if index is None:
            index = self.index
        if length is None:
            length = self.data[index]
            index += 1
            if length == 255:
                length = self.data[index : index + 4].view(">u4")[0]
                index += 4
        end = index + length
        self.index = end
        return self.data[index : end].tostring()

    def readcstring(self, index=None):
        if index is None:
            index = self.index
        start = index
        end = index
        while self.data[end] != 0:
            end += 1
        self.index = end + 1
        return self.data[start:end].tostring()
