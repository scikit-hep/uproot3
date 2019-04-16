#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import unittest

import uproot
try:
    import pandas
except ImportError:
    pandas = None

class Test(unittest.TestCase):
    if pandas is not None:
        sample = uproot.open("tests/samples/sample-6.10.05-uncompressed.root")["sample"]

    def test_flatten_False(self):
        if pandas is not None:
            df = self.sample.pandas.df(flatten=False)
            assert len(df.keys()) == 57
            assert "Af8" in df
            assert len(df.at[0, "Af8"]) == 0
            assert len(df.at[1, "Af8"]) == 1
            assert len(df.at[2, "Af8"]) == 2

    def test_flatten_None(self):
        if pandas is not None:
            df = self.sample.pandas.df(flatten=None)
            assert len(df.keys()) == 46
            assert "Af8" not in df

    def test_flatten_True(self):
        if pandas is not None:
            df = self.sample.pandas.df(flatten=True)
            assert len(df.keys()) == 57
            assert "Af8" in df
