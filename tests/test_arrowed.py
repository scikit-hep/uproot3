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

from collections import namedtuple
import unittest

import numpy

import uproot

class TestArrowed(unittest.TestCase):
    def runTest(self):
        pass
    
    def test_arrowed(self):
        try:
            import arrowed
        except ImportError:
            return

        tree = uproot.open("tests/mc10events.root")["Events"]

        print tree.to.arrowed.spec().format()
