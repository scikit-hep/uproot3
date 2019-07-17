#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from os.path import join

import pytest
import uproot

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
