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

from uproot.source.chunked import ChunkedSource

class ChunkedXRootD(ChunkedSource):
    def _open(self):
        try:
            import pyxrootd.client
        except ImportError:
            raise ImportError("\n\nInstall pyxrootd package from source and configure PYTHONPATH and LD_LIBRARY_PATH:\n\n    http://xrootd.org/dload.html\n\nAlternatively, try a conda package:\n\n    https://anaconda.org/search?q=xrootd")

        if self._source is None:
            self._source = pyxrootd.client.File()
            status, dummy = self._source.open(self._path)
            if status.get("error", None) is not None:
                raise OSError(status["message"])

    def _read(self, chunkindex):
        status, data = self._source.read(chunkindex * self._chunkbytes, self._chunkbytes)
        if status.get("error", None) is not None:
            raise OSError(status["message"])
        return numpy.frombuffer(data, dtype=numpy.uint8)

    def __del__(self):
        if self._source is not None:
            self._source.close()
