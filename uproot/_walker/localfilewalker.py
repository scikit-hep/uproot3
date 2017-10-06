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
                length = numpy.frombuffer(self.file.read(4), dtype=">u4")[0]
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
