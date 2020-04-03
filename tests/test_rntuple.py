#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import os

import numpy
import pytest

import awkward
import uproot

class Test(object):
    def test_read_anchor(self):
        f = uproot.open("tests/samples/ntpl001_staff.root")
        rntuple = f["Staff"]
        assert rntuple._fVersion == 0
        assert rntuple._fSize == 48
        assert rntuple._fSeekHeader == 854
        assert rntuple._fNBytesHeader == 537
        assert rntuple._fLenHeader == 2495
        assert rntuple._fSeekFooter == 72369
        assert rntuple._fNBytesFooter == 285
        assert rntuple._fLenFooter == 804
        assert rntuple._fReserved == 0
