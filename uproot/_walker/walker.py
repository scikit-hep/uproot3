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

import struct

import numpy

class Walker(object):
    def __init__(self, *args, **kwds):
        raise TypeError("Walker is an abstract class")

    @staticmethod
    def size(format):
        return struct.calcsize(format)

    def _evaluate(self, parallel=False):
        pass

    def _unevaluate(self):
        pass

    def startcontext(self):
        pass
