#!/usr/bin/env python

# Copyright (c) 2019, IRIS-HEP
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
