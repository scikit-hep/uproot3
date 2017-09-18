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

class LocalFileWalker(uproot._walker.walker.Walker):
    def __init__(self, localpath, index=None, origin=None, reusefile=None):
        if reusefile is None:
            self.path = os.path.abspath(os.path.expanduser(localpath))
            self.file = None
        else:
            self.path = localpath
            self.file = reusefile

        if index is not None:
            self.index = index
        elif self.file is not None:
            self.index = self.file.tell()
        else:
            self.index = 0

        self.refs = {}
        if origin is not None:
            self.origin = origin

    def __del__(self):
        del self.file
        del self.refs

    def _evaluate(self, parallel=False):
        self._holdfile = self.file
        if parallel:
            self.file = None

    def _unevaluate(self):
        if self.file is not self._holdfile:
            self.file.close()
        self.file = self._holdfile

    def startcontext(self):
        if self.file is None:
            self.file = open(self.path, "rb")
        self.file.seek(self.index)

    def copy(self, index=None, origin=None):
        if index is None:
            index = self.index
        return LocalFileWalker(self.path, index, origin, self.file)
        
    def skip(self, format):
        if isinstance(format, int):
            self.index += format
            self.file.seek(format, 1)
        else:
            size = self.size(format)
            self.index += size
            self.file.seek(size, 1)

    def readfields(self, format, index=None):
        if index is not None:
            self.index = index
            self.file.seek(index)
        size = self.size(format)
        self.index += size
        return struct.unpack(format, self.file.read(size))

    def readfield(self, format, index=None):
        out, = self.readfields(format, index)
        return out

    def readbytes(self, length, index=None):
        if index is not None:
            self.index = index
            self.file.seek(index)
        self.index += length
        return numpy.frombuffer(self.file.read(length), dtype=numpy.uint8)

    def readarray(self, dtype, length, index=None):
        if index is not None:
            self.index = index
            self.file.seek(index)
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        self.index += length * dtype.itemsize
        return numpy.frombuffer(self.file.read(length * dtype.itemsize), dtype=dtype)

    def readstring(self, index=None, length=None):
        if index is not None:
            self.index = index
            self.file.seek(index)
        if length is None:
            length = ord(self.file.read(1))
            self.index += 1
            if length == 255:
                length = numpy.frombuffer(self.file.read(4), dtype=numpy.uint32)[0]
                self.index += 4
        self.index += length
        return self.file.read(length)

    def readcstring(self, index=None):
        if index is not None:
            self.index = index
            self.file.seek(index)
        out = []
        while len(out) == 0 or ord(out[-1]) != 0:
            self.index += 1
            out.append(self.file.read(1))
        return b"".join(out[:-1])
