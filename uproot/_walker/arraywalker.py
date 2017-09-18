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
                # is this a ROOT thing or a Go thing? shouldn't it be big-endian?
                length = self.data[index : index + 4].view(numpy.uint32)[0]
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
