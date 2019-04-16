#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from os.path import join

import pytest
import uproot

ROOT = pytest.importorskip("ROOT")

def test_strings(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename) as f:
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("hello")) == "world"
    f.Close()

def test_cycle(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename) as f:
        f["hello"] = "world"
        f["hello"] = "uproot"

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("hello;1")) == "world"
    assert str(f.Get("hello;2")) == "uproot"
    f.Close()

def test_th1_varbin(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    import numpy as np
    bins = np.array([1.0, 3.0, 4.0, 10.0, 11.0, 12.0], dtype="float64")
    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, bins)
    f.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetBinWidth(1) == 2.0
    assert h.GetBinWidth(2) == 1.0
    assert h.GetBinWidth(3) == 6.0
    assert h.GetBinWidth(4) == 1.0
    assert h.GetBinWidth(5) == 1.0
