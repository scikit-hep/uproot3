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

class TestTree(unittest.TestCase):
    def runTest(self):
        pass
    
    def test_branch_array(self):
        file = uproot.open("tests/simple.root")

        tree = file["tree"]
        self.assertEqual(tree.branch("one").array().tolist(), [1, 2, 3, 4])
        self.assertEqual(tree.branch("two").array().tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
        self.assertEqual(tree.branch("three").array().tolist(), [b"uno", b"dos", b"tres", b"quatro"])

        # get branches again
        self.assertEqual(tree.branch("one").array().tolist(), [1, 2, 3, 4])
        self.assertEqual(tree.branch("two").array().tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
        self.assertEqual(tree.branch("three").array().tolist(), [b"uno", b"dos", b"tres", b"quatro"])

        # get tree again
        tree = file["tree"]
        self.assertEqual(tree.branch("one").array().tolist(), [1, 2, 3, 4])
        self.assertEqual(tree.branch("two").array().tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
        self.assertEqual(tree.branch("three").array().tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    def test_tree_arrays(self):
        file = uproot.open("tests/simple.root")

        tree = file["tree"]
        arrays = tree.arrays()
        self.assertEqual(arrays[b"one"].tolist(), [1, 2, 3, 4])
        self.assertEqual(arrays[b"two"].tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
        self.assertEqual(arrays[b"three"].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

        # get arrays again
        arrays = tree.arrays()
        self.assertEqual(arrays[b"one"].tolist(), [1, 2, 3, 4])
        self.assertEqual(arrays[b"two"].tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
        self.assertEqual(arrays[b"three"].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

        # get tree again
        tree = file["tree"]
        arrays = tree.arrays()
        self.assertEqual(arrays[b"one"].tolist(), [1, 2, 3, 4])
        self.assertEqual(arrays[b"two"].tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
        self.assertEqual(arrays[b"three"].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    def test_tree_arrayiter(self):
        # one big array
        for arrays in uproot.open("tests/foriter.root")["foriter"].arrayiter(1000):
            self.assertEqual(arrays["data"].tolist(), list(range(46)))

        # size is equal to basket size (for most baskets)
        i = 0
        for arrays in uproot.open("tests/foriter.root")["foriter"].arrayiter(6):
            self.assertEqual(arrays["data"].tolist(), list(range(i, min(i + 6, 46))))
            i += 6

        # size is smaller
        i = 0
        for arrays in uproot.open("tests/foriter.root")["foriter"].arrayiter(3):
            self.assertEqual(arrays["data"].tolist(), list(range(i, min(i + 3, 46))))
            i += 3
        i = 0
        for arrays in uproot.open("tests/foriter.root")["foriter"].arrayiter(4):
            self.assertEqual(arrays["data"].tolist(), list(range(i, min(i + 4, 46))))
            i += 4

        # size is larger
        i = 0
        for arrays in uproot.open("tests/foriter.root")["foriter"].arrayiter(12):
            self.assertEqual(arrays["data"].tolist(), list(range(i, min(i + 12, 46))))
            i += 12
        i = 0
        for arrays in uproot.open("tests/foriter.root")["foriter"].arrayiter(10):
            self.assertEqual(arrays["data"].tolist(), list(range(i, min(i + 10, 46))))
            i += 10

        # singleton case
        i = 0
        for arrays in uproot.open("tests/foriter.root")["foriter"].arrayiter(1):
            self.assertEqual(arrays["data"].tolist(), list(range(i, min(i + 1, 46))))
            i += 1

    def test_tree_arrayiter2(self):
        words = [b"zero", b"one", b"two", b"three", b"four", b"five", b"six", b"seven", b"eight", b"nine", b"ten", b"eleven", b"twelve", b"thirteen", b"fourteen", b"fifteen", b"sixteen", b"seventeen", b"eighteen", b"ninteen", b"twenty", b"twenty-one", b"twenty-two", b"twenty-three", b"twenty-four", b"twenty-five", b"twenty-six", b"twenty-seven", b"twenty-eight", b"twenty-nine", b"thirty"]

        # one big array
        for arrays in uproot.open("tests/foriter2.root")["foriter2"].arrayiter(1000):
            self.assertEqual(arrays["data"].tolist(), words)

        # size is equal to basket size (for most baskets)
        i = 0
        for arrays in uproot.open("tests/foriter2.root")["foriter2"].arrayiter(6):
            self.assertEqual(arrays["data"].tolist(), words[i:i + 6])
            i += 6

        # size is smaller
        i = 0
        for arrays in uproot.open("tests/foriter2.root")["foriter2"].arrayiter(3):
            self.assertEqual(arrays["data"].tolist(), words[i:i + 3])
            i += 3
        i = 0
        for arrays in uproot.open("tests/foriter2.root")["foriter2"].arrayiter(4):
            self.assertEqual(arrays["data"].tolist(), words[i:i + 4])
            i += 4

        # size is larger
        i = 0
        for arrays in uproot.open("tests/foriter2.root")["foriter2"].arrayiter(12):
            self.assertEqual(arrays["data"].tolist(), words[i:i + 12])
            i += 12
        i = 0
        for arrays in uproot.open("tests/foriter2.root")["foriter2"].arrayiter(10):
            self.assertEqual(arrays["data"].tolist(), words[i:i + 10])
            i += 10

        # singleton case
        i = 0
        for arrays in uproot.open("tests/foriter2.root")["foriter2"].arrayiter(1):
            self.assertEqual(arrays["data"].tolist(), words[i:i + 1])
            i += 1
