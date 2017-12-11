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

import os.path

import numpy

import uproot.cache.memorycache
import uproot.source.chunked

class FileSource(uproot.source.chunked.ChunkedSource):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.source.chunked.ChunkedSource.__metaclass__,), {})

    @staticmethod
    def defaults(path):
        return FileSource(path, chunkbytes=8*1024, limitbytes=1024**2)

    def __init__(self, path, *args, **kwds):
        self._size = None
        super(FileSource, self).__init__(os.path.expanduser(path), *args, **kwds)

    def size(self):
        if self._size is None:
            self._size = os.path.getsize(self.path)
        return self._size

    def threadlocal(self):
        out = FileSource.__new__(self.__class__)
        out.path = self.path
        out._chunkbytes = self._chunkbytes
        if isinstance(self.cache, (uproot.cache.memorycache.ThreadSafeMemoryCache, uproot.cache.memorycache.ThreadSafeDict)):
            out.cache = self.cache
        else:
            out.cache = {}
        out._source = None             # local file connections are *not shared* among threads (they're *not* thread-safe)
        return out

    def _open(self):
        if self._source is None or self._source.closed:
            self._source = open(self.path, "rb")

    def _read(self, chunkindex):
        self._source.seek(chunkindex * self._chunkbytes)
        return numpy.frombuffer(self._source.read(self._chunkbytes), dtype=numpy.uint8)
    
    def dismiss(self):
        if self._source is not None:
            self._source.close()       # local file connections are *not shared* among threads
