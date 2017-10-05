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
        tree.to.arrowed.schema().format()
        proxy = tree.to.arrowed.proxy()
        
        self.assertEqual(proxy[0].AddAK8CHS[0].sj1._toJson(), {"phi": 0.3957490921020508, "pt": 151.0018768310547, "m": 3.729222536087036, "q": -0.19528420269489288, "eta": -2.625094413757324, "csv": -10.0, "qgid": -1.0})

        tree.to.arrowed.run(lambda event: event.Info.runNum, debug=True)
