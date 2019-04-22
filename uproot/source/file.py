#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import os.path

import numpy

import uproot.source.chunked

class FileSource(uproot.source.chunked.ChunkedSource):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.source.chunked.ChunkedSource.__metaclass__,), {})

    defaults = {"chunkbytes": 8*1024, "limitbytes": 1024**2}

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
        out.cache = self.cache
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
