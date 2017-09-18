#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy

import uproot

class TestTypes(unittest.TestCase):
    def runTest(self):
        pass

    @staticmethod
    def check(x, y):
        return x.dtype == y.dtype and x.shape == y.shape and numpy.array_equal(x, y)

    def test_socalled_flat(self):
        tree = uproot.open("tests/small-flat-tree.root")["tree"]

        hundred = list(range(100))
        self.assertTrue(self.check(tree.array("Int32"), numpy.array(hundred, dtype=">i4")))
        self.assertTrue(self.check(tree.array("Int64"), numpy.array(hundred, dtype=">i8")))
        self.assertTrue(self.check(tree.array("UInt32"), numpy.array(hundred, dtype=">u4")))
        self.assertTrue(self.check(tree.array("UInt64"), numpy.array(hundred, dtype=">u8")))
        self.assertTrue(self.check(tree.array("Float32"), numpy.array(hundred, dtype=">f4")))
        self.assertTrue(self.check(tree.array("Float64"), numpy.array(hundred, dtype=">f8")))

        hundredstrings = ["evt-{0:03d}".format(x).encode("ascii") for x in range(100)]
        self.assertTrue(self.check(tree.array("Str"), numpy.array(hundredstrings, dtype=object)))

        hundredarrays = [[x] * 10 for x in range(100)]
        self.assertTrue(self.check(tree.array("ArrayInt32"), numpy.array(hundredarrays, dtype=">i4")))
        self.assertTrue(self.check(tree.array("ArrayInt64"), numpy.array(hundredarrays, dtype=">i8")))
        self.assertTrue(self.check(tree.array("ArrayUInt32"), numpy.array(hundredarrays, dtype=">u4")))
        self.assertTrue(self.check(tree.array("ArrayUInt64"), numpy.array(hundredarrays, dtype=">u8")))
        self.assertTrue(self.check(tree.array("ArrayFloat32"), numpy.array(hundredarrays, dtype=">f4")))
        self.assertTrue(self.check(tree.array("ArrayFloat64"), numpy.array(hundredarrays, dtype=">f8")))

        self.assertTrue(self.check(tree.array("N"), numpy.array(list(range(10)) * 10, dtype=">i4")))

        sliced = [[x] * (x % 10) for x in range(100)]
        flattened = [y for x in sliced for y in x]

        self.assertTrue(self.check(tree.array("SliceInt32"), numpy.array(flattened, dtype=">i4")))
        self.assertTrue(self.check(tree.array("SliceInt64"), numpy.array(flattened, dtype=">i8")))
        self.assertTrue(self.check(tree.array("SliceUInt32"), numpy.array(flattened, dtype=">u4")))
        self.assertTrue(self.check(tree.array("SliceUInt64"), numpy.array(flattened, dtype=">u8")))
        self.assertTrue(self.check(tree.array("SliceFloat32"), numpy.array(flattened, dtype=">f4")))
        self.assertTrue(self.check(tree.array("SliceFloat64"), numpy.array(flattened, dtype=">f8")))

    def test_splitobject(self):
        tree = uproot.open("tests/small-evnt-tree-fullsplit.root")["tree"]
        
        self.assertTrue(self.check(tree.array("Beg"), numpy.array(["beg-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))

        hundred = list(range(100))
        self.assertTrue(self.check(tree.array("I16"), numpy.array(hundred, dtype=">i2")))
        self.assertTrue(self.check(tree.array("I32"), numpy.array(hundred, dtype=">i4")))
        self.assertTrue(self.check(tree.array("I64"), numpy.array(hundred, dtype=">i8")))
        self.assertTrue(self.check(tree.array("U16"), numpy.array(hundred, dtype=">u2")))
        self.assertTrue(self.check(tree.array("U32"), numpy.array(hundred, dtype=">u4")))
        self.assertTrue(self.check(tree.array("U64"), numpy.array(hundred, dtype=">u8")))
        self.assertTrue(self.check(tree.array("F32"), numpy.array(hundred, dtype=">f4")))
        self.assertTrue(self.check(tree.array("F64"), numpy.array(hundred, dtype=">f8")))

        self.assertTrue(self.check(tree.array("Str"), numpy.array(["evt-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))

        self.assertTrue(self.check(tree.array("P3.Px"), numpy.array(list(range(-1, 99)), dtype=">i4")))
        self.assertTrue(self.check(tree.array("P3.Py"), numpy.array(list(range(0, 100)), dtype=">f8")))
        self.assertTrue(self.check(tree.array("P3.Pz"), numpy.array(list(range(-1, 99)), dtype=">i4")))

        hundredarrays = [[x] * 10 for x in range(100)]
        self.assertTrue(self.check(tree.array("ArrayI16[10]"), numpy.array(hundredarrays, dtype=">i2")))
        self.assertTrue(self.check(tree.array("ArrayI32[10]"), numpy.array(hundredarrays, dtype=">i4")))
        self.assertTrue(self.check(tree.array("ArrayI64[10]"), numpy.array(hundredarrays, dtype=">i8")))
        self.assertTrue(self.check(tree.array("ArrayU32[10]"), numpy.array(hundredarrays, dtype=">u4")))
        self.assertTrue(self.check(tree.array("ArrayU64[10]"), numpy.array(hundredarrays, dtype=">u8")))
        self.assertTrue(self.check(tree.array("ArrayF32[10]"), numpy.array(hundredarrays, dtype=">f4")))
        self.assertTrue(self.check(tree.array("ArrayF64[10]"), numpy.array(hundredarrays, dtype=">f8")))

        self.assertTrue(self.check(tree.array("N"), numpy.array(list(range(10)) * 10, dtype=">i4")))

        sliced = [[x] * (x % 10) for x in range(100)]
        flattened = [y for x in sliced for y in x]

        self.assertTrue(self.check(tree.array("SliceI16"), numpy.array(flattened, dtype=">i2")))
        self.assertTrue(self.check(tree.array("SliceI32"), numpy.array(flattened, dtype=">i4")))
        self.assertTrue(self.check(tree.array("SliceI64"), numpy.array(flattened, dtype=">i8")))
        self.assertTrue(self.check(tree.array("SliceU16"), numpy.array(flattened, dtype=">u2")))
        self.assertTrue(self.check(tree.array("SliceU32"), numpy.array(flattened, dtype=">u4")))
        self.assertTrue(self.check(tree.array("SliceU64"), numpy.array(flattened, dtype=">u8")))
        self.assertTrue(self.check(tree.array("SliceF32"), numpy.array(flattened, dtype=">f4")))
        self.assertTrue(self.check(tree.array("SliceF64"), numpy.array(flattened, dtype=">f8")))

        self.assertTrue(self.check(tree.array("End"), numpy.array(["end-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))
