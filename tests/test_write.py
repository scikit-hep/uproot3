#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from os.path import join

import pytest
import numpy

import uproot
from uproot.write.objects.TTree import newtree, newbranch

ROOT = pytest.importorskip("ROOT")

def test_strings(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=None) as f:
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("hello")) == "world"
    f.Close()

def test_cycle(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=None) as f:
        f["hello"] = "world"
        f["hello"] = "uproot"

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("hello;1")) == "world"
    assert str(f.Get("hello;2")) == "uproot"
    f.Close()

def test_zlib(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=uproot.ZLIB(1)) as f:
        f["hello"] = "a"*2000

    f = ROOT.TFile.Open(filename)
    assert f.GetCompressionAlgorithm() == uproot.const.kZLIB
    assert f.GetCompressionLevel() == 1
    assert str(f.Get("hello")) == "a"*2000
    f.Close()

def test_compresschange(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=uproot.ZLIB(2)) as f:
        f.compression = uproot.ZLIB(3)
        f["hello"] = "a"*2000

    f = ROOT.TFile.Open(filename)
    assert f.GetCompressionAlgorithm() == uproot.const.kZLIB
    assert f.GetCompressionLevel() == 3

def test_nocompress(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=None) as f:
        f["hello"] = "a"*2000

    f = ROOT.TFile.Open(filename)
    assert f.GetCompressionFactor() == 1
    assert str(f.Get("hello")) == "a"*2000
    f.Close()

def test_compress_small_data(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=uproot.ZLIB(4)) as f:
        f["hello"] = "a"

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("hello")) == "a"
    f.Close()

def test_lzma(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=uproot.LZMA(1)) as f:
        f["hello"] = "a"*2000

    f = ROOT.TFile.Open(filename)
    assert f.GetCompressionAlgorithm() == uproot.const.kLZMA
    assert f.GetCompressionLevel() == 1
    assert str(f.Get("hello")) == "a"*2000
    f.Close()

def test_lz4_leveldown(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=uproot.LZ4(5)) as f:
        f["hello"] = "a"*2000

    f = ROOT.TFile.Open(filename)
    assert (f.GetCompressionAlgorithm()) == uproot.const.kLZ4
    assert str(f.Get("hello")) == "a"*2000
    f.Close()

def test_lz4_levelup(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=uproot.LZ4(5)) as f:
        f["hello"] = "a"*2000

    f = ROOT.TFile.Open(filename)
    assert (f.GetCompressionAlgorithm()) == uproot.const.kLZ4
    assert (f.GetCompressionLevel()) == 5
    assert str(f.Get("hello")) == "a"*2000
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
    with uproot.recreate(filename, compression=None) as f:
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

def test_th1_uproot(tmp_path):
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
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    assert "TH1" in uproot.open(filename)["test"]._classname.decode("utf-8")

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
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetBinWidth(1) == 2.0
    assert h.GetBinWidth(2) == 1.0
    assert h.GetBinWidth(3) == 6.0
    assert h.GetBinWidth(4) == 1.0
    assert h.GetBinWidth(5) == 1.0

def test_compressed_th1(tmp_path):
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
    with uproot.recreate(filename, compression=uproot.ZLIB(1)) as f:
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
    with uproot.recreate(filename, compression=None) as f:
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

def test_th2_uproot(tmp_path):
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
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    assert "TH2" in uproot.open(filename)["test"]._classname.decode("utf-8")

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
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6

def test_compressed_th2(tmp_path):
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
    with uproot.recreate(filename, compression=uproot.ZLIB(1)) as f:
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
    with uproot.recreate(filename, compression=None) as f:
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

def test_th3_uproot(tmp_path):
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
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    assert "TH3" in uproot.open(filename)["test"]._classname.decode("utf-8")

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
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6
    assert h.GetNbinsZ() == 7

def test_compressed_th3(tmp_path):
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
    with uproot.recreate(filename, compression=uproot.ZLIB(1)) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6
    assert h.GetNbinsZ() == 7

