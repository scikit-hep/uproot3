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

from collections import namedtuple
import unittest

import numpy

import uproot

class TestIssues(unittest.TestCase):
    def runTest(self):
        pass

    def test_issue21(self):
        t = uproot.open("tests/samples/issue21.root")["nllscan"]

        ### Explicit recover removed
        # self.assertEqual(t.array("mH").tolist(), [])
        # t.recover()

        self.assertEqual(t.array("mH").tolist(), [124.0, 124.09089660644531, 124.18180084228516, 124.27269744873047, 124.36360168457031, 124.45449829101562, 124.54550170898438, 124.63639831542969, 124.72730255126953, 124.81819915771484, 124.87000274658203, 124.87550354003906, 124.88089752197266, 124.88639831542969, 124.89179992675781, 124.89730072021484, 124.90270233154297, 124.908203125, 124.90910339355469, 124.9135971069336, 124.91909790039062, 124.92449951171875, 124.93000030517578, 124.98739624023438, 124.9906997680664, 124.99349975585938, 124.99590301513672, 124.9977035522461, 124.9990005493164, 124.99970245361328, 125.0, 125.00029754638672, 125.0009994506836, 125.0022964477539, 125.00409698486328, 125.00650024414062, 125.0093002319336, 125.01260375976562, 125.06999969482422, 125.07550048828125, 125.08090209960938, 125.0864028930664, 125.09089660644531, 125.091796875, 125.09729766845703, 125.10269927978516, 125.10820007324219, 125.11360168457031, 125.11910247802734, 125.12449645996094, 125.12999725341797, 125.18180084228516, 125.27269744873047, 125.36360168457031, 125.45449829101562, 125.54550170898438, 125.63639831542969, 125.72730255126953, 125.81819915771484, 125.90910339355469, 126.0])

    def test_issue30(self):
        uproot.open("tests/samples/issue30.root")

    def test_issue31(self):
        t = uproot.open("tests/samples/issue31.root")["T"]
        self.assertEqual(t.array("name").tolist(), [b"one", b"two", b"three", b"four", b"five"])

    def test_issue33(self):
        h = uproot.open("tests/samples/issue33.root")["cutflow"]
        self.assertEqual(h.xlabels, ["Dijet", "MET", "MuonVeto", "IsoMuonTrackVeto", "ElectronVeto", "IsoElectronTrackVeto", "IsoPionTrackVeto"])

    def test_issue38(self):
        before_hadd = uproot.open("tests/samples/issue38a.root")["ntupler/tree"]
        after_hadd  = uproot.open("tests/samples/issue38b.root")["ntupler/tree"]

        before = before_hadd.arrays()
        after = after_hadd.arrays()

        self.assertEqual(set(before.keys()), set([b"v_int16", b"v_int32", b"v_int64", b"v_uint16", b"v_uint32", b"v_uint64", b"v_bool", b"v_float", b"v_double"]))
        self.assertEqual(set(after.keys()),  set([b"v_int16", b"v_int32", b"v_int64", b"v_uint16", b"v_uint32", b"v_uint64", b"v_bool", b"v_float", b"v_double"]))

        for key in before.keys():
            self.assertEqual(before[key].tolist() * 3, after[key].tolist())

    def test_issue46(self):
        t = uproot.open("tests/samples/issue46.root")["tree"]
        t["evt"].array(uproot.interp.asdebug)

    def test_issue49(self):
        t = uproot.open("tests/samples/issue49.root")["nllscan"]
        t.arrays()

    def test_issue54(self):
        h = uproot.open("tests/samples/hepdata-example.root")["hpx"]
        self.assertTrue(h.fFunctions[0].fParent is h)

    def test_issue55(self):
        withoffsets = uproot.open("tests/samples/small-dy-withoffsets.root")["tree"]
        nooffsets = uproot.open("tests/samples/small-dy-nooffsets.root")["tree"]
        self.assertTrue(numpy.array_equal(withoffsets.array("nJet"), nooffsets.array("nJet")))
        self.assertTrue(numpy.array_equal(withoffsets.array("nMuon"), nooffsets.array("nMuon")))
        self.assertTrue(numpy.array_equal(withoffsets.array("Jet_jetId"), nooffsets.array("Jet_jetId")))
        self.assertTrue(numpy.array_equal(withoffsets.array("Jet_pt"), nooffsets.array("Jet_pt")))
        self.assertTrue(numpy.array_equal(withoffsets.array("MET_pt"), nooffsets.array("MET_pt")))
        self.assertTrue(numpy.array_equal(withoffsets.array("Muon_charge"), nooffsets.array("Muon_charge")))
        self.assertTrue(numpy.array_equal(withoffsets.array("Muon_pt"), nooffsets.array("Muon_pt")))
        self.assertTrue(numpy.array_equal(withoffsets.array("event"), nooffsets.array("event")))

    def test_issue57(self):
        tree = uproot.open("tests/samples/issue57.root")["outtree"]
        self.assertTrue(all(isinstance(y, uproot.physics.TLorentzVectorMethods) and isinstance(y.fP, uproot.physics.TVector3Methods) for x in tree["sel_lep"].array() for y in x))
        self.assertTrue(all(isinstance(y, uproot.physics.TLorentzVectorMethods) and isinstance(y.fP, uproot.physics.TVector3Methods) for x in tree["selJet"].array() for y in x))
