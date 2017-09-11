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
import ROOT

import uproot

class TestTree(unittest.TestCase):
    def runTest(self):
        pass
    
    def test_simple(self):
        tree = uproot.memmap("tests/simple.root").get("tree")
        self.assertEqual(tree.branch("one").array().tolist(), [1, 2, 3, 4])
        self.assertEqual(tree.branch("two").array().tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
        self.assertEqual(list(tree.branch("three").strings()), ["uno", "dos", "tres", "quatro"])
