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

class Test(unittest.TestCase):
    def runTest(self):
        pass

    def test_flat_array(self):
        branch = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]["i8"]
        expectation = [-15, -14, -13, -12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

        cache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(cache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(cache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist(), expectation[entrystart:entrystop])
            cache = {}

        basketcache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(basketcache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(basketcache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist(), expectation[entrystart:entrystop])
            basketcache = {}

        keycache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(keycache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(keycache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist(), expectation[entrystart:entrystop])
            keycache = {}

    def test_regular_array(self):
        branch = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]["ai8"]
        expectation = [[-14, -13, -12], [-13, -12, -11], [-12, -11, -10], [-11, -10, -9], [-10, -9, -8], [-9, -8, -7], [-8, -7, -6], [-7, -6, -5], [-6, -5, -4], [-5, -4, -3], [-4, -3, -2], [-3, -2, -1], [-2, -1, 0], [-1, 0, 1], [0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7], [6, 7, 8], [7, 8, 9], [8, 9, 10], [9, 10, 11], [10, 11, 12], [11, 12, 13], [12, 13, 14], [13, 14, 15], [14, 15, 16], [15, 16, 17]]

        cache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(cache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(cache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist(), expectation[entrystart:entrystop])
            cache = {}

        basketcache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(basketcache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(basketcache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist(), expectation[entrystart:entrystop])
            basketcache = {}

        keycache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(keycache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(keycache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist(), expectation[entrystart:entrystop])
            keycache = {}

    def test_irregular_array(self):
        branch = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]["Ai8"]
        expectation = [[], [-15], [-15, -13], [-15, -13, -11], [-15, -13, -11, -9], [], [-10], [-10, -8], [-10, -8, -6], [-10, -8, -6, -4], [], [-5], [-5, -3], [-5, -3, -1], [-5, -3, -1, 1], [], [0], [0, 2], [0, 2, 4], [0, 2, 4, 6], [], [5], [5, 7], [5, 7, 9], [5, 7, 9, 11], [], [10], [10, 12], [10, 12, 14], [10, 12, 14, 16]]
        self.assertEqual([len(x) for x in expectation], [0, 1, 2, 3, 4] * 6)

        cache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(cache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(cache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist(), expectation[entrystart:entrystop])
            cache = {}

        basketcache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(basketcache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(basketcache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist(), expectation[entrystart:entrystop])
            basketcache = {}

        keycache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(keycache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(keycache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist(), expectation[entrystart:entrystop])
            keycache = {}

    def test_strings_array(self):
        branch = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]["str"]
        expectation = [b"hey-0", b"hey-1", b"hey-2", b"hey-3", b"hey-4", b"hey-5", b"hey-6", b"hey-7", b"hey-8", b"hey-9", b"hey-10", b"hey-11", b"hey-12", b"hey-13", b"hey-14", b"hey-15", b"hey-16", b"hey-17", b"hey-18", b"hey-19", b"hey-20", b"hey-21", b"hey-22", b"hey-23", b"hey-24", b"hey-25", b"hey-26", b"hey-27", b"hey-28", b"hey-29"]

        cache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(cache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(cache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist(), expectation[entrystart:entrystop])
            cache = {}

        basketcache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(basketcache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(basketcache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist(), expectation[entrystart:entrystop])
            basketcache = {}

        keycache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            self.assertTrue(len(keycache) == 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist(), expectation[entrystart:entrystop])
            self.assertTrue(len(keycache) > 0)
            self.assertEqual(branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist(), expectation[entrystart:entrystop])
            keycache = {}
