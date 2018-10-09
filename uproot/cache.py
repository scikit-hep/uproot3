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

import collections
import threading

import cachetools

class ArrayCache(collections.MutableMapping):
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