def test_tprofile(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile("hvar", "title", 5, 1, 10)
    h.Sumw2()
    h.Fill(1.0, 3)
    h.Fill(2.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    sums = [0.0, 25.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    bincontents = [3.5, 0.0, 0.0, 0.0, 0.0]
    assert list(h.GetSumw2()) == sums
    assert h.GetMean() == 1.5
    assert h.GetRMS() == 0.5
    count = 0
    for x in range(1, 6):
        assert h.GetBinContent(x) == bincontents[count]
        count += 1

def test_tprofile_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile("hvar", "title", 5, 1, 10)
    h.Sumw2()
    h.Fill(1.0, 3)
    h.Fill(2.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    assert uproot.open(filename)["test"]._classname == b"TProfile"

def test_compressed_tprofile(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile("hvar", "title", 5, 1, 10)
    h.Sumw2()
    h.Fill(1.0, 3)
    h.Fill(2.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=uproot.LZMA(5)) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    sums = [0.0, 25.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    bincontents = [3.5, 0.0, 0.0, 0.0, 0.0]
    assert list(h.GetSumw2()) == sums
    assert h.GetMean() == 1.5
    assert h.GetRMS() == 0.5
    count = 0
    for x in range(1, 6):
        assert h.GetBinContent(x) == bincontents[count]
        count += 1

def test_tprofile2d(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile2D("hvar", "title", 5, 1, 10, 6, 1, 20)
    h.Sumw2()
    h.Fill(1.0, 5.0, 3)
    h.Fill(2.0, 10.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
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
    assert h.GetMean() == 1.5
    assert h.GetRMS() == 0.5
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6

def test_tprofile2d_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile2D("hvar", "title", 5, 1, 10, 6, 1, 20)
    h.Sumw2()
    h.Fill(1.0, 5.0, 3)
    h.Fill(2.0, 10.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    assert uproot.open(filename)["test"]._classname == b"TProfile2D"

def test_compressed_tprofile2d(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile2D("hvar", "title", 5, 1, 10, 6, 1, 20)
    h.Sumw2()
    h.Fill(1.0, 5.0, 3)
    h.Fill(2.0, 10.0, 4)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=uproot.LZMA(5)) as f:
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
    assert h.GetMean() == 1.5
    assert h.GetRMS() == 0.5
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6

def test_tprofile3d(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile3D("hvar", "title", 5, 1, 10, 6, 1, 20, 8, 2, 8)
    h.Sumw2()
    h.Fill(1.0, 5.0, 3, 6)
    h.Fill(2.0, 10.0, 4, 7)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    sums = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 36.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 49.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    bincontents = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    count = 0
    for x in range(1, 6):
        for y in range(1, 7):
            for z in range(1, 9):
                assert h.GetBinContent(x, y, z) == bincontents[count]
                count += 1
    assert list(h.GetSumw2()) == sums
    assert h.GetMean() == 1.5
    assert h.GetRMS() == 0.5
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6
    assert h.GetNbinsZ() == 8

def test_tprofile3d_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile3D("hvar", "title", 5, 1, 10, 6, 1, 20, 8, 2, 5)
    h.Sumw2()
    h.Fill(1.0, 5.0, 3, 5)
    h.Fill(2.0, 10.0, 4, 8)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    assert uproot.open(filename)["test"]._classname == b"TProfile3D"

def test_compressed_tprofile3d(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TProfile3D("hvar", "title", 5, 1, 10, 6, 1, 20, 8, 2, 8)
    h.Sumw2()
    h.Fill(1.0, 5.0, 3, 6)
    h.Fill(2.0, 10.0, 4, 7)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=uproot.LZMA(6)) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    sums = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 36.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 49.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    bincontents = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    count = 0
    for x in range(1, 6):
        for y in range(1, 7):
            for z in range(1, 9):
                assert h.GetBinContent(x, y, z) == bincontents[count]
                count += 1
    assert list(h.GetSumw2()) == sums
    assert h.GetMean() == 1.5
    assert h.GetRMS() == 0.5
    assert h.GetNbinsX() == 5
    assert h.GetNbinsY() == 6
    assert h.GetNbinsZ() == 8

def test_dir_allocation(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=None) as f:
        for i in range(1, 101):
            f["a"*i] = "a"*i

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("a"*100)) == "a"*100
    f.Close()

def test_taxis_axisbins(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.Fill(1.0, 3)
    h.Fill(3.0, 8)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetXaxis().GetFirst() == 1
    assert h.GetXaxis().GetLast() == 5

def test_taxis_time(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.GetXaxis().SetTimeDisplay(1)
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetXaxis().GetTimeDisplay() == True

def test_th1_binlabel1(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.Fill(1.0, 3)
    h.GetXaxis().SetBinLabel(1, "Hi")
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetXaxis().GetBinLabel(1) == "Hi"

def test_th1_binlabel1_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.Fill(1.0, 3)
    h.GetXaxis().SetBinLabel(1, "Hi")
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = uproot.open(filename)
    h = f["test"]
    assert h._fXaxis._fLabels[0] == b"Hi"

def test_th1_binlabel2(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.Fill(1.0, 3)
    h.Fill(2.0, 4)
    h.GetXaxis().SetBinLabel(1, "Hi")
    h.GetXaxis().SetBinLabel(2, "Hello")
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetXaxis().GetBinLabel(1) == "Hi"
    assert h.GetXaxis().GetBinLabel(2) == "Hello"

def test_th1_binlabel2_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.Fill(1.0, 3)
    h.Fill(2.0, 4)
    h.GetXaxis().SetBinLabel(1, "Hi")
    h.GetXaxis().SetBinLabel(2, "Hello")
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = uproot.open(filename)
    h = f["test"]
    assert h._fXaxis._fLabels[0] == b"Hi"
    assert h._fXaxis._fLabels[1] == b"Hello"

def test_th2_binlabel1(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH2F("hvar", "title", 5, 1, 10, 6, 1, 20)
    h.Fill(1.0, 5.0, 3)
    h.GetXaxis().SetBinLabel(1, "Hi1")
    h.GetYaxis().SetBinLabel(2, "Hi2")
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetXaxis().GetBinLabel(1) == "Hi1"
    assert h.GetYaxis().GetBinLabel(2) == "Hi2"

def test_th3_binlabel1(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH3F("hvar", "title", 5, 1, 10, 6, 1, 20, 7, 1, 30)
    h.Fill(1.0, 5.0, 8.0, 3)
    h.GetXaxis().SetBinLabel(1, "Hi1")
    h.GetYaxis().SetBinLabel(2, "Hi2")
    h.GetZaxis().SetBinLabel(3, "Hi3")
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetXaxis().GetBinLabel(1) == "Hi1"
    assert h.GetYaxis().GetBinLabel(2) == "Hi2"
    assert h.GetZaxis().GetBinLabel(3) == "Hi3"

def test_objany_multihist(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.Fill(1.0, 3)
    h.GetXaxis().SetBinLabel(1, "Hi")
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist
        f["test1"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    h1 = f.Get("test1")
    assert h.GetXaxis().GetBinLabel(1) == "Hi"
    assert h1.GetXaxis().GetBinLabel(1) == "Hi"

def test_objany_multihist_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")
    testfile = join(str(tmp_path), "test.root")

    f = ROOT.TFile.Open(testfile, "RECREATE")
    h = ROOT.TH1F("hvar", "title", 5, 1, 10)
    h.Fill(1.0, 3)
    h.GetXaxis().SetBinLabel(1, "Hi")
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist
        f["test1"] = hist

    f = uproot.open(filename)
    h = f["test"]
    h1 = f["test1"]
    assert h._fXaxis._fLabels[0] == b"Hi"
    assert h1._fXaxis._fLabels[0] == b"Hi"

def test_ttree(tmp_path):
    filename = join(str(tmp_path), "example.root")

    tree = newtree()
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = ROOT.TFile.Open(filename)
    assert f.GetKey("t").GetClassName() == "TTree"

def test_tree_diff_interface(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=None) as f:
        f.newtree("t")

    f = ROOT.TFile.Open(filename)
    assert f.GetKey("t").GetClassName() == "TTree"

def test_ttree_multiple(tmp_path):
    filename = join(str(tmp_path), "example.root")

    tree = newtree()
    with uproot.recreate(filename, compression=None) as f:
        for i in range(100):
            f["t"*(i+1)] = tree

    f = ROOT.TFile.Open(filename)
    for i in range(100):
        assert f.GetKey("t"*(i+1)).GetClassName() == "TTree"

def test_ttree_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    tree = newtree()
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = uproot.open(filename)
    assert f["t"]._classname == b"TTree"

def test_ttree_multiple_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    tree = newtree()
    with uproot.recreate(filename, compression=None) as f:
        for i in range(100):
            f["t"*(i+1)] = tree

    f = uproot.open(filename)
    for i in range(100):
        assert f["t"*(i+1)]._classname == b"TTree"

def test_ttree_empty_tbranch(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = ROOT.TFile.Open(filename)
    assert f.Get("t").GetBranch("intBranch").GetName() == "intBranch"

def test_ttree_empty_tbranch_multitree(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        for i in range(10):
            f["t" * (i + 1)] = tree

    f = ROOT.TFile.Open(filename)
    for i in range(10):
        assert f.Get("t" * (i + 1)).GetBranch("intBranch").GetName() == "intBranch"

def test_ttree_empty_tbranch_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = uproot.open(filename)
    assert f["t"]["intBranch"]._classname == b"TBranch"

def test_ttree_empty_tbranch_multitree_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        for i in range(10):
            f["t"*(i+1)] = tree

    f = uproot.open(filename)
    for i in range(10):
        assert f["t" * (i + 1)]["intBranch"]._classname == b"TBranch"

def test_ttree_empty_tbranch_multiple(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b, "testbranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = ROOT.TFile.Open(filename)
    assert f.Get("t").GetBranch("intBranch").GetName() == "intBranch"
    assert f.Get("t").GetBranch("testbranch").GetName() == "testbranch"

def test_ttree_empty_tbranch_multiple_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b, "testbranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = uproot.open(filename)
    assert f["t"]["intBranch"]._classname == b"TBranch"
    assert f["t"]["testbranch"]._classname == b"TBranch"

def test_ttree_empty_tbranch_diff_type(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int64")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = ROOT.TFile.Open(filename)
    assert f.Get("t").GetBranch("intBranch").GetName() == "intBranch"

def test_ttree_empty_tbranch_title(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32", title="hi")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = ROOT.TFile.Open(filename)
    assert f.Get("t").GetBranch("intBranch").GetTitle() == "hi"

def test_hist_rewrite_root(tmp_path):
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
    with uproot.recreate(filename, compression=None) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename, "UPDATE")
    t = ROOT.TObjString("Hello World")
    t.Write()
    f.Close()

    f = ROOT.TFile.Open(filename)
    assert f.Get("Hello World") == "Hello World"

def test_empty_ttree_rewrite_root(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = ROOT.TFile.Open(filename, "UPDATE")
    t = ROOT.TObjString("Hello World")
    t.Write()
    f.Close()

    f = ROOT.TFile.Open(filename)
    assert f.Get("Hello World") == "Hello World"

def test_string_rewrite_root(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=None) as f:
        f["a"*5] = "a"*5

    f = ROOT.TFile.Open(filename, "UPDATE")
    t = ROOT.TObjString("Hello World")
    t.Write()
    f.Close()

    f = ROOT.TFile.Open(filename)
    assert f.Get("Hello World") == "Hello World"

def test_string_rewrite_root_compress(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compression=uproot.ZLIB(4)) as f:
        f["a"*5] = "a"*5

    f = ROOT.TFile.Open(filename, "UPDATE")
    t = ROOT.TObjString("Hello World")
    t.Write()
    f.Close()

    f = ROOT.TFile.Open(filename)
    assert f.Get("Hello World") == "Hello World"

def test_branch_alt_interface(tmp_path):
    filename = join(str(tmp_path), "example.root")

    branchdict = {"intBranch": "int"}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree

    f = ROOT.TFile.Open(filename)
    assert f.Get("t").GetBranch("intBranch").GetName() == "intBranch"

def test_branch_basket_one(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(5):
        assert a[i] == treedata[i]

def test_branch_basket_one_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5]).astype("int32").newbyteorder(">")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = uproot.open(filename)
    tree = f["t"]
    treedata = tree.array("intBranch")
    for i in range(5):
        assert a[i] == treedata[i]

def test_branch_basket_one_rewrite_root(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5]).astype("int32").newbyteorder(">")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename, "UPDATE")
    t = ROOT.TObjString("Hello World")
    t.Write()
    f.Close()

    f = ROOT.TFile.Open(filename)
    assert f.Get("Hello World") == "Hello World"

def test_branch_basket_one_more_data(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = []
    for i in range(0, 100):
        a.append(i)
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(0, 100):
        assert a[i] == treedata[i]

def test_branch_basket_one_less_data(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(4):
        assert a[i] == treedata[i]

def test_branch_basket_one_tleafb(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int8")
    branchdict = {"int8Branch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype="int8")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["int8Branch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype("int8")
    for i in range(5):
        assert a[i] == treedata[i]

def test_branch_basket_one_tleaff(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("float32")
    branchdict = {"floatBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype="float32")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["floatBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype("float32")
    for i in range(5):
        assert a[i] == treedata[i]

def test_branch_basket_one_tleafd(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">f8")
    branchdict = {"float8Branch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">f8")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["float8Branch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">f8")
    for i in range(5):
        assert a[i] == treedata[i]

def test_branch_basket_one_tleafl(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i8")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i8")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i8")
    for i in range(5):
        assert a[i] == treedata[i]

def test_branch_basket_one_tleafO(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">?")
    branchdict = {"booleanBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 0, 0, 0, 1], dtype=">?")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["booleanBranch"].newbasket(a)

    ROOT.gInterpreter.Declare("""
    void readnewbasket(bool* arr, char* filename) {
        Bool_t x;
        TFile f(filename);
        auto tree = f.Get<TTree>("t");
        auto branch = tree->GetBranch("booleanBranch");
        branch->SetAddress(&x);
        for (int i=0; i<tree->GetEntries(); i++) {
            tree->GetEvent(i);
            arr[i] = x;
        }
    }""")

    testa = numpy.array([0, 0, 0, 0, 0], dtype=">?")
    ROOT.readnewbasket(testa, filename)
    for i in range(5):
        assert a[i] == testa[i]

def test_branch_basket_one_tleafs(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i2")
    branchdict = {"int2Branch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i2")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["int2Branch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i2")
    for i in range(5):
        assert a[i] == treedata[i]

def test_one_branch_multi_basket(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    b = numpy.array([6, 7, 8, 9, 10], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)
        f["t"]["intBranch"].newbasket(b)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(5):
        assert a[i] == treedata[i]
        assert b[i] == treedata[i+5]

def test_multi_branch_one_basket_same_type(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b1 = newbranch("int32")
    b2 = newbranch("int32")
    branchdict = {"intBranch": b1, "intBranch2": b2}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    b = numpy.array([6, 7, 8, 9, 10], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)
        f["t"]["intBranch2"].newbasket(b)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    intBranchdata = tree.AsMatrix(["intBranch"]).astype(">i4")
    int8Branchdata = tree.AsMatrix(["intBranch2"]).astype(">i4")
    for i in range(5):
        assert a[i] == intBranchdata[i]
        assert b[i] == int8Branchdata[i]

def test_multi_branch_one_basket_same_type_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b1 = newbranch("int32")
    b2 = newbranch("int32")
    branchdict = {"intBranch": b1, "intBranch2": b2}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    b = numpy.array([6, 7, 8, 9, 10], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)
        f["t"]["intBranch2"].newbasket(b)

    f = uproot.open(filename)
    tree = f["t"]
    intBranchdata = tree.array("intBranch")
    int8Branchdata = tree.array("intBranch2")
    for i in range(5):
        assert a[i] == intBranchdata[i]
        assert b[i] == int8Branchdata[i]

def test_multi_branch_one_basket_diff_type(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b1 = newbranch("int32")
    b2 = newbranch("int64")
    branchdict = {"intBranch": b1, "int8Branch": b2}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    b = numpy.array([6, 7, 8, 9, 10], dtype=">i8")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)
        f["t"]["int8Branch"].newbasket(b)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    intBranchdata = tree.AsMatrix(["intBranch"]).astype(">i4")
    int8Branchdata = tree.AsMatrix(["int8Branch"]).astype(">i8")
    for i in range(5):
        assert a[i] == intBranchdata[i]
        assert b[i] == int8Branchdata[i]

def test_multi_branch_multi_basket_diff_type(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b1 = newbranch("int32")
    b2 = newbranch("int64")
    branchdict = {"intBranch": b1, "int8Branch": b2}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    b = numpy.array([6, 7, 8, 9, 10], dtype=">i4")
    c = numpy.array([6, 7, 8, 9, 10], dtype=">i8")
    d = numpy.array([1, 2, 3, 4, 5], dtype=">i8")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)
        f["t"]["intBranch"].newbasket(b)
        f["t"]["int8Branch"].newbasket(c)
        f["t"]["int8Branch"].newbasket(d)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    intBranchdata = tree.AsMatrix(["intBranch"]).astype(">i4")
    int8Branchdata = tree.AsMatrix(["int8Branch"]).astype(">i8")
    for i in range(5):
        assert a[i] == intBranchdata[i]
        assert b[i] == intBranchdata[i+5]
        assert c[i] == int8Branchdata[i]
        assert d[i] == int8Branchdata[i+5]

def test_multi_tree_one_branch_multi_basket_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    b = numpy.array([6, 7, 8, 9, 10], dtype=">i4")
    c = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=">i4")
    d = numpy.array([11, 12, 13, 14, 15, 16, 17, 18, 19], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["tree"] = tree
        f["tree"]["intBranch"].newbasket(c)
        f["tree"]["intBranch"].newbasket(d)
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)
        f["t"]["intBranch"].newbasket(b)

    f = uproot.open(filename)
    treedata1 = f["t"].array("intBranch")
    treedata2 = f["tree"].array("intBranch")
    for i in range(5):
        assert a[i] == treedata1[i]
        assert b[i] == treedata1[i+5]
    for i in range(9):
        assert c[i] == treedata2[i]
        assert d[i] == treedata2[i+9]

def test_multi_tree_one_branch_multi_basket(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    b = numpy.array([6, 7, 8, 9, 10], dtype=">i4")
    c = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=">i4")
    d = numpy.array([11, 12, 13, 14, 15, 16, 17, 18, 19], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["tree"] = tree
        f["tree"]["intBranch"].newbasket(c)
        f["tree"]["intBranch"].newbasket(d)
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)
        f["t"]["intBranch"].newbasket(b)

    f = ROOT.TFile.Open(filename)
    t = f.Get("t")
    tree = f.Get("tree")
    treedata1 = t.AsMatrix().astype(">i4")
    treedata2 = tree.AsMatrix().astype(">i4")
    for i in range(5):
        assert a[i] == treedata1[i]
        assert b[i] == treedata1[i+5]
    for i in range(9):
        assert c[i] == treedata2[i]
        assert d[i] == treedata2[i+9]

# Not actually compressed
def test_tree_compression_empty(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i4")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    with uproot.recreate(filename, compression=uproot.ZLIB(4)) as f:
        f["t"] = tree

    f = ROOT.TFile.Open(filename)
    assert f.Get("t").GetBranch("intBranch").GetName() == "intBranch"
    assert f.GetCompressionAlgorithm() == uproot.const.kZLIB
    assert f.GetCompressionLevel() == 4

# Not actually compressed
def test_tree_compression(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i4")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    with uproot.recreate(filename, compression=uproot.ZLIB(4)) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(5):
        assert a[i] == treedata[i]

def test_tree_branch_compression_only(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i4", compression=uproot.ZLIB(4))
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(5):
        assert a[i] == treedata[i]

def test_tree_branch_compression(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i4", compression=uproot.ZLIB(4))
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    with uproot.recreate(filename) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(5):
        assert a[i] == treedata[i]
    branch = tree.GetBranch("intBranch")
    assert branch.GetCompressionAlgorithm() == 1
    assert branch.GetCompressionLevel() == 4

def test_branch_compression_interface1(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i8")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], dtype=">i8")
    with uproot.recreate(filename, compression=uproot.ZLIB(4)) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i8")
    for i in range(15):
        assert a[i] == treedata[i]
    branch = tree.GetBranch("intBranch")
    assert branch.GetCompressionAlgorithm() == 1
    assert branch.GetCompressionLevel() == 4

def test_branch_compression_interface1_diff_type(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i4")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], dtype=">i4")
    with uproot.recreate(filename, compression=uproot.ZLIB(4)) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(15):
        assert a[i] == treedata[i]
    branch = tree.GetBranch("intBranch")
    assert branch.GetCompressionAlgorithm() == 1
    assert branch.GetCompressionLevel() == 4

def test_branch_compression_interface2(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i8", compression=uproot.ZLIB(4))
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], dtype=">i8")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i8")
    for i in range(15):
        assert a[i] == treedata[i]
    branch = tree.GetBranch("intBranch")
    assert branch.GetCompressionAlgorithm() == 1
    assert branch.GetCompressionLevel() == 4

def test_branch_compression_interface3(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i8")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict, compression=uproot.ZLIB(4))
    a = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], dtype=">i8")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i8")
    for i in range(15):
        assert a[i] == treedata[i]
    branch = tree.GetBranch("intBranch")
    assert branch.GetCompressionAlgorithm() == 1
    assert branch.GetCompressionLevel() == 4

def test_many_basket_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i4")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        for i in range(101):
            f["t"]["intBranch"].newbasket(a)

    f = uproot.open(filename)
    tree = f["t"]
    treedata = tree.array("intBranch")
    for i in range(101):
        assert a[0] == treedata[i]

def test_many_basket(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i4")
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        for i in range(101):
            f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(101):
        assert a[0] == treedata[i]

def test_tree_move_compress(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch(">i4", compression=uproot.ZLIB(4))
    branchdict = {"intBranch": b}
    tree = newtree(branchdict)
    a = numpy.array([1], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        for i in range(101):
            f["t"]["intBranch"].newbasket(a)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    treedata = tree.AsMatrix().astype(">i4")
    for i in range(101):
        assert a[0] == treedata[i]
    branch = tree.GetBranch("intBranch")
    assert branch.GetCompressionAlgorithm() == 1
    assert branch.GetCompressionLevel() == 4

def test_tree_renames(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = uproot.newbranch(">i4")
    branchdict = {"intBranch": b}
    tree = uproot.newtree(branchdict)
    a = numpy.array([1], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        for i in range(19):
            f["t"]["intBranch"].newbasket(a)

    f = uproot.open(filename)
    tree = f["t"]
    treedata = tree.array("intBranch")
    for i in range(19):
        assert a[0] == treedata[i]

def test_ttree_extend(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = uproot.newbranch(">i4")
    branchdict = {"intBranch": b, "intBranch2": b}
    tree = uproot.newtree(branchdict)
    with uproot.recreate(filename) as f:
        f["t"] = tree
        basket_add = {"intBranch": numpy.array([1, 2, 3, 4, 5]), "intBranch2": numpy.array([6, 7, 8, 9, 10])}
        f["t"].extend(basket_add)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    branch1 = tree.AsMatrix(["intBranch"])
    branch2 = tree.AsMatrix(["intBranch2"])
    branch1_test = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    branch2_test = numpy.array([6, 7, 8, 9, 10], dtype=">i4")
    for i in range(5):
        assert branch1[i] == branch1_test[i]
        assert branch2[i] == branch2_test[i]

def test_issue340(tmp_path):
    filename = join(str(tmp_path), "example.root")

    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    with uproot.recreate(filename) as f:
        f["t"] = uproot.newtree({"normal": numpy.float64})
        f["t"].extend({"normal": a})

    t = uproot.open(filename)["t"]
    for i in range(10):
        assert t["normal"].basket(0)[i] == a[i]

def test_rdf(tmp_path):
    filename = join(str(tmp_path), "example.root")

    b = newbranch("int32")
    branchdict = {"intBranch": b, "intBranch2": b}
    tree = newtree(branchdict)
    a = numpy.array([1, 2, 3, 4, 5], dtype=">i4")
    b = numpy.array([11, 12, 13, 14, 15], dtype=">i4")
    with uproot.recreate(filename, compression=None) as f:
        f["t"] = tree
        f["t"]["intBranch"].newbasket(a)
        f["t"]["intBranch2"].newbasket(b)

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    rdf = ROOT.RDataFrame(tree)
    for i in range(5):
        assert a[i] == rdf.AsNumpy()["intBranch"][i]
        assert b[i] == rdf.AsNumpy()["intBranch2"][i]

def test_tree_cycle(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename) as f:
        f["t;1"] = uproot.newtree({"branch": "int32"})
        f["t;2"] = uproot.newtree({"branch": "int32"})
        f["t;1"].extend({"branch": numpy.array([1, 2, 3, 4, 5])})
        f["t"].extend({"branch": numpy.array([6, 7, 8, 9, 10])})

    f = ROOT.TFile.Open(filename)
    tree1 = f.Get("t;1")
    branch1 = tree1.AsMatrix(["branch"])
    tree2 = f.Get("t;2")
    branch2 = tree2.AsMatrix(["branch"])
    a = numpy.array([1, 2, 3, 4, 5], dtype="int32")
    b = numpy.array([6, 7, 8, 9, 10], dtype="int32")
    for i in range(5):
        assert branch1[i] == a[i]
        assert branch2[i] == b[i]

def test_large_compress(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, uproot.ZLIB(5)) as f:
        f["a"] = "a" * ((2 ** 24) + 2000)
        f["b"] = "b" * ((2 ** 24) + 10)

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("a")) == "a" * ((2 ** 24) + 2000)
    assert str(f.Get("b")) == "b" * ((2 ** 24) + 10)
    f.Close()

def test_large_compress_uproot(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, uproot.ZLIB(5)) as f:
        f["a"] = "a"*((2**24) + 2000)
        f["b"] = "b"*((2**24) + 10)

    f = uproot.open(filename)
    assert f["a"] == ("a"*((2**24) + 2000)).encode("utf-8")
    assert f["b"] == ("b"*((2**24) + 10)).encode("utf-8")

def test_tree_twodim(tmp_path):
    filename = join(str(tmp_path), "example.root")

    a = numpy.array([[0, 1, 2, 3],
                     [3, 4, 5, 6]])

    with uproot.recreate(filename, compression=None) as f:
        f["t"] = uproot.newtree({"branch": uproot.newbranch(numpy.dtype(">i4"), shape=a.shape)})
        f["t"].extend({"branch": a})

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    rdf = ROOT.RDataFrame(tree).AsNumpy()["branch"]
    for i in range(0, 2):
        for j in range(0, 4):
            assert a[i][j] == rdf[i][j]

def test_tree_threedim(tmp_path):
    filename = join(str(tmp_path), "example.root")

    a = numpy.array([[[0, 1, 2, 3],
                      [3, 4, 5, 6],
                      [90, 91, 91, 92]],
                     [[10, 11, 12, 13],
                      [13, 14, 15, 16],
                      [190, 191, 191, 192]]])

    with uproot.recreate(filename, compression=None) as f:
        f["t"] = uproot.newtree({"branch": uproot.newbranch(numpy.dtype(">i4"), shape=a.shape)})
        f["t"].extend({"branch": a})

    f = ROOT.TFile.Open(filename)
    tree = f.Get("t")
    rdf = ROOT.RDataFrame(tree).AsNumpy()["branch"]
    for i in range(2):
        test = numpy.array(rdf[i]).reshape(3, 4)
        for j in range(3):
            for k in range(4):
                assert a[i][j][k] == test[j][k]
