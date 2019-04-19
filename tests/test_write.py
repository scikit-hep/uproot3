#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from os.path import join

import pytest
import uproot

ROOT = pytest.importorskip("ROOT")

def test_strings(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=0, compressionLevel=0) as f:
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("hello")) == "world"
    f.Close()

def test_cycle(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=0, compressionLevel=0) as f:
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
    h.Write()
    f.Close()

    t = uproot.open(testfile)
    hist = t["hvar"]
    with uproot.recreate(filename, compressionAlgorithm=0, compressionLevel=0) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetBinWidth(1) == 2.0
    assert h.GetBinWidth(2) == 1.0
    assert h.GetBinWidth(3) == 6.0
    assert h.GetBinWidth(4) == 1.0
    assert h.GetBinWidth(5) == 1.0

def test_zlib(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=uproot.const.kZLIB, compressionLevel=1) as f:
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    assert (f.GetCompressionAlgorithm()) == uproot.const.kZLIB
    assert (f.GetCompressionLevel()) == 1
    assert str(f.Get("hello")) == "world"
    f.Close()

def test_compresschange(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=uproot.const.kLZMA, compressionLevel=2) as f:
        f.updateCompression(compressionAlgorithm=uproot.const.kZLIB, compressionLevel=3)
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    assert (f.GetCompressionAlgorithm()) == uproot.const.kZLIB
    assert (f.GetCompressionLevel()) == 3

def test_nocompress(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=0, compressionLevel=1) as f:
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    # GetCompressionFactor() returns >1 (1.000047206878662) even while not compressed
    assert (f.GetCompressionAlgorithm()) == 0
    assert str(f.Get("hello")) == "world"
    f.Close()

def test_lzma(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=uproot.const.kLZMA, compressionLevel=1) as f:
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    assert (f.GetCompressionAlgorithm()) == uproot.const.kLZMA
    assert (f.GetCompressionLevel()) == 1
    assert str(f.Get("hello")) == "world"
    f.Close()

def test_lz4_leveldown(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=uproot.const.kLZ4, compressionLevel=1) as f:
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    assert (f.GetCompressionAlgorithm()) == uproot.const.kLZ4
    assert str(f.Get("hello")) == "world"
    f.Close()

def test_lz4_levelup(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=uproot.const.kLZ4, compressionLevel=5) as f:
        f["hello"] = "world"

    f = ROOT.TFile.Open(filename)
    assert (f.GetCompressionAlgorithm()) == uproot.const.kLZ4
    assert (f.GetCompressionLevel()) == 5
    assert str(f.Get("hello")) == "world"
    f.Close()

def test_compressed_TObjString(tmp_path):
    filename = join(str(tmp_path), "example.root")

    with uproot.recreate(filename, compressionAlgorithm=uproot.const.kZLIB, compressionLevel=1) as f:
        f["hello"] = "a"*2000

    f = ROOT.TFile.Open(filename)
    assert str(f.Get("hello")) == "a"*2000
    f.Close()

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
    with uproot.recreate(filename, compressionAlgorithm=uproot.const.kZLIB, compressionLevel=1) as f:
        f["test"] = hist

    f = ROOT.TFile.Open(filename)
    h = f.Get("test")
    assert h.GetNbinsX() == 5
    assert h.GetBinWidth(1) == 2.0
    assert h.GetBinWidth(2) == 1.0
    assert h.GetBinWidth(3) == 6.0
    assert h.GetBinWidth(4) == 1.0
    assert h.GetBinWidth(5) == 1.0
