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
