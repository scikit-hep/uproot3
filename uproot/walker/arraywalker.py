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

import numpy

import uproot.const

class ArrayWalker(object):
    @staticmethod
    def memmap(filepath, index=0):
        return ArrayWalker(numpy.memmap(filepath, dtype=numpy.uint8, mode="r"), index)

    @staticmethod
    def size(format):
        return struct.calcsize(format)

    def _evaluate(self):
        pass

    def _unevaluate(self):
        pass

    def __init__(self, data, index=0, origin=None):
        self.data = data
        self.index = index
        self.refs = {}
        if origin is not None:
            self.origin = origin

    def copy(self, index=None, origin=None):
        if index is None:
            index = self.index
        out = ArrayWalker(self.data, index, origin)
        return out

    def skip(self, format):
        if isinstance(format, int):
            self.index += format
        else:
            self.index += self.size(format)

    def fields(self, format, index=None, read=False):
        if index is None:
            index = self.index
        start = index
        end = index + self.size(format)
        if read:
            self.index = end
        return struct.unpack(format, self.data[start:end])

    def readfields(self, format, index=None):
        return self.fields(format, index, True)

    def field(self, format, index=None, read=False):
        out, = self.fields(format, index, read)
        return out

    def readfield(self, format, index=None):
        out, = self.fields(format, index, True)
        return out

    def bytes(self, length, index=None, read=False):
        if index is None:
            index = self.index
        start = index
        end = index + length
        if read:
            self.index = end
        return self.data[start:end]

    def readbytes(self, length, index=None):
        return self.bytes(length, index, True)

    def array(self, dtype, length, index=None, read=False):
        if index is None:
            index = self.index
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        start = index
        end = index + length * dtype.itemsize
        if read:
            self.index = end
        return self.data[start:end].view(dtype)

    def readarray(self, dtype, length, index=None):
        return self.array(dtype, length, index, True)

    def string(self, index=None, length=None, read=False):
        if index is None:
            index = self.index
        if length is None:
            length = self.data[index]
            index += 1
            if length == 255:
                length = self.data[index : index + 4].view(numpy.uint32)
                index += 4
        end = index + length
        if read:
            self.index = end
        return self.data[index : end].tostring()

    def readstring(self, index=None, length=None):
        return self.string(index, length, True)

    def cstring(self, index=None, read=False):
        if index is None:
            index = self.index
        start = index
        end = index
        while self.data[end] != 0:
            end += 1
        if read:
            self.index = end + 1
        return self.data[start:end].tostring()

    def readcstring(self, index=None):
        return self.cstring(index, True)

    def readversion(self):
        bcnt, vers = self.readfields("!IH")
        bcnt = int(numpy.int64(bcnt) & ~uproot.const.kByteCountMask)
        if bcnt == 0:
            raise IOError("readversion byte count is zero")
        return vers, bcnt

    def skipversion(self):
        version = self.readfield("!h")
        if numpy.int64(version) & uproot.const.kByteCountVMask:
            self.skip("!hh")

    def skiptobject(self):
        id, bits = self.readfields("!II")
        bits = numpy.uint32(bits) | uproot.const.kIsOnHeap
        if bits & uproot.const.kIsReferenced:
            self.skip("!H")
