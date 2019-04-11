#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

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
