#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

class LazyArray_dask(object):
    def __init__(self, lazyarray):
        self._lazyarray = lazyarray

    def array(self, chunks=None, name=None):
        import dask.array

        if chunks is None:
            chunks = self._lazyarray._chunksize

        # TODO: what would it take to support fancy indexing?
        return dask.array.from_array(self._lazyarray, chunks, fancy=False)
