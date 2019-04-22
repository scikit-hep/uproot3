#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import numpy

class Source(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    def __init__(self, data):
        assert len(data.shape) == 1 and data.dtype == numpy.uint8
        self._source = data

    def parent(self):
        return self

    def size(self):
        return len(self._source)

    def threadlocal(self):
        return self

    def dismiss(self):
        pass

    def close(self):
        self.dismiss()

    def preload(self, starts):
        pass

    def data(self, start, stop, dtype=None):
        # assert start >= 0
        # assert stop >= 0
        # assert stop >= start

        if stop > len(self._source):
            raise IndexError("indexes {0}:{1} are beyond the end of data source of length {2}".format(start, stop, len(self._source)))

        if dtype is None:
            return self._source[start:stop]
        else:
            return self._source[start:stop].view(dtype)
