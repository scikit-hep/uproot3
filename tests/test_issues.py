#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import unittest

from collections import namedtuple

import pytest
import numpy

import uproot

import uproot_methods.classes.TVector3
import uproot_methods.classes.TLorentzVector

class Test(unittest.TestCase):
    def test_issue21(self):
        t = uproot.open("tests/samples/issue21.root")["nllscan"]

        ### Explicit recover removed
        # assert t.array("mH").tolist() == []
        # t.recover()

        assert t["mH"].numbaskets == 1
        assert t["mH"].basket_entrystart(0) == 0
        assert t["mH"].basket_entrystop(0) == 61
        assert t["mH"].basket_numentries(0) == 61
        assert t.array("mH").tolist() == [124.0, 124.09089660644531, 124.18180084228516, 124.27269744873047, 124.36360168457031, 124.45449829101562, 124.54550170898438, 124.63639831542969, 124.72730255126953, 124.81819915771484, 124.87000274658203, 124.87550354003906, 124.88089752197266, 124.88639831542969, 124.89179992675781, 124.89730072021484, 124.90270233154297, 124.908203125, 124.90910339355469, 124.9135971069336, 124.91909790039062, 124.92449951171875, 124.93000030517578, 124.98739624023438, 124.9906997680664, 124.99349975585938, 124.99590301513672, 124.9977035522461, 124.9990005493164, 124.99970245361328, 125.0, 125.00029754638672, 125.0009994506836, 125.0022964477539, 125.00409698486328, 125.00650024414062, 125.0093002319336, 125.01260375976562, 125.06999969482422, 125.07550048828125, 125.08090209960938, 125.0864028930664, 125.09089660644531, 125.091796875, 125.09729766845703, 125.10269927978516, 125.10820007324219, 125.11360168457031, 125.11910247802734, 125.12449645996094, 125.12999725341797, 125.18180084228516, 125.27269744873047, 125.36360168457031, 125.45449829101562, 125.54550170898438, 125.63639831542969, 125.72730255126953, 125.81819915771484, 125.90910339355469, 126.0]

    def test_issue30(self):
        uproot.open("tests/samples/issue30.root")

    def test_issue31(self):
        t = uproot.open("tests/samples/issue31.root")["T"]
        assert t.array("name").tolist() == [b"one", b"two", b"three", b"four", b"five"]

    def test_issue33(self):
        h = uproot.open("tests/samples/issue33.root")["cutflow"]
        assert h.xlabels == ["Dijet", "MET", "MuonVeto", "IsoMuonTrackVeto", "ElectronVeto", "IsoElectronTrackVeto", "IsoPionTrackVeto"]

    def test_issue38(self):
        before_hadd = uproot.open("tests/samples/issue38a.root")["ntupler/tree"]
        after_hadd  = uproot.open("tests/samples/issue38b.root")["ntupler/tree"]

        before = before_hadd.arrays()
        after = after_hadd.arrays()

        assert set(before.keys()), se == ([b"v_int16", b"v_int32", b"v_int64", b"v_uint16", b"v_uint32", b"v_uint64", b"v_bool", b"v_float", b"v_double"])
        assert set(after.keys()),  se == ([b"v_int16", b"v_int32", b"v_int64", b"v_uint16", b"v_uint32", b"v_uint64", b"v_bool", b"v_float", b"v_double"])

        for key in before.keys():
            assert before[key].tolist() * 3 == after[key].tolist()

    def test_issue46(self):
        t = uproot.open("tests/samples/issue46.root")["tree"]
        t["evt"].array(uproot.asdebug)

    def test_issue49(self):
        t = uproot.open("tests/samples/issue49.root")["nllscan"]
        t.arrays()

    def test_issue54(self):
        h = uproot.open("tests/samples/hepdata-example.root")["hpx"]
        assert h._fFunctions[0]._fParent is h

    def test_issue55(self):
        withoffsets = uproot.open("tests/samples/small-dy-withoffsets.root")["tree"]
        nooffsets = uproot.open("tests/samples/small-dy-nooffsets.root")["tree"]
        assert numpy.array_equal(withoffsets.array("nJet"), nooffsets.array("nJet"))
        assert numpy.array_equal(withoffsets.array("nMuon"), nooffsets.array("nMuon"))

        def equal(left, right):
            if len(left) != len(right):
                return False
            for x, y in zip(left, right):
                if not numpy.array_equal(x, y):
                    return False
            return True

        assert equal(withoffsets.array("Jet_jetId"), nooffsets.array("Jet_jetId"))
        assert equal(withoffsets.array("Jet_pt"), nooffsets.array("Jet_pt"))
        assert equal(withoffsets.array("MET_pt"), nooffsets.array("MET_pt"))
        assert equal(withoffsets.array("Muon_charge"), nooffsets.array("Muon_charge"))
        assert equal(withoffsets.array("Muon_pt"), nooffsets.array("Muon_pt"))
        assert equal(withoffsets.array("event"), nooffsets.array("event"))

    def test_issue57(self):
        tree = uproot.open("tests/samples/issue57.root")["outtree"]
        assert all(isinstance(y, uproot_methods.classes.TLorentzVector.Methods) and isinstance(y._fP, uproot_methods.classes.TVector3.Methods) for x in tree["sel_lep"].array() for y in x)
        assert all(isinstance(y, uproot_methods.classes.TLorentzVector.Methods) and isinstance(y._fP, uproot_methods.classes.TVector3.Methods) for x in tree["selJet"].array() for y in x)

    def test_issue60(self):
        t = uproot.open("tests/samples/issue60.root")["nllscan"]

        assert t["status"].numbaskets == 2
        assert t["mH"].numbaskets == 3
        assert (t["mH"].basket_entrystart(0), t["mH"].basket_entrystart(1), t["mH"].basket_entrystart(2)) == (0, 3990, 7980)
        assert (t["mH"].basket_entrystop(0), t["mH"].basket_entrystop(1), t["mH"].basket_entrystop(2)) == (3990, 7980, 11535)
        assert (t["mH"].basket_numentries(0), t["mH"].basket_numentries(1), t["mH"].basket_numentries(2)) == (3990, 3990, 3555)
        assert t.array("mH")[:10].tolist() == [125.3575896071691, 124.75819175713684, 124.79865223661515, 125.13239376420276, 125.19612659731995, 125.33001837818416, 124.93261741760551, 125.02903289132837, 124.65206649938854, 125.50663519903532]
        assert t.array("mH")[-10:].tolist() == [125.5150930345707, 125.00248572708085, 124.55838505657864, 125.03766816520313, 125.27765299737514, 124.9976442776121, 124.8339210081154, 124.62415638855144, 125.33988981473144, 124.93384515492096]

    def test_issue63(self):
        t = uproot.open("tests/samples/issue63.root")["WtLoop_meta"]
        assert t["initialState"].array().tolist() == [b"Wt"]
        assert t["generator"].array().tolist() == [b"PowhegPythia6"]
        assert t["sampleType"].array().tolist() == [b"Nominal"]
        assert t["campaign"].array().tolist() == [b"MC16a"]

    def test_issue64(self):
        t = uproot.open("tests/samples/issue64.root")["events/events"]
        assert t["e_pri"].array().tolist() == [0.00698000006377697] * 500

    def test_issue66(self):
        f = uproot.open("tests/samples/issue66.root")
        h, = f.values()
        assert h.values.tolist() == [4814.0, 45.0, 45.0, 25.0, 15.0, 4.0, 0.0, 6.0, 7.0, 5.0, 3.0, 3.0, 6.0, 3.0, 7.0, 5.0, 7.0, 11.0, 9.0, 5.0, 4.0, 10.0, 12.0, 7.0, 10.0, 8.0, 12.0, 11.0, 12.0, 12.0, 14.0, 15.0, 13.0, 14.0, 14.0, 20.0, 20.0, 16.0, 21.0, 22.0, 22.0, 28.0, 25.0, 33.0, 26.0, 21.0, 42.0, 36.0, 43.0, 42.0, 43.0, 39.0, 42.0, 56.0, 67.0, 50.0, 67.0, 71.0, 59.0, 76.0, 73.0, 84.0, 63.0, 76.0, 84.0, 97.0, 91.0, 100.0, 108.0, 121.0, 129.0, 137.0, 127.0, 141.0, 152.0, 147.0, 166.0, 158.0, 166.0, 159.0, 146.0, 176.0, 189.0, 213.0, 212.0, 228.0, 193.0, 232.0, 225.0, 210.0, 211.0, 229.0, 226.0, 237.0, 246.0, 243.0, 265.0, 303.0, 248.0, 302.0, 326.0, 318.0, 340.0, 362.0, 313.0, 366.0, 379.0, 376.0, 423.0, 433.0, 486.0, 486.0, 482.0, 518.0, 548.0, 583.0, 628.0, 705.0, 735.0, 814.0, 852.0, 920.0, 1000.0, 1095.0, 1184.0, 1296.0, 1544.0, 1700.0, 2091.0, 2738.0, 3794.0, 5591.0, 8640.0, 13619.0, 20171.0, 11051.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def test_issue70(self):
        f = uproot.open("tests/samples/issue70.root")
        assert f.keys() == []

    def test_issue74(self):
        t = uproot.open("tests/samples/issue74.root")["Events"]
        assert all(isinstance(x[0], uproot_methods.classes.TVector3.Methods) for x in t.array("bees.xyzPosition"))
        assert t.array("bees.xyzPosition")[0][0] == uproot_methods.classes.TVector3.TVector3(1.0, 2.0, -1.0)

    def test_issue76(self):
        t = uproot.open("tests/samples/issue76.root")["Events"]
        assert list(t.array("rootStrings")[0]) == [b"2", b"4"]
        x, y = t.array("rootStrings")[0]
        assert isinstance(x, uproot.rootio.TString)

    def test_issue79(self):
        t = uproot.open("tests/samples/issue79.root")["taus"]
        assert t["pt"].numbaskets == 2
        baskets = numpy.concatenate([t["pt"].basket(0), t["pt"].basket(1)])
        assert baskets.shape == (t["pt"].numentries,)
        assert numpy.array_equal(baskets, t["pt"].array())

    def test_issue96(self):
        t = uproot.open("tests/samples/issue96.root")["tree"]
        assert all(isinstance(x, uproot_methods.classes.TLorentzVector.Methods) for x in t.array("jet1P4"))

    def test_geant4(self):
        f = uproot.open("tests/samples/from-geant4.root")
        arrays = f["Details"].arrays()
        assert arrays[b"numgood"][0] == 224
        assert [len(x) for x in f["HitStrips"].arrays().values()] == [4808, 4808, 4808]
        assert sum(f["edep_inner"].values) == 1547
        assert sum(sum(x) for x in f["recon_orig"].values) == 141

    ### file is too big to include
    # def test_issue168(self):
    #     t = uproot.open("tests/samples/issue168.root")["Events"]
    #     a1 = t["MRawEvtData.fHiGainFadcSamples"].array(t["MRawEvtData.fHiGainFadcSamples"].interpretation.speedbump(False), entrystop=4)
    #     assert a1[0]._fArray.shape == (108400,)
    #     a2 = t["MRawEvtData.fHiGainPixId"].array(t["MRawEvtData.fHiGainPixId"].interpretation.speedbump(False))
    #     assert a2[0]._fArray.shape == (1084,)

    def test_issue187(self):
        t = uproot.open("tests/samples/issue187.root")["fTreeV0"]
        assert (t.array("fMultiplicity") == -1).all()
        assert t.array("V0s.fEtaPos")[-3].tolist() == [-0.390625, 0.046875]

    def test_issue213(self):
        t = uproot.open("tests/samples/issue213.root")["T"]
        assert t["fMCHits.fPosition"].array().x.tolist() == [[], [], [], [], [], [], [], [42.17024612426758, 50.63192367553711], [], [], [], [43.292755126953125], [], [], [], [], [], [], [], [], [42.15415954589844], [41.60139083862305], [42.95103454589844], [], [41.55511474609375], [], [], [], [], [], [], [42.549156188964844], [], [], [], [42.80044174194336, 46.136253356933594], [], [], [], [], [41.58171081542969], [], [], [42.741485595703125], [41.228477478027344], [], [], [], [], [], [], [], [], [], [42.518882751464844], [43.34626388549805], [], [], [43.214759826660156], [], [], [], [], [], [], [42.78463363647461], [], [], [], [], [], [], [], [41.927093505859375], [42.65863037109375], [], [42.66266632080078], [], [], [], [], [], [], [], [], [], [], [41.91042709350586, 41.807674407958984], [], [42.79293441772461], [], [], [], [], [], [], [41.72440719604492], [], [], [41.609615325927734]]

    def test_issue232(self):
        try:
            import pandas
        except ImportError:
            pass
        else:
            t = uproot.open("tests/samples/issue232.root")["fTreeV0"]
            t.pandas.df(["V0Hyper.fNsigmaHe3Pos", "V0Hyper.fDcaPos2PrimaryVertex"], flatten=True)

    @pytest.mark.skip(reason="This one takes way too long (eospublic?).")
    def test_issue240(self):
        try:
            import pyxrootd
        except ImportError:
            pytest.skip("unable to import pyxrootd")
        else:
            t = uproot.open("root://eospublic.cern.ch//eos/root-eos/cms_opendata_2012_nanoaod/Run2012B_DoubleMuParked.root")["Events"]
            assert (abs(t.array("nMuon")) < 50).all()

    def test_issue243(self):
        t = uproot.open("tests/samples/issue243.root")["triggerList"]
        for x in t.array("triggerMap", entrystop=100):
            assert all(y == 1.0 for y in x.values())
