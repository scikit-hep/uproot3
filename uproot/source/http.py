#!/usr/bin/env python

# Copyright (c) 2019, IRIS-HEP
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
import re
import multiprocessing
import sys

import numpy

import uproot.source.chunked

class HTTPSource(uproot.source.chunked.ChunkedSource):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.source.chunked.ChunkedSource.__metaclass__,), {})

    def __init__(self, path, auth=None, *args, **kwds):
        super(HTTPSource, self).__init__(path, *args, **kwds)
        self._size = None
        self.auth = auth

    defaults = {"chunkbytes": 32*1024, "limitbytes": 32*1024**2, "parallel": 8*multiprocessing.cpu_count() if sys.version_info[0] > 2 else 1}

    def _open(self):
        try:
            import requests
        except ImportError:
            raise ImportError("Install requests package (for HTTP) with:\n    pip install requests\nor\n    conda install -c anaconda requests")

    def size(self):
        return self._size

    _contentrange = re.compile("^bytes ([0-9]+)-([0-9]+)/([0-9]+)$")

    def _read(self, chunkindex):
        import requests
        while True:
            response = requests.get(
                self.path,
                headers={"Range": "bytes={0}-{1}".format(chunkindex * self._chunkbytes, (chunkindex + 1) * self._chunkbytes)},
                auth=self.auth,
            )
            if response.status_code == 504:   # timeout, try it again
                pass
            else:
                response.raise_for_status()   # if it's an error, raise exception
                break                         # otherwise, break out of the loop
        data = response.content

        if self._size is None:
            m = self._contentrange.match(response.headers.get("Content-Range", ""))
            if m is not None:
                start_inclusive, stop_inclusive, size = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if size > (stop_inclusive - start_inclusive) + 1:
                    self._size = size
        return numpy.frombuffer(data, dtype=numpy.uint8)
