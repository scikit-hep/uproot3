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
    
    def test_socalled_flat(self):
        tree = uproot.open("tests/small-flat-tree.root")["tree"]

        hundred = list(range(100))
        self.assertTrue(numpy.array_equal(tree.array("Int32"), numpy.array(hundred, dtype=">i4")))
        self.assertTrue(numpy.array_equal(tree.array("Int64"), numpy.array(hundred, dtype=">i8")))
        self.assertTrue(numpy.array_equal(tree.array("UInt32"), numpy.array(hundred, dtype=">u4")))
        self.assertTrue(numpy.array_equal(tree.array("UInt64"), numpy.array(hundred, dtype=">u8")))
        self.assertTrue(numpy.array_equal(tree.array("Float32"), numpy.array(hundred, dtype=">f4")))
        self.assertTrue(numpy.array_equal(tree.array("Float64"), numpy.array(hundred, dtype=">f8")))

        hundredstrings = ["evt-{0:03d}".format(x) for x in range(100)]
        self.assertTrue(numpy.array_equal(tree.array("Str"), numpy.array(hundredstrings, dtype=object)))

        hundredarrays = [[x] * 10 for x in range(100)]
        self.assertTrue(numpy.array_equal(tree.array("ArrayInt32"), numpy.array(hundredarrays, dtype=">i4")))
        self.assertTrue(numpy.array_equal(tree.array("ArrayInt64"), numpy.array(hundredarrays, dtype=">i8")))
        self.assertTrue(numpy.array_equal(tree.array("ArrayUInt32"), numpy.array(hundredarrays, dtype=">u4")))
        self.assertTrue(numpy.array_equal(tree.array("ArrayUInt64"), numpy.array(hundredarrays, dtype=">u8")))
        self.assertTrue(numpy.array_equal(tree.array("ArrayFloat32"), numpy.array(hundredarrays, dtype=">f4")))
        self.assertTrue(numpy.array_equal(tree.array("ArrayFloat64"), numpy.array(hundredarrays, dtype=">f8")))

        self.assertTrue(numpy.array_equal(tree.array("N"), numpy.array(list(range(10)) * 10, dtype=">i4")))

        sliced = [[x] * (x % 10) for x in range(100)]
        flattened = [y for x in sliced for y in x]
        self.assertTrue(numpy.array_equal(tree.array("SliceInt32"), numpy.array(flattened, dtype=">i4")))
        self.assertTrue(numpy.array_equal(tree.array("SliceInt64"), numpy.array(flattened, dtype=">i8")))
        self.assertTrue(numpy.array_equal(tree.array("SliceUInt32"), numpy.array(flattened, dtype=">u4")))
        self.assertTrue(numpy.array_equal(tree.array("SliceUInt64"), numpy.array(flattened, dtype=">u8")))
        self.assertTrue(numpy.array_equal(tree.array("SliceFloat32"), numpy.array(flattened, dtype=">f4")))
        self.assertTrue(numpy.array_equal(tree.array("SliceFloat64"), numpy.array(flattened, dtype=">f8")))
