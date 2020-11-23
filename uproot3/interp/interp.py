#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

from __future__ import absolute_import

import awkward0

class Interpretation(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    awkward = awkward0
    awkward0 = awkward0

    debug_reading = False

    def awkwardlib(self, lib):
        cls = type(self)
        out = cls.__new__(cls)
        out.__dict__.update(self.__dict__)
        out.awkward0 = lib
        return out

    @property
    def identifier(self):
        raise NotImplementedError

    @property
    def type(self):
        raise NotImplementedError   # awkward0.type.Type

    def empty(self):
        raise NotImplementedError

    def compatible(self, other):
        raise NotImplementedError

    def numitems(self, numbytes, numentries):
        raise NotImplementedError

    def source_numitems(self, source):
        raise NotImplementedError

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop, keylen):
        raise NotImplementedError

    def destination(self, numitems, numentries):
        raise NotImplementedError

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        raise NotImplementedError

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        raise NotImplementedError

    def finalize(self, destination, branch):
        raise NotImplementedError
