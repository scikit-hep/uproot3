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

from collections import namedtuple
import unittest

import numpy

import uproot

def basest(array):
    while getattr(array, "base", None) is not None:
        array = array.base
    return array

class TestTree(unittest.TestCase):
    def runTest(self):
        pass

    def test_branch_flat_basket(self):
        branch = uproot.open("tests/sample-6.10.05-uncompressed.root")["sample"]["i8"]
        interpretation = branch._normalize_interpretation(None)
        entrystart, entrystop = branch._normalize_entrystartstop(None, None)
        local_entrystart, local_entrystop = branch._localentries(0, entrystart, entrystop)

        one = branch._basket(0, interpretation, local_entrystart, local_entrystop, None, None)
        two = branch._basket(0, interpretation, local_entrystart, local_entrystop, None, None)
        self.assertTrue(numpy.array_equal(one, numpy.array([-15, -14, -13], dtype=">i8")))
        self.assertTrue(basest(one) is basest(two))

        three = branch.basket(0)
        self.assertTrue(numpy.array_equal(three, numpy.array([-15, -14, -13], dtype=">i8")))
        self.assertFalse(basest(one) is basest(three))

    def test_branch_regular_basket(self):
        branch = uproot.open("tests/sample-6.10.05-uncompressed.root")["sample"]["ai8"]
        interpretation = branch._normalize_interpretation(None)
        entrystart, entrystop = branch._normalize_entrystartstop(None, None)
        local_entrystart, local_entrystop = branch._localentries(0, entrystart, entrystop)

        one = branch._basket(0, interpretation, local_entrystart, local_entrystop, None, None)
        two = branch._basket(0, interpretation, local_entrystart, local_entrystop, None, None)
        self.assertTrue(numpy.array_equal(one, numpy.array([[-14, -13, -12]], dtype=">i8")))
        self.assertTrue(basest(one) is basest(two))

        three = branch.basket(0)
        self.assertTrue(numpy.array_equal(three, numpy.array([[-14, -13, -12]], dtype=">i8")))
        self.assertFalse(basest(one) is basest(three))

        self.assertEqual(branch.basket(0, interpretation.to(todims=(3,))).shape, (1, 3))
        self.assertEqual(branch.basket(0, interpretation.to(todims=())).shape, (3,))
        self.assertEqual(branch.basket(0, interpretation.to(todims=(1,))).shape, (3, 1))
        self.assertEqual(branch.basket(0, interpretation.to(todims=(1, 1))).shape, (3, 1, 1))
        self.assertEqual(branch.basket(0, interpretation.to(todims=(1, 3))).shape, (1, 1, 3))

    def test_branch_irregular_basket(self):
        branch = uproot.open("tests/sample-6.10.05-uncompressed.root")["sample"]["Ai8"]
        interpretation = branch._normalize_interpretation(None)
        entrystart, entrystop = branch._normalize_entrystartstop(None, None)
        local_entrystart, local_entrystop = branch._localentries(0, entrystart, entrystop)

        one = branch._basket(0, interpretation, local_entrystart, local_entrystop, None, None)
        two = branch._basket(0, interpretation, local_entrystart, local_entrystop, None, None)
        self.assertTrue(numpy.array_equal(one[0], numpy.array([], dtype=">i8")))
        self.assertTrue(numpy.array_equal(one[1], numpy.array([-15], dtype=">i8")))
        self.assertTrue(basest(one.contents) is basest(two.contents))

        three = branch.basket(0)
        self.assertTrue(numpy.array_equal(three[0], numpy.array([], dtype=">i8")))
        self.assertTrue(numpy.array_equal(three[1], numpy.array([-15], dtype=">i8")))


    # def test_branch_array(self):
    #     file = uproot.open("tests/simple.root")
    #     repr(file)

    #     tree = file["tree"]
    #     repr(tree)
    #     repr(tree["one"])

    #     self.assertEqual(tree["one"].array().tolist(), [1, 2, 3, 4])
    #     self.assertEqual(tree["two"].array().tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
    #     self.assertEqual(tree["three"].array().tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    #     self.assertEqual(tree["one"].array().tolist(), [1, 2, 3, 4])
    #     self.assertEqual(tree["two"].array().tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
    #     self.assertEqual(tree["three"].array().tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    #     tree = file["tree"]
    #     self.assertEqual(tree["one"].array().tolist(), [1, 2, 3, 4])
    #     self.assertEqual(tree["two"].array().tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
    #     self.assertEqual(tree["three"].array().tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    # def test_tree_arrays(self):
    #     file = uproot.open("tests/simple.root")

    #     tree = file["tree"]
    #     arrays = tree.arrays()
    #     self.assertEqual(arrays[b"one"].tolist(), [1, 2, 3, 4])
    #     self.assertEqual(arrays[b"two"].tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
    #     self.assertEqual(arrays[b"three"].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    #     # get arrays again
    #     arrays = tree.arrays()
    #     self.assertEqual(arrays[b"one"].tolist(), [1, 2, 3, 4])
    #     self.assertEqual(arrays[b"two"].tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
    #     self.assertEqual(arrays[b"three"].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    #     # get tree again
    #     tree = file["tree"]
    #     arrays = tree.arrays()
    #     self.assertEqual(arrays[b"one"].tolist(), [1, 2, 3, 4])
    #     self.assertEqual(arrays[b"two"].tolist(), numpy.array([1.1, 2.2, 3.3, 4.4], dtype=numpy.float32).tolist())
    #     self.assertEqual(arrays[b"three"].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    # def test_tree_iterator1(self):
    #     # one big array
    #     for arrays in uproot.open("tests/foriter.root")["foriter"].iterator(1000):
    #         self.assertEqual(arrays[b"data"].tolist(), list(range(46)))

    #     # size is equal to basket size (for most baskets)
    #     i = 0
    #     for arrays in uproot.open("tests/foriter.root")["foriter"].iterator(6):
    #         self.assertEqual(arrays[b"data"].tolist(), list(range(i, min(i + 6, 46))))
    #         i += 6

    #     # size is smaller
    #     i = 0
    #     for arrays in uproot.open("tests/foriter.root")["foriter"].iterator(3):
    #         self.assertEqual(arrays[b"data"].tolist(), list(range(i, min(i + 3, 46))))
    #         i += 3
    #     i = 0
    #     for arrays in uproot.open("tests/foriter.root")["foriter"].iterator(4):
    #         self.assertEqual(arrays[b"data"].tolist(), list(range(i, min(i + 4, 46))))
    #         i += 4

    #     # size is larger
    #     i = 0
    #     for arrays in uproot.open("tests/foriter.root")["foriter"].iterator(12):
    #         self.assertEqual(arrays[b"data"].tolist(), list(range(i, min(i + 12, 46))))
    #         i += 12
    #     i = 0
    #     for arrays in uproot.open("tests/foriter.root")["foriter"].iterator(10):
    #         self.assertEqual(arrays[b"data"].tolist(), list(range(i, min(i + 10, 46))))
    #         i += 10

    #     # singleton case
    #     i = 0
    #     for arrays in uproot.open("tests/foriter.root")["foriter"].iterator(1):
    #         self.assertEqual(arrays[b"data"].tolist(), list(range(i, min(i + 1, 46))))
    #         i += 1

    # def test_tree_iterator2(self):
    #     words = [b"zero", b"one", b"two", b"three", b"four", b"five", b"six", b"seven", b"eight", b"nine", b"ten", b"eleven", b"twelve", b"thirteen", b"fourteen", b"fifteen", b"sixteen", b"seventeen", b"eighteen", b"ninteen", b"twenty", b"twenty-one", b"twenty-two", b"twenty-three", b"twenty-four", b"twenty-five", b"twenty-six", b"twenty-seven", b"twenty-eight", b"twenty-nine", b"thirty"]

    #     # one big array
    #     for arrays in uproot.open("tests/foriter2.root")["foriter2"].iterator(1000):
    #         self.assertEqual(arrays[b"data"].tolist(), words)

    #     # size is equal to basket size (for most baskets)
    #     i = 0
    #     for arrays in uproot.open("tests/foriter2.root")["foriter2"].iterator(6):
    #         self.assertEqual(arrays[b"data"].tolist(), words[i:i + 6])
    #         i += 6

    #     # size is smaller
    #     i = 0
    #     for arrays in uproot.open("tests/foriter2.root")["foriter2"].iterator(3):
    #         self.assertEqual(arrays[b"data"].tolist(), words[i:i + 3])
    #         i += 3
    #     i = 0
    #     for arrays in uproot.open("tests/foriter2.root")["foriter2"].iterator(4):
    #         self.assertEqual(arrays[b"data"].tolist(), words[i:i + 4])
    #         i += 4

    #     # size is larger
    #     i = 0
    #     for arrays in uproot.open("tests/foriter2.root")["foriter2"].iterator(12):
    #         self.assertEqual(arrays[b"data"].tolist(), words[i:i + 12])
    #         i += 12
    #     i = 0
    #     for arrays in uproot.open("tests/foriter2.root")["foriter2"].iterator(10):
    #         self.assertEqual(arrays[b"data"].tolist(), words[i:i + 10])
    #         i += 10

    #     # singleton case
    #     i = 0
    #     for arrays in uproot.open("tests/foriter2.root")["foriter2"].iterator(1):
    #         self.assertEqual(arrays[b"data"].tolist(), words[i:i + 1])
    #         i += 1

    # def test_tree_iterator3(self):
    #     source = list(range(46)) + list(range(46))

    #     # one big array
    #     for arrays in uproot.iterator(1000, ["tests/foriter.root", "tests/foriter.root"], "foriter"):
    #         self.assertEqual(arrays[b"data"].tolist(), source)

    #     # size is equal to basket size (for most baskets)
    #     i = 0
    #     for arrays in uproot.iterator(6, ["tests/foriter.root", "tests/foriter.root"], "foriter"):
    #         self.assertEqual(arrays[b"data"].tolist(), source[i:min(i + 6, 46*2)])
    #         i += 6

    #     # size is smaller
    #     i = 0
    #     for arrays in uproot.iterator(3, ["tests/foriter.root", "tests/foriter.root"], "foriter"):
    #         self.assertEqual(arrays[b"data"].tolist(), source[i:min(i + 3, 46*2)])
    #         i += 3
    #     i = 0
    #     for arrays in uproot.iterator(4, ["tests/foriter.root", "tests/foriter.root"], "foriter"):
    #         self.assertEqual(arrays[b"data"].tolist(), source[i:min(i + 4, 46*2)])
    #         i += 4

    #     # size is larger
    #     i = 0
    #     for arrays in uproot.iterator(12, ["tests/foriter.root", "tests/foriter.root"], "foriter"):
    #         self.assertEqual(arrays[b"data"].tolist(), source[i:min(i + 12, 46*2)])
    #         i += 12
    #     i = 0
    #     for arrays in uproot.iterator(10, ["tests/foriter.root", "tests/foriter.root"], "foriter"):
    #         self.assertEqual(arrays[b"data"].tolist(), source[i:min(i + 10, 46*2)])
    #         i += 10

    #     # singleton case
    #     i = 0
    #     for arrays in uproot.iterator(1, ["tests/foriter.root", "tests/foriter.root"], "foriter"):
    #         self.assertEqual(arrays[b"data"].tolist(), source[i:min(i + 1, 46*2)])
    #         i += 1

    # def test_tree_iterator4(self):
    #     words2 = [b"zero", b"one", b"two", b"three", b"four", b"five", b"six", b"seven", b"eight", b"nine", b"ten", b"eleven", b"twelve", b"thirteen", b"fourteen", b"fifteen", b"sixteen", b"seventeen", b"eighteen", b"ninteen", b"twenty", b"twenty-one", b"twenty-two", b"twenty-three", b"twenty-four", b"twenty-five", b"twenty-six", b"twenty-seven", b"twenty-eight", b"twenty-nine", b"thirty"] * 2

    #     # one big array
    #     for arrays in uproot.iterator(1000, ["tests/foriter2.root", "tests/foriter2.root"], "foriter2"):
    #         self.assertEqual(arrays[b"data"].tolist(), words2)

    #     # size is equal to basket size (for most baskets)
    #     i = 0
    #     for arrays in uproot.iterator(6, ["tests/foriter2.root", "tests/foriter2.root"], "foriter2"):
    #         self.assertEqual(arrays[b"data"].tolist(), words2[i:i + 6])
    #         i += 6

    #     # size is smaller
    #     i = 0
    #     for arrays in uproot.iterator(3, ["tests/foriter2.root", "tests/foriter2.root"], "foriter2"):
    #         self.assertEqual(arrays[b"data"].tolist(), words2[i:i + 3])
    #         i += 3
    #     i = 0
    #     for arrays in uproot.iterator(4, ["tests/foriter2.root", "tests/foriter2.root"], "foriter2"):
    #         self.assertEqual(arrays[b"data"].tolist(), words2[i:i + 4])
    #         i += 4

    #     # size is larger
    #     i = 0
    #     for arrays in uproot.iterator(12, ["tests/foriter2.root", "tests/foriter2.root"], "foriter2"):
    #         self.assertEqual(arrays[b"data"].tolist(), words2[i:i + 12])
    #         i += 12
    #     i = 0
    #     for arrays in uproot.iterator(10, ["tests/foriter2.root", "tests/foriter2.root"], "foriter2"):
    #         self.assertEqual(arrays[b"data"].tolist(), words2[i:i + 10])
    #         i += 10

    #     # singleton case
    #     i = 0
    #     for arrays in uproot.iterator(1, ["tests/foriter2.root", "tests/foriter2.root"], "foriter2"):
    #         self.assertEqual(arrays[b"data"].tolist(), words2[i:i + 1])
    #         i += 1

    # def test_directories(self):
    #     file = uproot.open("tests/nesteddirs.root")
    #     self.assertEqual(file.contents, {b"one;1": b"TDirectory", b"three;1": b"TDirectory"})
    #     self.assertEqual(file.allcontents, {b"one/two;1": b"TDirectory", b"one/two/tree;1": b"TTree", b"three/tree;1": b"TTree", b"one;1": b"TDirectory", b"one/tree;1": b"TTree", b"three;1": b"TDirectory"})

    #     self.assertEqual(file["one"]["tree"].branchnames, [b"one", b"two", b"three"])
    #     self.assertEqual(file["one"].get("tree", 1).branchnames, [b"one", b"two", b"three"])
    #     self.assertEqual(file["one/tree;1"].branchnames, [b"one", b"two", b"three"])
    #     self.assertEqual(file["one/two/tree;1"].branchnames, [b"Int32", b"Int64", b"UInt32", b"UInt64", b"Float32", b"Float64", b"Str", b"ArrayInt32", b"ArrayInt64", b"ArrayUInt32", b"ArrayUInt64", b"ArrayFloat32", b"ArrayFloat64", b"N", b"SliceInt32", b"SliceInt64", b"SliceUInt32", b"SliceUInt64", b"SliceFloat32", b"SliceFloat64"])
    #     self.assertEqual(file["three/tree;1"].branchnames, [b"evt"])

    #     self.assertEqual(dict((name, array.tolist()) for name, array in file["one/tree"].arrays(["one", "two", "three"]).items()), {b"one": [1, 2, 3, 4], b"two": [1.100000023841858, 2.200000047683716, 3.299999952316284, 4.400000095367432], b"three": [b"uno", b"dos", b"tres", b"quatro"]})
    #     self.assertEqual(file["one/two/tree"].array("Int32").shape, (100,))
    #     self.assertEqual(file["three/tree"].array("I32").shape, (100,))

    #     file = uproot.open("tests/nesteddirs.root")

    #     self.assertEqual(file["one/tree"].branchnames, [b"one", b"two", b"three"])
    #     self.assertEqual(file["one/two/tree"].branchnames, [b"Int32", b"Int64", b"UInt32", b"UInt64", b"Float32", b"Float64", b"Str", b"ArrayInt32", b"ArrayInt64", b"ArrayUInt32", b"ArrayUInt64", b"ArrayFloat32", b"ArrayFloat64", b"N", b"SliceInt32", b"SliceInt64", b"SliceUInt32", b"SliceUInt64", b"SliceFloat32", b"SliceFloat64"])
    #     self.assertEqual(file["three/tree"].branchnames, [b"evt"])

    #     self.assertEqual(dict((name, array.tolist()) for name, array in file["one/tree;1"].arrays(["one", "two", "three"]).items()), {b"one": [1, 2, 3, 4], b"two": [1.100000023841858, 2.200000047683716, 3.299999952316284, 4.400000095367432], b"three": [b"uno", b"dos", b"tres", b"quatro"]})
    #     self.assertEqual(file["one/two/tree;1"].array("Int32").shape, (100,))
    #     self.assertEqual(file["three/tree;1"].array("I32").shape, (100,))

    # def test_cast(self):
    #     tree = uproot.open("tests/Zmumu.root")["events"]
    #     one = numpy.cast[numpy.int32](numpy.floor(tree.array("M")))
    #     two = tree.array("M", numpy.int32)
    #     self.assertEqual(one.dtype, two.dtype)
    #     self.assertEqual(one.shape, two.shape)
    #     self.assertTrue(numpy.array_equal(one, two))

    #     for (one,) in tree.iterator(10000, "M", outputtype=tuple):
    #         one = numpy.cast[numpy.int32](numpy.floor(one))
    #     for (two,) in tree.iterator(10000, {"M": numpy.int32}, outputtype=tuple):
    #         pass
    #     self.assertEqual(one.dtype, two.dtype)
    #     self.assertEqual(one.shape, two.shape)
    #     self.assertTrue(numpy.array_equal(one, two))

    # def test_pass_array(self):
    #     tree = uproot.open("tests/Zmumu.root")["events"]
    #     one = numpy.cast[numpy.int32](numpy.floor(tree.array("M")))
    #     two = numpy.zeros(one.shape, dtype=one.dtype)
    #     tree.array("M", two)
    #     self.assertTrue(numpy.array_equal(one, two))

    #     for (one,) in tree.iterator(10000, "M", outputtype=tuple):
    #         one = numpy.cast[numpy.int32](numpy.floor(one))
    #         two = numpy.zeros(one.shape, dtype=one.dtype)
    #         for (two,) in tree.iterator(10000, {"M": numpy.int32}, outputtype=tuple):
    #             self.assertTrue(numpy.array_equal(one, two))

    # def test_outputtype(self):
    #     tree = uproot.open("tests/simple.root")["tree"]

    #     arrays = tree.arrays(["three", "two", "one"], outputtype=dict)
    #     self.assertTrue(isinstance(arrays, dict))
    #     self.assertEqual(arrays[b"one"].tolist(), [1, 2, 3, 4])
    #     self.assertEqual(arrays[b"three"].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    #     arrays = tree.arrays(["three", "two", "one"], outputtype=tuple)
    #     self.assertTrue(isinstance(arrays, tuple))
    #     self.assertEqual(arrays[2].tolist(), [1, 2, 3, 4])
    #     self.assertEqual(arrays[0].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    #     arrays = tree.arrays(["three", "two", "one"], outputtype=namedtuple)
    #     self.assertEqual(arrays.one.tolist(), [1, 2, 3, 4])
    #     self.assertEqual(arrays.three.tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    #     arrays = tree.arrays(["three", "two", "one"], outputtype=list)
    #     self.assertTrue(isinstance(arrays, list))
    #     self.assertEqual(arrays[2].tolist(), [1, 2, 3, 4])
    #     self.assertEqual(arrays[0].tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    #     class Awesome(object):
    #         def __init__(self, one, two, three):
    #             self.one = one
    #             self.two = two
    #             self.three = three

    #     arrays = tree.arrays(["one", "two", "three"], outputtype=Awesome)
    #     self.assertTrue(isinstance(arrays, Awesome))
    #     self.assertEqual(arrays.one.tolist(), [1, 2, 3, 4])
    #     self.assertEqual(arrays.three.tolist(), [b"uno", b"dos", b"tres", b"quatro"])

    # def test_informational(self):
    #     self.assertEqual(uproot.open("tests/simple.root")["tree"].branchnames, [b"one", b"two", b"three"])
    #     self.assertEqual(uproot.open("tests/simple.root")["tree"].branchtypes, {b"two": numpy.dtype(">f4"), b"one": numpy.dtype(">i4"), b"three": numpy.dtype("O")})
    #     self.assertEqual(uproot.open("tests/small-evnt-tree-fullsplit.root")["tree"].allbranchnames, [b"evt", b"Beg", b"I16", b"I32", b"I64", b"U16", b"U32", b"U64", b"F32", b"F64", b"Str", b"P3.Px", b"P3.Py", b"P3.Pz", b"ArrayI16[10]", b"ArrayI32[10]", b"ArrayI64[10]", b"ArrayU16[10]", b"ArrayU32[10]", b"ArrayU64[10]", b"ArrayF32[10]", b"ArrayF64[10]", b"N", b"SliceI16", b"SliceI32", b"SliceI64", b"SliceU16", b"SliceU32", b"SliceU64", b"SliceF32", b"SliceF64", b"End"])
    #     self.assertEqual(uproot.open("tests/small-evnt-tree-fullsplit.root")["tree"].allbranchtypes, {b"Str": numpy.dtype("O"), b"P3.Px": numpy.dtype(">i4"), b"I64": numpy.dtype(">i8"), b"U64": numpy.dtype(">u8"), b"ArrayF32[10]": numpy.dtype(">f4"), b"SliceI16": numpy.dtype(">i2"), b"ArrayI64[10]": numpy.dtype(">i8"), b"evt": numpy.dtype(">i4"), b"SliceF64": numpy.dtype(">f8"), b"End": numpy.dtype("O"), b"U32": numpy.dtype(">u4"), b"Beg": numpy.dtype("O"), b"I32": numpy.dtype(">i4"), b"N": numpy.dtype(">i4"), b"SliceI32": numpy.dtype(">i4"), b"P3.Py": numpy.dtype(">f8"), b"U16": numpy.dtype(">u2"), b"SliceU32": numpy.dtype(">u4"), b"P3.Pz": numpy.dtype(">i4"), b"ArrayI32[10]": numpy.dtype(">i4"), b"ArrayF64[10]": numpy.dtype(">f8"), b"I16": numpy.dtype(">i2"), b"SliceU64": numpy.dtype(">u8"), b"F64": numpy.dtype(">f8"), b"ArrayI16[10]": numpy.dtype(">i2"), b"ArrayU16[10]": numpy.dtype(">u2"), b"ArrayU32[10]": numpy.dtype(">u4"), b"F32": numpy.dtype(">f4"), b"SliceF32": numpy.dtype(">f4"), b"ArrayU64[10]": numpy.dtype(">u8"), b"SliceU16": numpy.dtype(">u2"), b"SliceI64": numpy.dtype(">i8")})

    # def test_tree_lazy(self):
    #     tree = uproot.open("tests/sample-5.30.00-uncompressed.root")["sample"]

    #     for branchname in b"u1", b"i8", b"Ai8", b"f4", b"af4":
    #         strict = tree[branchname].array()

    #         lazy = tree[branchname].lazyarray()
    #         for i in range(len(lazy)):
    #             self.assertEqual(lazy[i].tolist(), strict[i].tolist())

    #         lazy = tree[branchname].lazyarray()
    #         for i in range(len(lazy), 0, -1):
    #             self.assertEqual(lazy[i - 1].tolist(), strict[i - 1].tolist())

    #         lazy = tree[branchname].lazyarray()
    #         for i in range(len(lazy)):
    #             self.assertEqual(lazy[i : i + 3].tolist(), strict[i : i + 3].tolist())

    #         lazy = tree[branchname].lazyarray()
    #         for i in range(len(lazy), 0, -1):
    #             self.assertEqual(lazy[i - 1 : i + 3].tolist(), strict[i - 1 : i + 3].tolist())
