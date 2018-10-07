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

import uproot.cache
import uproot.source.source

class ChunkedSource(uproot.source.source.Source):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.source.source.Source.__metaclass__,), {})

    def __init__(self, path, chunkbytes, limitbytes):
        self.path = path
        self._chunkbytes = chunkbytes
        if limitbytes is None:
            self.cache = {}
        else:
            self.cache = uproot.cache.ThreadSafeArrayCache(limitbytes)
        self._source = None

    def parent(self):
        return self

    def threadlocal(self):
        return self

    def __del__(self):
        self.dismiss()

    def _read(self, chunkindex):
        raise NotImplementedError

    def dismiss(self):
        pass

    def data(self, start, stop, dtype=None):
        if dtype is None:
            thedtype = numpy.dtype(numpy.uint8)
        else:
            thedtype = dtype

        # assert start >= 0
        # assert stop >= 0
        # assert stop >= start

        chunkstart = start // self._chunkbytes
        if stop % self._chunkbytes == 0:
            chunkstop = stop // self._chunkbytes
        else:
            chunkstop = stop // self._chunkbytes + 1

        out = numpy.empty((stop - start) // thedtype.itemsize, dtype=thedtype)

        for chunkindex in range(chunkstart, chunkstop):
            try:
                chunk = self.cache[chunkindex]
            except KeyError:
                self._open()
                chunk = self.cache[chunkindex] = self._read(chunkindex)

            cstart = 0
            cstop = self._chunkbytes
            gstart = chunkindex * self._chunkbytes
            gstop = (chunkindex + 1) * self._chunkbytes

            if gstart < start:
                cstart += start - gstart
                gstart += start - gstart
            if gstop > stop:
                cstop -= gstop - stop
                gstop -= gstop - stop

            if cstop - cstart > len(chunk):
                raise IndexError("indexes {0}:{1} are beyond the end of data source {2}".format(gstart + len(chunk), stop, repr(self.path)))

            if dtype is None:
                out[gstart - start : gstop - start] = chunk[cstart:cstop]
            else:
                out.view(numpy.uint8)[gstart - start : gstop - start] = chunk[cstart:cstop]

        return out
