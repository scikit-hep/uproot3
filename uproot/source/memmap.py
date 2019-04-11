#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import os.path

import numpy

import uproot.source.source

class MemmapSource(uproot.source.source.Source):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.source.source.Source.__metaclass__,), {})

    defaults = {}

    def __init__(self, path):
        self.path = os.path.expanduser(path)
        self._source = numpy.memmap(self.path, dtype=numpy.uint8, mode="r")

    def parent(self):
        return self

    def size(self):
        return len(self._source)

    def threadlocal(self):
        return self

    def dismiss(self):
        pass

    def close(self):
        self._source._mmap.close()

    def data(self, start, stop, dtype=None):
        # assert start >= 0
        # assert stop >= 0
        # assert stop >= start

        if stop > len(self._source):
            raise IndexError("indexes {0}:{1} are beyond the end of data source {2}".format(len(self._source), stop, repr(self.path)))

        if dtype is None:
            return self._source[start:stop]
        else:
            return self._source[start:stop].view(dtype)
