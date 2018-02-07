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

import sys
import numbers
import threading

import numpy

class MemoryCache(dict):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    __slots__ = ("limitbytes", "numevicted", "spillover", "spill_immediately", "_order", "_lookup", "_numbytes")

    if sys.version_info[0] < 3:
        # Python 2
        @staticmethod
        def sizeof(obj):
            if isinstance(obj, numpy.ndarray):
                return sys.getsizeof(obj)
            elif isinstance(obj, dict):
                return sys.getsizeof(obj) + sum(MemoryCache.sizeof(k) + MemoryCache.sizeof(v) for k, v in obj)
            elif isinstance(obj, (unicode, str)):
                return sys.getsizeof(obj)
            else:
                out = sys.getsizeof(obj)
                try:
                    for x in obj:
                        out += MemoryCache.sizeof(x)
                except TypeError:
                    pass
                return out
            return sys.getsizeof(obj)
    else:
        # Python 3
        @staticmethod
        def sizeof(obj):
            if isinstance(obj, numpy.ndarray):
                return sys.getsizeof(obj) + obj.nbytes
            elif isinstance(obj, dict):
                return sys.getsizeof(obj) + sum(MemoryCache.sizeof(k) + MemoryCache.sizeof(v) for k, v in obj)
            elif isinstance(obj, (str, bytes)):
                return sys.getsizeof(obj)
            else:
                out = sys.getsizeof(obj)
                try:
                    for x in obj:
                        out += MemoryCache.sizeof(x)
                except TypeError:
                    pass
                return out
            return sys.getsizeof(obj)

    def __init__(self, limitbytes, spillover=None, spill_immediately=False, items=(), **kwds):
        assert isinstance(limitbytes, numbers.Integral) and limitbytes > 0
        self.limitbytes = limitbytes
        self.spillover = spillover
        self.spill_immediately = spill_immediately
        self.numevicted = 0
        self._order = []
        self._lookup = {}
        self._numbytes = self.sizeof(self.limitbytes) + self.sizeof(0) + self.sizeof(self.numevicted) + self.sizeof(self._order) + self.sizeof(self._lookup)
        self.update(items, **kwds)

    def _assertvalid(self):
        assert isinstance(self.limitbytes, numbers.Integral) and self.limitbytes > 0
        assert isinstance(self.numevicted, numbers.Integral)
        assert isinstance(self._order, list)
        assert isinstance(self._lookup, dict)
        assert set(self._lookup) == set(self._order)
        assert self._numbytes == self.sizeof(self.limitbytes) + self.sizeof(0) + self.sizeof(self.numevicted) + sys.getsizeof(self._order) + sys.getsizeof(self._lookup) + sum(self.sizeof(k) for k in self._order) + sum(self.sizeof(v) for v in self._lookup.values())  # same keys in both _order and _lookup; don't double-count

    @property
    def numbytes(self):
        return self._numbytes

    def index(self, key):
        for i, obj in enumerate(reversed(self._order)):
            if key == obj:
                return len(self._order) - i - 1
        raise KeyError("{0} is not in MemoryCache".format(repr(key)))

    def promote(self, key):
        i = self.index(key)
        del self._order[i]
        self._order.append(key)
        
    def __getitem__(self, key):
        if key in self._lookup:
            self.promote(key)
            return self._lookup[key]

        elif self.spillover is not None:
            # get it from the backup
            value = self.spillover[key]
            # temporarily disconnect the spillover so that we don't put the value back in there (should already be promoted)
            spillover = self.spillover
            self.spillover = None
            # put the key-value pair into *this* cache
            self[key] = value
            # restore the spillover
            self.spillover = spillover
            return value

        else:
            raise KeyError(repr(key))

    def spill(self, key):
        if self.spillover is not None:
            self.spillover[key] = self._lookup[key]

    def spillall(self):
        for key in self._order:
            self.spillover[key] = self._lookup[key]

    def __setitem__(self, key, value):
        container_before = sys.getsizeof(self._order) + sys.getsizeof(self._lookup)
        delta_contents = self.sizeof(key) + self.sizeof(value)

        if key in self._lookup:
            delta_contents -= self.sizeof(key) + self.sizeof(self._lookup[key])
            self.promote(key)
        else:
            self._order.append(key)
        self._lookup[key] = value

        if self.spill_immediately:
            self.spill(key)

        container_after = sys.getsizeof(self._order) + sys.getsizeof(self._lookup)
        self._numbytes += container_after - container_before + delta_contents

        while len(self._order) > 0 and self._numbytes > self.limitbytes:
            container_before = sys.getsizeof(self._order) + sys.getsizeof(self._lookup)
            delta_contents = -(self.sizeof(self._lookup[self._order[0]]) + self.sizeof(self._order[0]))

            if not self.spill_immediately:
                self.spill(self._order[0])

            del self._lookup[self._order[0]]
            del self._order[0]

            container_after = sys.getsizeof(self._order) + sys.getsizeof(self._lookup)
            self._numbytes += container_after - container_before + delta_contents
            self.numevicted += 1

    def __delitem__(self, key):
        if self.spillover is not None:
            try:
                del self.spillover[key]
            except KeyError:
                pass

        if key not in self._lookup:
            raise KeyError(repr(key))

        container_before = sys.getsizeof(self._order) + sys.getsizeof(self._lookup)
        delta_contents = -(sys.getsizeof(self._lookup[key]) + sys.getsizeof(key))

        del self._order[index(key)]
        del self._lookup[key]

        container_after = sys.getsizeof(self._order) + sys.getsizeof(self._lookup)
        self._numbytes += container_after - container_before + delta_contents

    def keys(self):
        for key in self._order:
            yield key

    iterkeys = keys

    def values(self):
        for key in self._order:
            yield self._lookup[key]

    itervalues = values

    def items(self):
        for key in self._order:
            yield (key, self._lookup[key])

    iteritems = items

    def __repr__(self):
        if not hasattr(self, "_order"):
            return "<uninitialized MemoryCache>"
        else:
            return "{" + ", ".join("{0}: {1}".format(repr(key), repr(value)) for key, value in self.items()) + "}"

    def __sizeof__(self):
        return self._numbytes

    @staticmethod
    def fromkeys(limitbytes, keys, value=None):
        return MemoryCache(limitbytes, [(key, value) for key in keys])

    def copy(self):
        out = MemoryCache(self.limitbytes, self.items())
        out.numevicted = self.numevicted
        return out

    def clear(self):
        self.numevicted = 0
        self._order = []
        self._lookup = {}
        self._numbytes = self.sizeof(self.limitbytes) + self.sizeof(0) + self.sizeof(self.numevicted) + sys.getsizeof(self._order) + sys.getsizeof(self._lookup)

    def has_key(self, key):
        if key in self._lookup:
            return True
        elif self.spillover is not None:
            return key in self.spillover
        else:
            return False

    def __contains__(self, key):
        return self.has_key(key)

    def update(self, items=(), **kwds):
        if hasattr(items, "keys"):
            for key in items.keys():
                self[key] = items[key]
        else:
            for key, value in items:
                self[key] = value

        for key, value in kwds.items():
            self[key] = value

    def pop(self, **args):
        return self.popitem(**args)[1]

    def popitem(self, **args):
        if len(args) == 0:
            if len(self._order) > 0:
                key = self._order[-1]
            else:
                raise IndexError("pop from empty MemoryCache")
        elif len(args) == 1:
            key, = args
        elif len(args) == 2:
            key, default = args
        else:
            raise TypeError("popitem expected at most 2 arguments, got {0}".format(len(args)))

        if key in self._lookup:
            out = (key, self._lookup[key])
            del self[key]
            return out
        elif len(args) == 2:
            return default
        else:
            raise KeyError(repr(key))
    
    def get(self, key, default=None):
        if key in self._lookup:
            return self[key]
        else:
            return default

    def setdefault(self, key, default=None):
        if key not in self._lookup:
            self[key] = default
            return default
        else:
            return self[key]

    def do(self, key, function):
        if not callable(function):
            raise TypeError("'function' must be a zero-argument function")
        if key not in self._lookup:
            value = function()
            self[key] = value
            return value
        else:
            return self[key]

    def __len__(self):
        return len(self._order)

    def __iter__(self):
        return self.iterkeys()

    def viewkeys(self, *args, **kwds):
        raise NotImplementedError("a view could allow you to break the consistency between _order and _lookup")

    def viewvalues(self, *args, **kwds):
        raise NotImplementedError("a view could allow you to break the consistency between _order and _lookup")

    def viewitems(self, *args, **kwds):
        raise NotImplementedError("a view could allow you to break the consistency between _order and _lookup")

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.limitbytes == other.limitbytes and self.numevicted == other.numevicted and self._order == other._order and self._lookup == other._lookup and self._numbytes == other._numbytes

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if isinstance(other, MemoryCache):
            if self._order == other._order:
                selfvalues = list(self.values())
                othervalues = list(other.values())
                if selfvalues == othervalues:
                    if self.limitbytes == other.limitbytes:
                        return self.numevicted < other.numevicted
                    else:
                        return self.limitbytes < other.limitbytes
                else:
                    return selfvalues < othervalues
            else:
                return self._order < other._order
        else:
            raise TypeError("unorderable types: {0} < {1}".format(type(self), type(other)))

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return not self < other

    def __gt__(self, other):
        return self >= other and not self == other

    def __cmp__(self, other):
        if self < other:
            return -1
        elif self == other:
            return 0
        else:
            return 1

    def __getstate__(self):
        return (self.limitbytes, self.numevicted, self._order, self._lookup)

    def __setstate__(self, state):
        self.limitbytes, self.numevicted, order, lookup = state
        self._order = []
        self._lookup = {}
        self._numbytes = self.sizeof(self.limitbytes) + self.sizeof(0) + self.sizeof(self.numevicted) + sys.getsizeof(self._order) + sys.getsizeof(self._lookup)
        for key in order:
            self[key] = lookup[key]

