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

import uproot.partition

class TestPartition(unittest.TestCase):
    def runTest(self):
        pass
    
    def test_make_partitions(self):
        files = ["tests/sample-5.23.02-uncompressed.root",
                 "tests/sample-5.24.00-uncompressed.root",
                 "tests/sample-5.25.02-uncompressed.root",
                 "tests/sample-5.26.00-uncompressed.root",
                 "tests/sample-5.27.02-uncompressed.root",
                 "tests/sample-5.28.00-uncompressed.root",
                 "tests/sample-5.29.02-uncompressed.root",
                 "tests/sample-5.30.00-uncompressed.root",
                 "tests/sample-6.08.04-uncompressed.root",
                 "tests/sample-6.10.05-uncompressed.root"]

        partitionset = uproot.partition.PartitionSet.fill(files, "sample", ["n", "i8", "ai4", "Ai2"], under=lambda baskets: sum(x.numbytes for x in baskets) < 600, debug=False)

        check = uproot.partition.PartitionSet(
            "sample",
            {"n": numpy.dtype(">i4"), "i8": numpy.dtype(">i8"), "ai4": numpy.dtype(">i4"), "Ai2": numpy.dtype(">i2")},
            {"Ai2": "n"},
            {"ai4": (3,)},
            7,
            300,
            uproot.partition.Partition(0,
                uproot.partition.Range("tests/sample-5.23.02-uncompressed.root", 0, 30),
                uproot.partition.Range("tests/sample-5.24.00-uncompressed.root", 0, 18)),
            uproot.partition.Partition(1,
                uproot.partition.Range("tests/sample-5.24.00-uncompressed.root", 18, 30),
                uproot.partition.Range("tests/sample-5.25.02-uncompressed.root", 0, 30),
                uproot.partition.Range("tests/sample-5.26.00-uncompressed.root", 0, 6)),
            uproot.partition.Partition(2,
                uproot.partition.Range("tests/sample-5.26.00-uncompressed.root", 6, 30),
                uproot.partition.Range("tests/sample-5.27.02-uncompressed.root", 0, 24)),
            uproot.partition.Partition(3,
                uproot.partition.Range("tests/sample-5.27.02-uncompressed.root", 24, 30),
                uproot.partition.Range("tests/sample-5.28.00-uncompressed.root", 0, 30),
                uproot.partition.Range("tests/sample-5.29.02-uncompressed.root", 0, 12)),
            uproot.partition.Partition(4,
                uproot.partition.Range("tests/sample-5.29.02-uncompressed.root", 12, 30),
                uproot.partition.Range("tests/sample-5.30.00-uncompressed.root", 0, 30)),
            uproot.partition.Partition(5,
                uproot.partition.Range("tests/sample-6.08.04-uncompressed.root", 0, 30),
                uproot.partition.Range("tests/sample-6.10.05-uncompressed.root", 0, 16)),
            uproot.partition.Partition(6,
                uproot.partition.Range("tests/sample-6.10.05-uncompressed.root", 16, 30)))

        self.assertEqual(partitionset, check)
        self.assertEqual(hash(partitionset), hash(check))
        self.assertEqual(uproot.partition.PartitionSet.fromJson(partitionset.toJson()), partitionset)
        self.assertEqual(uproot.partition.PartitionSet.fromJsonString(partitionset.toJsonString()), partitionset)


