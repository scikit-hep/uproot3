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

"""ROOT constants used in deserialization."""

import numpy

kByteCountMask  = numpy.int64(0x40000000)
kByteCountVMask = numpy.int64(0x4000)
kClassMask      = numpy.int64(0x80000000)
kNewClassTag    = numpy.int64(0xFFFFFFFF)

kIsOnHeap       = numpy.uint32(0x01000000)
kIsReferenced   = numpy.uint32(1 << 4)

kMapOffset      = 2
