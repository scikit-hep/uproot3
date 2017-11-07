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

import numpy
try:
    import numba
except ImportError:
    numba = None

class JaggedArray(object):
    starts_dtype = numpy.dtype(numpy.int64)
    sizes_dtype = numpy.dtype(numpy.int64)

    def __init__(self, contents, starts, sizes):
        assert isinstance(contents, numpy.ndarray)
        assert isinstance(starts, numpy.ndarray) and starts.dtype == JaggedArray.starts_dtype
        assert isinstance(sizes, numpy.ndarray) and sizes.dtype == JaggedArray.sizes_dtype
        assert starts.shape == sizes.shape
        assert len(starts.shape) == 1
        self.contents = contents
        self.starts = starts
        self.sizes = sizes

    def __getitem__(self, index):
        if index < 0:
            index += len(self.starts)
        start = self.starts[index]
        stop  = start + self.sizes[index]
        return self.contents[start:stop]

a = JaggedArray(numpy.array([1.1, 1.1, 1.1, 3.3, 3.3]), numpy.array([0, 3, 3]), numpy.array([3, 0, 2]))
print a[0], a[1], a[2]

class JaggedArrayType(numba.types.Type):
    concrete = {}

    def __init__(self, contents, starts, sizes):
        assert isinstance(contents, numba.types.Array)
        assert isinstance(starts, numba.types.Array) and starts.dtype == numba.numpy_support.from_dtype(JaggedArray.starts_dtype) and starts.ndim == 1
        assert isinstance(sizes, numba.types.Array) and sizes.dtype == numba.numpy_support.from_dtype(JaggedArray.sizes_dtype) and starts.ndim == 1
        self.contents = contents
        self.starts = starts
        self.sizes = sizes

    def get(self, contents, starts, sizes):
        key = (contents, starts, sizes)
        try:
            return JaggedArrayType.concrete[key]
        except KeyError:
            JaggedArrayType.concrete[key] = JaggedArrayType(contents, starts, sizes)
            return JaggedArrayType.concrete[key]

@numba.extending.typeof_impl.register(JaggedArray)
def typeof_index(val, c):
    assert isinstance(val, JaggedArray)
    return JaggedArrayType.get(numba.typing._typeof_ndarray(val.contents, c),
                               numba.typing._typeof_ndarray(val.starts, c),
                               numba.typing._typeof_ndarray(val.sizes, c))

@numba.extending.register_model(JaggedArrayType)
class JaggedArrayModel(numba.datamodel.models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [("contents", fe_type.contents),
                   ("starts", fe_type.starts),
                   ("sizes", fe_type.sizes)]
        super(JaggedArrayModel, self).__init__(dmm, fe_type, members)

numba.extending.make_attribute_wrapper(JaggedArrayType, "contents", "contents")
numba.extending.make_attribute_wrapper(JaggedArrayType, "starts", "starts")
numba.extending.make_attribute_wrapper(JaggedArrayType, "sizes", "sizes")

@numba.extending.lower_builtin(JaggedArray, numba.types.Array, numba.types.Array, numba.types.Array)
def jaggedarray_impl(context, builder, sig, args):
    typ = sig.return_type
    contents, starts, sizes = args
    jaggedarray = numba.cgutils.create_struct_proxy(typ)(context, builder)
    jaggedarray.contents = contents
    jaggedarray.starts = starts
    jaggedarray.sizes = sizes
    return jaggedarray._getvalue()

@numba.njit
def test1(x, y, z):
    a = JaggedArray(x, y, z)
    return a.contents

print test1(numpy.array([1.1, 1.1, 1.1, 3.3, 3.3]), numpy.array([0, 3, 3]), numpy.array([3, 0, 2]))
