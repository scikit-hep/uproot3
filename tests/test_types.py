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

import unittest

import numpy

import uproot

class TestTypes(unittest.TestCase):
    def runTest(self):
        pass

    @staticmethod
    def check(x, y):
        return x.dtype == y.dtype and x.shape == y.shape and numpy.array_equal(x, y)

    # def test_socalled_flat(self):
    #     tree = uproot.open("tests/small-flat-tree.root")["tree"]

    #     hundred = list(range(100))
    #     self.assertTrue(self.check(tree.array("Int32"), numpy.array(hundred, dtype=">i4")))
    #     self.assertTrue(self.check(tree.array("Int64"), numpy.array(hundred, dtype=">i8")))
    #     self.assertTrue(self.check(tree.array("UInt32"), numpy.array(hundred, dtype=">u4")))
    #     self.assertTrue(self.check(tree.array("UInt64"), numpy.array(hundred, dtype=">u8")))
    #     self.assertTrue(self.check(tree.array("Float32"), numpy.array(hundred, dtype=">f4")))
    #     self.assertTrue(self.check(tree.array("Float64"), numpy.array(hundred, dtype=">f8")))

    #     hundredstrings = ["evt-{0:03d}".format(x).encode("ascii") for x in range(100)]
    #     self.assertTrue(self.check(tree.array("Str"), numpy.array(hundredstrings, dtype=object)))

    #     hundredarrays = [[x] * 10 for x in range(100)]
    #     self.assertTrue(self.check(tree.array("ArrayInt32"), numpy.array(hundredarrays, dtype=">i4")))
    #     self.assertTrue(self.check(tree.array("ArrayInt64"), numpy.array(hundredarrays, dtype=">i8")))
    #     self.assertTrue(self.check(tree.array("ArrayUInt32"), numpy.array(hundredarrays, dtype=">u4")))
    #     self.assertTrue(self.check(tree.array("ArrayUInt64"), numpy.array(hundredarrays, dtype=">u8")))
    #     self.assertTrue(self.check(tree.array("ArrayFloat32"), numpy.array(hundredarrays, dtype=">f4")))
    #     self.assertTrue(self.check(tree.array("ArrayFloat64"), numpy.array(hundredarrays, dtype=">f8")))

    #     self.assertTrue(self.check(tree.array("N"), numpy.array(list(range(10)) * 10, dtype=">i4")))

    #     sliced = [[x] * (x % 10) for x in range(100)]
    #     flattened = [y for x in sliced for y in x]

    #     self.assertTrue(self.check(tree.array("SliceInt32"), numpy.array(flattened, dtype=">i4")))
    #     self.assertTrue(self.check(tree.array("SliceInt64"), numpy.array(flattened, dtype=">i8")))
    #     self.assertTrue(self.check(tree.array("SliceUInt32"), numpy.array(flattened, dtype=">u4")))
    #     self.assertTrue(self.check(tree.array("SliceUInt64"), numpy.array(flattened, dtype=">u8")))
    #     self.assertTrue(self.check(tree.array("SliceFloat32"), numpy.array(flattened, dtype=">f4")))
    #     self.assertTrue(self.check(tree.array("SliceFloat64"), numpy.array(flattened, dtype=">f8")))

    # def test_splitobject(self):
    #     tree = uproot.open("tests/small-evnt-tree-fullsplit.root")["tree"]
        
    #     self.assertTrue(self.check(tree.array("Beg"), numpy.array(["beg-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))

    #     hundred = list(range(100))
    #     self.assertTrue(self.check(tree.array("I16"), numpy.array(hundred, dtype=">i2")))
    #     self.assertTrue(self.check(tree.array("I32"), numpy.array(hundred, dtype=">i4")))
    #     self.assertTrue(self.check(tree.array("I64"), numpy.array(hundred, dtype=">i8")))
    #     self.assertTrue(self.check(tree.array("U16"), numpy.array(hundred, dtype=">u2")))
    #     self.assertTrue(self.check(tree.array("U32"), numpy.array(hundred, dtype=">u4")))
    #     self.assertTrue(self.check(tree.array("U64"), numpy.array(hundred, dtype=">u8")))
    #     self.assertTrue(self.check(tree.array("F32"), numpy.array(hundred, dtype=">f4")))
    #     self.assertTrue(self.check(tree.array("F64"), numpy.array(hundred, dtype=">f8")))

    #     self.assertTrue(self.check(tree.array("Str"), numpy.array(["evt-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))

    #     self.assertTrue(self.check(tree.array("P3.Px"), numpy.array(list(range(-1, 99)), dtype=">i4")))
    #     self.assertTrue(self.check(tree.array("P3.Py"), numpy.array(list(range(0, 100)), dtype=">f8")))
    #     self.assertTrue(self.check(tree.array("P3.Pz"), numpy.array(list(range(-1, 99)), dtype=">i4")))

    #     hundredarrays = [[x] * 10 for x in range(100)]
    #     self.assertTrue(self.check(tree.array("ArrayI16[10]"), numpy.array(hundredarrays, dtype=">i2")))
    #     self.assertTrue(self.check(tree.array("ArrayI32[10]"), numpy.array(hundredarrays, dtype=">i4")))
    #     self.assertTrue(self.check(tree.array("ArrayI64[10]"), numpy.array(hundredarrays, dtype=">i8")))
    #     self.assertTrue(self.check(tree.array("ArrayU32[10]"), numpy.array(hundredarrays, dtype=">u4")))
    #     self.assertTrue(self.check(tree.array("ArrayU64[10]"), numpy.array(hundredarrays, dtype=">u8")))
    #     self.assertTrue(self.check(tree.array("ArrayF32[10]"), numpy.array(hundredarrays, dtype=">f4")))
    #     self.assertTrue(self.check(tree.array("ArrayF64[10]"), numpy.array(hundredarrays, dtype=">f8")))

    #     self.assertTrue(self.check(tree.array("N"), numpy.array(list(range(10)) * 10, dtype=">i4")))

    #     sliced = [[x] * (x % 10) for x in range(100)]
    #     flattened = [y for x in sliced for y in x]

    #     self.assertTrue(self.check(tree.array("SliceI16"), numpy.array(flattened, dtype=">i2")))
    #     self.assertTrue(self.check(tree.array("SliceI32"), numpy.array(flattened, dtype=">i4")))
    #     self.assertTrue(self.check(tree.array("SliceI64"), numpy.array(flattened, dtype=">i8")))
    #     self.assertTrue(self.check(tree.array("SliceU16"), numpy.array(flattened, dtype=">u2")))
    #     self.assertTrue(self.check(tree.array("SliceU32"), numpy.array(flattened, dtype=">u4")))
    #     self.assertTrue(self.check(tree.array("SliceU64"), numpy.array(flattened, dtype=">u8")))
    #     self.assertTrue(self.check(tree.array("SliceF32"), numpy.array(flattened, dtype=">f4")))
    #     self.assertTrue(self.check(tree.array("SliceF64"), numpy.array(flattened, dtype=">f8")))

    #     self.assertTrue(self.check(tree.array("End"), numpy.array(["end-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))

    # def test_tclonesarray(self):
    #     tree = uproot.open("tests/mc10events.root")["Events"]
    #     self.assertEqual(tree.branchnames, [b"Info", b"GenEvtInfo", b"GenParticle", b"Electron", b"Muon", b"Tau", b"Photon", b"PV", b"AK4CHS", b"AK8CHS", b"AddAK8CHS", b"CA15CHS", b"AddCA15CHS", b"AK4Puppi", b"CA8Puppi", b"AddCA8Puppi", b"CA15Puppi", b"AddCA15Puppi"])

    #     for singleton in b"Info", b"GenEvtInfo":
    #         for branchname in tree.branch(singleton).branchnames:
    #             self.assertTrue(branchname not in tree.counter)
    #             if hasattr(tree.branch(singleton).branch(branchname), "dtype"):
    #                 self.assertEqual(tree.branch(singleton).branch(branchname).array().shape, (tree.numentries,))
                
    #     for tclonesarray in b"GenParticle", b"Electron", b"Muon", b"Tau", b"Photon", b"PV", b"AK4CHS", b"AK8CHS", b"AddAK8CHS", b"CA15CHS", b"AddCA15CHS", b"AK4Puppi", b"CA8Puppi", b"AddCA8Puppi", b"CA15Puppi", b"AddCA15Puppi":
    #         length = sum(tree.branch(tclonesarray).array())
    #         for branchname in tree.branch(tclonesarray).branchnames:
    #             self.assertEqual(tree.counter[branchname], tree.Counter(tclonesarray, tclonesarray + b"_"))
    #             if hasattr(tree.branch(tclonesarray).branch(branchname), "dtype"):
    #                 self.assertEqual(tree.branch(tclonesarray).branch(branchname).array().shape, (length,))
