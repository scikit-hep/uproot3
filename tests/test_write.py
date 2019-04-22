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

def test_th1(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.Sumw2()
    h.Fill(1.0, 3)
    h.Fill(2.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    sums = [0.0, 25.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    bincontents = [7.0, 0.0, 0.0, 0.0, 0.0]
    assert list(h.GetSumw2()) == sums
    count = 0
    for x in range(1, 6):
        assert h.GetBinContent(x) == bincontents[count]
        count += 1
    assert h.GetNbinsX() == 5
    assert h.GetMean() == 1.5714285714285714
    assert h.GetRMS() == 0.4948716593053938

def test_th1_varbin(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    import numpy as np
    bins = np.array([1.0, 3.0, 4.0, 10.0, 11.0, 12.0], dtype="float64")
    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, bins)
    h.Write()
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

def test_th2(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH2F("hvar", "title", 5, 1, 10, 6, 1, 20)
    h.Sumw2()
    h.Fill(1.0, 5.0, 3)
    h.Fill(2.0, 10.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    sums = [0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 9.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 16.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0 , 0.0]
    bincontents = [0.0, 3.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    count = 0
    for x in range(1, 6):
        for y in range(1, 7):
            assert h.GetBinContent(x, y) == bincontents[count]
            count += 1
    assert list(h.GetSumw2()) == sums
    assert h.GetMean() == 1.5714285714285714
    assert h.GetRMS() == 0.4948716593053938
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6

def test_th2_varbin(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    import numpy as np
    binsx = np.array([1.0, 3.0, 4.0, 10.0, 11.0, 12.0], dtype="float64")
    binsy = np.array([1.0, 3.0, 4.0, 10.0, 11.0, 12.0, 20.0], dtype="float64")
    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH2F("hvar", "title", 5, binsx, 6, binsy)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6

def test_th3(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH3F("hvar", "title", 5, 1, 10, 6, 1, 20, 7, 1, 30)
    h.Sumw2()
    h.Fill(1.0, 5.0, 8.0, 3)
    h.Fill(2.0, 10.0, 9.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    sums = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 16.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    bincontents = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6
    assert h.GetNbinsZ() == 7
    assert list(h.GetSumw2()) == sums
    assert h.GetMean() == 1.5714285714285714
    assert h.GetRMS() == 0.4948716593053938
    count = 0
    for x in range(1, 6):
        for y in range(1, 7):
            for z in range(1, 8):
                assert h.GetBinContent(x, y, z) == bincontents[count]
                count += 1

def test_th3_varbin(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    import numpy as np
    binsx = np.array([1.0, 3.0, 4.0, 10.0, 11.0, 12.0], dtype="float64")
    binsy = np.array([1.0, 3.0, 4.0, 10.0, 11.0, 12.0, 20.0], dtype="float64")
    binsz = np.array([1.0, 10.0, 13.0, 14.0, 16.0, 20.0, 21.0, 23.0], dtype="float64")
    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH3F("hvar", "title", 5, binsx, 6, binsy, 7, binsz)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6
    assert h.GetNbinsZ() == 7