class ThreadSafeMemoryCache(MemoryCache):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (MemoryCache.__metaclass__,), {})

    __slots__ = ("limitbytes", "numevicted", "_order", "_lookup", "_numbytes", "_lock")

    def __init__(self, limitbytes, spillover=None, spill_immediately=False, items=(), **kwds):
        self._lock = threading.RLock()
        with self._lock:
            super(ThreadSafeMemoryCache, self).__init__(limitbytes, spillover=spillover, spill_immediately=spill_immediately, items=items, **kwds)

    def index(self, key):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).index(key)

    def promote(self, key):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).promote(key)

    def __getitem__(self, key):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).__getitem__(key)

    def spill(self, key):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).spill(key)

    def spillall(self):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).spillall()

    def __setitem__(self, key, value):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).__setitem__(key, value)

    def __delitem__(self, key):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).__delitem__(key)

    def keys(self):
        with self._lock:
            return list(super(ThreadSafeMemoryCache, self).keys())

    def values(self):
        with self._lock:
            return list(super(ThreadSafeMemoryCache, self).values())

    def items(self):
        with self._lock:
            return list(super(ThreadSafeMemoryCache, self).items())

    @staticmethod
    def fromkeys(limitbytes, keys, value=None):
        return ThreadSafeMemoryCache(limitbytes, [(key, value) for key in keys])

    def copy(self):
        out = ThreadSafeMemoryCache(self.limitbytes, self.items())
        out.numevicted = self.numevicted
        return out

    def update(self, items=(), **kwds):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).update(items, **kwds)

    def popitem(self, **args):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).popitem(**args)

    def get(self, key, default=None):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).get(key, default)

    def setdefault(self, key, default=None):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).setdefault(key, default)

    def do(self, key, function):
        with self._lock:
            return super(ThreadSafeMemoryCache, self).do(key, function)

    def __eq__(self, other):
        if not self.__class__ == other.__class__:
            return False
        with self._lock:
            with other._lock:
                return super(ThreadSafeMemoryCache, self).__eq__(self, other)

    def __lt__(self, other):
        if isinstance(other, ThreadLocalMemoryCache):
            with self._lock:
                with other._lock:
                    return super(ThreadSafeMemoryCache, self).__lt__(self, other)
        else:
            raise TypeError("unorderable types: {0} < {1}".format(type(self), type(other)))

