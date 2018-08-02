'''
MIT License

Copyright (c) 2018 Deep Compute, LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import os
from functools import reduce

import numpy as np

class DiskArray(object):
    '''
    Stores binary data on disk as a memory mapped file
    using numpy.memmap. Allows for growing the disk data
    by appending and extending.

    Links:
    * https://en.wikipedia.org/wiki/Memory-mapped_file

    # FIXME:
    1. Explain capacity and actual shape
    2. Explain growby
    3. Explain not having to specify shape for 1d arrays
    4. Explain using structured arrays
    5. Why memory mapping? What does it provide?
    6. Why not use np.save and np.load?
    '''
    GROWBY = 10000

    def __init__(self, fpath, dtype, mode='r+', shape=None,
        capacity=None, growby=GROWBY):
        '''
        >>> import numpy as np
        >>> da = DiskArray('/tmp/test.array', shape=(0, 3), dtype=np.float32)
        >>> print(da[:])
        [[0. 0. 0.]]
        '''

        itemsize = np.dtype(dtype).itemsize

        if not os.path.exists(fpath):
            if not shape:
                shape = (0,)
            # FIXME: what if capacity is defined?
            if not capacity:
                capacity = tuple([max(x, 1) for x in shape])

            n_init_capacity = self._shape_bytes(capacity, itemsize)
            open(fpath, 'w').write('\x00' * n_init_capacity) # touch file

        if not shape:
            n = int(os.path.getsize(fpath) / itemsize)
            shape = (n,)

        self._fpath = fpath
        self._shape = shape
        self._capacity_shape = capacity or shape
        self._dtype = dtype
        self._mode = mode
        self._growby = growby

        self.data = None
        self._update_ndarray()

    def _update_ndarray(self):
        if self.data is not None:
            self.data.flush()

        self._create_ndarray()

    def _create_ndarray(self):
        self.data = np.memmap(self._fpath,
                        shape=self._capacity_shape,
                        dtype=self._dtype,
                        mode=self._mode)
        if self._shape is None:
            self._shape = self.data.shape

    def flush(self):
        self.data.flush()
        self._truncate_if_needed()

    def _shape_bytes(self, shape, dtype_bytes):
        return reduce((lambda x, y: x * y), shape) * dtype_bytes

    def _truncate_if_needed(self):
        fd = os.open(self._fpath, os.O_RDWR|os.O_CREAT)
        try:
            dtype_bytes = np.dtype(self._dtype).itemsize
            nbytes = self._shape_bytes(self._shape, dtype_bytes)
            os.ftruncate(fd, nbytes)
            self._capacity_shape = self._shape
        finally:
            os.close(fd)
        self._create_ndarray()

    @property
    def shape(self):
        return self._shape

    @property
    def capacity(self):
        return self._capacity_shape

    @property
    def dtype(self):
        return self._dtype

    def __getitem__(self, idx):
        return self.data[idx]

    def __setitem__(self, idx, v):
        self.data[idx] = v

    def __len__(self):
        return self._shape[0]

    def _incr_shape(self, shape, n):
        _s = list(shape)
        _s[0] += n
        return tuple(_s)

    def extend(self, v):
        '''
        >>> import numpy as np
        >>> da = DiskArray('/tmp/test.array', shape=(0, 3), capacity=(10, 3), dtype=np.float32)
        >>> print(da[:])
	[[2. 3. 4.]
	 [0. 0. 0.]
	 [0. 0. 0.]
	 [0. 0. 0.]
	 [0. 0. 0.]
	 [0. 0. 0.]
	 [0. 0. 0.]
	 [0. 0. 0.]
	 [0. 0. 0.]
	 [0. 0. 0.]]
        >>> data = np.array([[2,3,4], [1, 2, 3]])
        >>> da.extend(data)
        >>> print(da[:])
        [[2. 3. 4.]
         [1. 2. 3.]
         [0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]]
        >>> os.remove('/tmp/test.array')
        '''

        nrows = self._shape[0]
        nrows_capacity = self._capacity_shape[0]
        remaining_capacity = nrows_capacity - nrows

        if remaining_capacity < len(v):
            diff = len(v) - remaining_capacity
            self._capacity_shape = self._incr_shape(self._capacity_shape, diff)
            self._update_ndarray()

        self.data[nrows:nrows+len(v)] = v
        self._shape = self._incr_shape(self._shape, len(v))

    def close(self):
        self.data._mmap.close()
        del self.data
        del self._fpath

    def destroy(self):
        self.data = None
        os.remove(self._fpath)

    def resize(self, size):
        temp = np.array([])
        for x in range(size - len(self)):
            temp = np.append(temp, 0)
        self.extend(temp)