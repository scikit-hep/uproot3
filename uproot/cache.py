#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import threading
try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping

import cachetools

class ArrayCache(MutableMapping):
    @staticmethod
    def getsizeof(obj):
        return getattr(obj, "nbytes", 1)

    def __init__(self, limitbytes, method="LRU"):
        if method == "LRU":
            self._cache = cachetools.LRUCache(limitbytes, getsizeof=self.getsizeof)
        elif method == "LFU":
            self._cache = cachetools.LFUCache(limitbytes, getsizeof=self.getsizeof)
        else:
            raise ValueError("unrecognized method: {0}".format(method))

    def __contains__(self, where):
        return where in self._cache

    def __getitem__(self, where):
        return self._cache[where]

    def __setitem__(self, where, what):
        self._cache[where] = what

    def __delitem__(self, where):
        del self._cache[where]

    def __iter__(self):
        for x in self._cache:
            yield x

    def __len__(self):
        return len(self._cache)

class ThreadSafeArrayCache(ArrayCache):
    def __init__(self, limitbytes, method="LRU"):
        super(ThreadSafeArrayCache, self).__init__(limitbytes, method=method)
        self._lock = threading.Lock()

    def __contains__(self, where):
        with self._lock:
            return where in self._cache

    def __getitem__(self, where):
        with self._lock:
            return self._cache[where]

    def __setitem__(self, where, what):
        with self._lock:
            self._cache[where] = what

    def __delitem__(self, where):
        with self._lock:
            del self._cache[where]

    def __iter__(self):
        with self._lock:
            for x in self._cache:
                yield x

    def __len__(self):
        with self._lock:
            return len(self._cache)
