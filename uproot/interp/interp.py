#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import awkward

class Interpretation(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    awkward = awkward

    def awkwardlib(self, lib):
        cls = type(self)
        out = cls.__new__(cls)
        out.__dict__.update(self.__dict__)
        out.awkward = lib
        return out

    @property
    def identifier(self):
        raise NotImplementedError

    @property
    def type(self):
        raise NotImplementedError   # awkward.type.Type

    def empty(self):
        raise NotImplementedError

    def compatible(self, other):
        raise NotImplementedError

    def numitems(self, numbytes, numentries):
        raise NotImplementedError

    def source_numitems(self, source):
        raise NotImplementedError

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        raise NotImplementedError

    def destination(self, numitems, numentries):
        raise NotImplementedError

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        raise NotImplementedError

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        raise NotImplementedError

    def finalize(self, destination, branch):
        raise NotImplementedError
