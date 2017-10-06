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

import numpy

import uproot._walker.walker

class XRootDWalker(uproot._walker.walker.Walker):
    def __init__(self, path, index=None, origin=None, reusefile=None):
        try:
            import pyxrootd.client
        except ImportError:
            raise ImportError("\n\nInstall pyxrootd package from source and configure PYTHONPATH and LD_LIBRARY_PATH:\n\n    http://xrootd.org/dload.html\n\nAlternatively, try a conda package:\n\n    https://anaconda.org/search?q=xrootd")

        self.path = path

        if reusefile is None:
            self.file = pyxrootd.client.File()
            status, dummy = self.file.open(self.path)
            if status["error"]:
                raise IOError(status["message"])
        else:
            self.file = reusefile

        if index is not None:
            self.index = index
        else:
            self.index = 0

        self.refs = {}
        if origin is not None:
            self.origin = origin

    def __del__(self):
        del self.file
        del self.refs

    def copy(self, index=None, origin=None):
        if index is None:
            index = self.index
        return XRootDWalker(self.path, index, origin, self.file)
        
    def skip(self, format):
        if isinstance(format, int):
            self.index += format
        else:
            size = self.size(format)
            self.index += size

    def readfields(self, format, index=None):
        if index is not None:
            self.index = index
        size = self.size(format)
        status, data = self.file.read(self.index, size)
        if status["error"]:
            raise IOError(status["message"])
        self.index += size
        return struct.unpack(format, data)

    def readfield(self, format, index=None):
        out, = self.readfields(format, index)
        return out

    def readbytes(self, length, index=None):
        if index is not None:
            self.index = index
        status, data = self.file.read(self.index, length)
        if status["error"]:
            raise IOError(status["message"])
        self.index += length
        return numpy.frombuffer(data, dtype=numpy.uint8)

    def readarray(self, dtype, length, index=None):
        if index is not None:
            self.index = index
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        status, data = self.file.read(self.index, length * dtype.itemsize)
        if status["error"]:
            raise IOError(status["message"])
        self.index += length * dtype.itemsize
        return numpy.frombuffer(data, dtype=dtype)

    def readstring(self, index=None, length=None):
        if index is not None:
            self.index = index
        if length is None:
            status, data = self.file.read(self.index, 1)
            if status["error"]:
                raise IOError(status["message"])
            length = ord(data)
            self.index += 1
            if length == 255:
                status, data = self.file.read(self.index, 4)
                if status["error"]:
                    raise IOError(status["message"])
                length = numpy.frombuffer(data, dtype=">u4")[0]
                self.index += 4
        status, data = self.file.read(self.index, length)
        if status["error"]:
            raise IOError(status["message"])
        self.index += length
        return data

    def readcstring(self, index=None):
        if index is not None:
            self.index = index
        out = []
        while len(out) == 0 or ord(out[-1]) != 0:
            status, data = self.file.read(self.index, 1)
            if status["error"]:
                raise IOError(status["message"])
            self.index += 1
            out.append(data)
        return b"".join(out[:-1])