class ThreadSafeDict(dict):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    def __init__(self, items=(), **kwds):
        self._lock = threading.RLock()
        with self._lock:
            super(ThreadSafeDict, self).__init__(items, **kwds)

    def __getitem__(self, key):
        with self._lock:
            return super(ThreadSafeDict, self).__getitem__(key)

    def __setitem__(self, key, value):
        with self._lock:
            return super(ThreadSafeDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        with self._lock:
            return super(ThreadSafeDict, self).__delitem__(key)

    def keys(self):
        with self._lock:
            return list(super(ThreadSafeDict, self).keys())

    def values(self):
        with self._lock:
            return list(super(ThreadSafeDict, self).values())

    def items(self):
        with self._lock:
            return list(super(ThreadSafeDict, self).items())

    @staticmethod
    def fromkeys(keys, value=None):
        return ThreadSafeDict([(key, value) for key in keys])

    def copy(self):
        return ThreadSafeDict(self.items())

    def update(self, items=(), **kwds):
        with self._lock:
            return super(ThreadSafeDict, self).update(items, **kwds)

    def popitem(self, **args):
        with self._lock:
            return super(ThreadSafeDict, self).popitem(**args)

    def get(self, key, default=None):
        with self._lock:
            return super(ThreadSafeDict, self).get(key, default)

    def setdefault(self, key, default=None):
        with self._lock:
            return super(ThreadSafeDict, self).setdefault(key, default)

    def __eq__(self, other):
        if not self.__class__ == other.__class__:
            return False
        with self._lock:
            with other._lock:
                return super(ThreadSafeDict, self).__eq__(self, other)

    def __lt__(self, other):
        if isinstance(other, ThreadLocalMemoryCache):
            with self._lock:
                with other._lock:
                    return super(ThreadSafeDict, self).__lt__(self, other)
        else:
            raise TypeError("unorderable types: {0} < {1}".format(type(self), type(other)))
