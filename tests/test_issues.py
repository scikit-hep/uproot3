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

import uproot_methods.classes.TVector3
import uproot_methods.classes.TLorentzVector

class Test(unittest.TestCase):
    def runTest(self):
        pass

    def test_issue21(self):
        t = uproot.open("tests/samples/issue21.root")["nllscan"]

        ### Explicit recover removed
        # self.assertEqual(t.array("mH").tolist(), [])
        # t.recover()

        self.assertEqual(t["mH"].numbaskets, 1)
        self.assertEqual(t["mH"].basket_entrystart(0), 0)
        self.assertEqual(t["mH"].basket_entrystop(0), 61)
        self.assertEqual(t["mH"].basket_numentries(0), 61)
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
        t["evt"].array(uproot.asdebug)

    def test_issue49(self):
        t = uproot.open("tests/samples/issue49.root")["nllscan"]
        t.arrays()

    def test_issue54(self):
        h = uproot.open("tests/samples/hepdata-example.root")["hpx"]
        self.assertTrue(h._fFunctions[0]._fParent is h)

    def test_issue55(self):
        withoffsets = uproot.open("tests/samples/small-dy-withoffsets.root")["tree"]
        nooffsets = uproot.open("tests/samples/small-dy-nooffsets.root")["tree"]
        self.assertTrue(numpy.array_equal(withoffsets.array("nJet"), nooffsets.array("nJet")))
        self.assertTrue(numpy.array_equal(withoffsets.array("nMuon"), nooffsets.array("nMuon")))

        def equal(left, right):
            if len(left) != len(right):
                return False
            for x, y in zip(left, right):
                if not numpy.array_equal(x, y):
                    return False
            return True

        self.assertTrue(equal(withoffsets.array("Jet_jetId"), nooffsets.array("Jet_jetId")))
        self.assertTrue(equal(withoffsets.array("Jet_pt"), nooffsets.array("Jet_pt")))
        self.assertTrue(equal(withoffsets.array("MET_pt"), nooffsets.array("MET_pt")))
        self.assertTrue(equal(withoffsets.array("Muon_charge"), nooffsets.array("Muon_charge")))
        self.assertTrue(equal(withoffsets.array("Muon_pt"), nooffsets.array("Muon_pt")))
        self.assertTrue(equal(withoffsets.array("event"), nooffsets.array("event")))

    def test_issue57(self):
        tree = uproot.open("tests/samples/issue57.root")["outtree"]
        self.assertTrue(all(isinstance(y, uproot_methods.classes.TLorentzVector.Methods) and isinstance(y._fP, uproot_methods.classes.TVector3.Methods) for x in tree["sel_lep"].array() for y in x))
        self.assertTrue(all(isinstance(y, uproot_methods.classes.TLorentzVector.Methods) and isinstance(y._fP, uproot_methods.classes.TVector3.Methods) for x in tree["selJet"].array() for y in x))

    def test_issue60(self):
        t = uproot.open("tests/samples/issue60.root")["nllscan"]

        self.assertEqual(t["status"].numbaskets, 2)
        self.assertEqual(t["mH"].numbaskets, 3)
        self.assertEqual((t["mH"].basket_entrystart(0), t["mH"].basket_entrystart(1), t["mH"].basket_entrystart(2)), (0, 3990, 7980))
        self.assertEqual((t["mH"].basket_entrystop(0), t["mH"].basket_entrystop(1), t["mH"].basket_entrystop(2)), (3990, 7980, 11535))
        self.assertEqual((t["mH"].basket_numentries(0), t["mH"].basket_numentries(1), t["mH"].basket_numentries(2)), (3990, 3990, 3555))
        self.assertEqual(t.array("mH")[:10].tolist(), [125.3575896071691, 124.75819175713684, 124.79865223661515, 125.13239376420276, 125.19612659731995, 125.33001837818416, 124.93261741760551, 125.02903289132837, 124.65206649938854, 125.50663519903532])
        self.assertEqual(t.array("mH")[-10:].tolist(), [125.5150930345707, 125.00248572708085, 124.55838505657864, 125.03766816520313, 125.27765299737514, 124.9976442776121, 124.8339210081154, 124.62415638855144, 125.33988981473144, 124.93384515492096])

    def test_issue63(self):
        t = uproot.open("tests/samples/issue63.root")["WtLoop_meta"]
        self.assertEqual(t["initialState"].array().tolist(), [b"Wt"])
        self.assertEqual(t["generator"].array().tolist(), [b"PowhegPythia6"])
        self.assertEqual(t["sampleType"].array().tolist(), [b"Nominal"])
        self.assertEqual(t["campaign"].array().tolist(), [b"MC16a"])

    def test_issue64(self):
        t = uproot.open("tests/samples/issue64.root")["events/events"]
        self.assertEqual(t["e_pri"].array().tolist(), [0.00698000006377697] * 500)

    def test_issue66(self):
        f = uproot.open("tests/samples/issue66.root")
        h, = f.values()
        self.assertEqual(h.values, [4814.0, 45.0, 45.0, 25.0, 15.0, 4.0, 0.0, 6.0, 7.0, 5.0, 3.0, 3.0, 6.0, 3.0, 7.0, 5.0, 7.0, 11.0, 9.0, 5.0, 4.0, 10.0, 12.0, 7.0, 10.0, 8.0, 12.0, 11.0, 12.0, 12.0, 14.0, 15.0, 13.0, 14.0, 14.0, 20.0, 20.0, 16.0, 21.0, 22.0, 22.0, 28.0, 25.0, 33.0, 26.0, 21.0, 42.0, 36.0, 43.0, 42.0, 43.0, 39.0, 42.0, 56.0, 67.0, 50.0, 67.0, 71.0, 59.0, 76.0, 73.0, 84.0, 63.0, 76.0, 84.0, 97.0, 91.0, 100.0, 108.0, 121.0, 129.0, 137.0, 127.0, 141.0, 152.0, 147.0, 166.0, 158.0, 166.0, 159.0, 146.0, 176.0, 189.0, 213.0, 212.0, 228.0, 193.0, 232.0, 225.0, 210.0, 211.0, 229.0, 226.0, 237.0, 246.0, 243.0, 265.0, 303.0, 248.0, 302.0, 326.0, 318.0, 340.0, 362.0, 313.0, 366.0, 379.0, 376.0, 423.0, 433.0, 486.0, 486.0, 482.0, 518.0, 548.0, 583.0, 628.0, 705.0, 735.0, 814.0, 852.0, 920.0, 1000.0, 1095.0, 1184.0, 1296.0, 1544.0, 1700.0, 2091.0, 2738.0, 3794.0, 5591.0, 8640.0, 13619.0, 20171.0, 11051.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_issue70(self):
        f = uproot.open("tests/samples/issue70.root")
        self.assertEqual(f.keys(), [])

    def test_issue74(self):
        t = uproot.open("tests/samples/issue74.root")["Events"]
        self.assertTrue(all(isinstance(x[0], uproot_methods.classes.TVector3.Methods) for x in t.array("bees.xyzPosition")))
        self.assertEqual(t.array("bees.xyzPosition")[0][0], uproot_methods.classes.TVector3.TVector3(1.0, 2.0, -1.0))

    def test_issue76(self):
        t = uproot.open("tests/samples/issue76.root")["Events"]
        self.assertEqual(list(t.array("rootStrings")[0]), [b"2", b"4"])
        x, y = t.array("rootStrings")[0]
        self.assertTrue(isinstance(x, uproot.rootio.TString))

    def test_issue79(self):
        t = uproot.open("tests/samples/issue79.root")["taus"]
        self.assertEqual(t["pt"].numbaskets, 2)
        baskets = numpy.concatenate([t["pt"].basket(0), t["pt"].basket(1)])
        self.assertEqual(baskets.shape, (t["pt"].numentries,))
        self.assertTrue(numpy.array_equal(baskets, t["pt"].array()))
    
    def test_issue96(self):
        t = uproot.open("tests/samples/issue96.root")["tree"]
        self.assertTrue(all(isinstance(x, uproot_methods.classes.TLorentzVector.Methods) for x in t.array("jet1P4")))
