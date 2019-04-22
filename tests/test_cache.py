#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import unittest

from collections import namedtuple

import uproot

class Test(unittest.TestCase):
    def test_flat_array(self):
        branch = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]["i8"]
        expectation = [-15, -14, -13, -12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

        cache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(cache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist() == expectation[entrystart:entrystop]
            assert len(cache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist() == expectation[entrystart:entrystop]
            cache = {}

        basketcache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(basketcache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist() == expectation[entrystart:entrystop]
            assert len(basketcache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist() == expectation[entrystart:entrystop]
            basketcache = {}

        keycache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(keycache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist() == expectation[entrystart:entrystop]
            assert len(keycache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist() == expectation[entrystart:entrystop]
            keycache = {}

    def test_regular_array(self):
        branch = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]["ai8"]
        expectation = [[-14, -13, -12], [-13, -12, -11], [-12, -11, -10], [-11, -10, -9], [-10, -9, -8], [-9, -8, -7], [-8, -7, -6], [-7, -6, -5], [-6, -5, -4], [-5, -4, -3], [-4, -3, -2], [-3, -2, -1], [-2, -1, 0], [-1, 0, 1], [0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7], [6, 7, 8], [7, 8, 9], [8, 9, 10], [9, 10, 11], [10, 11, 12], [11, 12, 13], [12, 13, 14], [13, 14, 15], [14, 15, 16], [15, 16, 17]]

        cache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(cache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist() == expectation[entrystart:entrystop]
            assert len(cache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist() == expectation[entrystart:entrystop]
            cache = {}

        basketcache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(basketcache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist() == expectation[entrystart:entrystop]
            assert len(basketcache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist() == expectation[entrystart:entrystop]
            basketcache = {}

        keycache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(keycache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist() == expectation[entrystart:entrystop]
            assert len(keycache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist() == expectation[entrystart:entrystop]
            keycache = {}

    def test_irregular_array(self):
        branch = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]["Ai8"]
        expectation = [[], [-15], [-15, -13], [-15, -13, -11], [-15, -13, -11, -9], [], [-10], [-10, -8], [-10, -8, -6], [-10, -8, -6, -4], [], [-5], [-5, -3], [-5, -3, -1], [-5, -3, -1, 1], [], [0], [0, 2], [0, 2, 4], [0, 2, 4, 6], [], [5], [5, 7], [5, 7, 9], [5, 7, 9, 11], [], [10], [10, 12], [10, 12, 14], [10, 12, 14, 16]]
        assert [len(x) for x in expectation] == [0, 1, 2, 3, 4] * 6

        cache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(cache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist() == expectation[entrystart:entrystop]
            assert len(cache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist() == expectation[entrystart:entrystop]
            cache = {}

        basketcache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(basketcache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist() == expectation[entrystart:entrystop]
            assert len(basketcache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist() == expectation[entrystart:entrystop]
            basketcache = {}

        keycache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(keycache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist() == expectation[entrystart:entrystop]
            assert len(keycache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist() == expectation[entrystart:entrystop]
            keycache = {}

    def test_strings_array(self):
        branch = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]["str"]
        expectation = [b"hey-0", b"hey-1", b"hey-2", b"hey-3", b"hey-4", b"hey-5", b"hey-6", b"hey-7", b"hey-8", b"hey-9", b"hey-10", b"hey-11", b"hey-12", b"hey-13", b"hey-14", b"hey-15", b"hey-16", b"hey-17", b"hey-18", b"hey-19", b"hey-20", b"hey-21", b"hey-22", b"hey-23", b"hey-24", b"hey-25", b"hey-26", b"hey-27", b"hey-28", b"hey-29"]

        cache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(cache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist() == expectation[entrystart:entrystop]
            assert len(cache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, cache=cache).tolist() == expectation[entrystart:entrystop]
            cache = {}

        basketcache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(basketcache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist() == expectation[entrystart:entrystop]
            assert len(basketcache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, basketcache=basketcache).tolist() == expectation[entrystart:entrystop]
            basketcache = {}

        keycache = {}
        for entrystart, entrystop in [(None, None), (1, None), (1, 2), (1, 10), (10, 11), (10, 20), (6, 12), (6, 13)]:
            assert len(keycache) == 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist() == expectation[entrystart:entrystop]
            assert len(keycache) > 0
            assert branch.array(entrystart=entrystart, entrystop=entrystop, keycache=keycache).tolist() == expectation[entrystart:entrystop]
            keycache = {}
