#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import sys

import pytest
import numpy

import uproot
import awkward

import uproot_methods.classes.TVector3
import uproot_methods.classes.TLorentzVector


class Test(object):
    def test_issue21(self):
        t = uproot.open("tests/samples/issue21.root")["nllscan"]

        ### Explicit recover removed
        # assert t.array("mH").tolist() == []
        # t.recover()

        assert t["mH"].numbaskets == 1
        assert t["mH"].basket_entrystart(0) == 0
        assert t["mH"].basket_entrystop(0) == 61
        assert t["mH"].basket_numentries(0) == 61
        assert t.array("mH").tolist() == [
            124.0, 124.09089660644531, 124.18180084228516, 124.27269744873047,
            124.36360168457031, 124.45449829101562, 124.54550170898438,
            124.63639831542969, 124.72730255126953, 124.81819915771484,
            124.87000274658203, 124.87550354003906, 124.88089752197266,
            124.88639831542969, 124.89179992675781, 124.89730072021484,
            124.90270233154297, 124.908203125, 124.90910339355469,
            124.9135971069336, 124.91909790039062, 124.92449951171875,
            124.93000030517578, 124.98739624023438, 124.9906997680664,
            124.99349975585938, 124.99590301513672, 124.9977035522461,
            124.9990005493164, 124.99970245361328, 125.0, 125.00029754638672,
            125.0009994506836, 125.0022964477539, 125.00409698486328,
            125.00650024414062, 125.0093002319336, 125.01260375976562,
            125.06999969482422, 125.07550048828125, 125.08090209960938,
            125.0864028930664, 125.09089660644531, 125.091796875,
            125.09729766845703, 125.10269927978516, 125.10820007324219,
            125.11360168457031, 125.11910247802734, 125.12449645996094,
            125.12999725341797, 125.18180084228516, 125.27269744873047,
            125.36360168457031, 125.45449829101562, 125.54550170898438,
            125.63639831542969, 125.72730255126953, 125.81819915771484,
            125.90910339355469, 126.0
        ]

    def test_issue30(self):
        uproot.open("tests/samples/issue30.root")

    def test_issue31(self):
        t = uproot.open("tests/samples/issue31.root")["T"]
        assert t.array("name").tolist() == [
            b"one", b"two", b"three", b"four", b"five"
        ]

    def test_issue33(self):
        h = uproot.open("tests/samples/issue33.root")["cutflow"]
        assert h.xlabels == [
            "Dijet", "MET", "MuonVeto", "IsoMuonTrackVeto", "ElectronVeto",
            "IsoElectronTrackVeto", "IsoPionTrackVeto"
        ]

    def test_issue38(self):
        before_hadd = uproot.open(
            "tests/samples/issue38a.root")["ntupler/tree"]
        after_hadd = uproot.open("tests/samples/issue38b.root")["ntupler/tree"]

        before = before_hadd.arrays()
        after = after_hadd.arrays()

        assert set(before.keys())
        assert set(after.keys())

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
        withoffsets = uproot.open(
            "tests/samples/small-dy-withoffsets.root")["tree"]
        nooffsets = uproot.open(
            "tests/samples/small-dy-nooffsets.root")["tree"]
        assert numpy.array_equal(withoffsets.array("nJet"),
                                 nooffsets.array("nJet"))
        assert numpy.array_equal(withoffsets.array("nMuon"),
                                 nooffsets.array("nMuon"))

        def equal(left, right):
            if len(left) != len(right):
                return False
            for x, y in zip(left, right):
                if not numpy.array_equal(x, y):
                    return False
            return True

        assert equal(withoffsets.array("Jet_jetId"),
                     nooffsets.array("Jet_jetId"))
        assert equal(withoffsets.array("Jet_pt"), nooffsets.array("Jet_pt"))
        assert equal(withoffsets.array("MET_pt"), nooffsets.array("MET_pt"))
        assert equal(withoffsets.array("Muon_charge"),
                     nooffsets.array("Muon_charge"))
        assert equal(withoffsets.array("Muon_pt"), nooffsets.array("Muon_pt"))
        assert equal(withoffsets.array("event"), nooffsets.array("event"))

    def test_issue57(self):
        tree = uproot.open("tests/samples/issue57.root")["outtree"]
        for x in tree["sel_lep"].array():
            for y in x:
                assert isinstance(
                    y, uproot_methods.classes.TLorentzVector.
                    Methods) and isinstance(
                        y._fP, uproot_methods.classes.TVector3.Methods)
        for x in tree["selJet"].array():
            for y in x:
                assert isinstance(
                    y, uproot_methods.classes.TLorentzVector.
                    Methods) and isinstance(
                        y._fP, uproot_methods.classes.TVector3.Methods)

    def test_issue60(self):
        t = uproot.open("tests/samples/issue60.root")["nllscan"]

        assert t["status"].numbaskets == 2
        assert t["mH"].numbaskets == 3
        assert (t["mH"].basket_entrystart(0), t["mH"].basket_entrystart(1),
                t["mH"].basket_entrystart(2)) == (0, 3990, 7980)
        assert (t["mH"].basket_entrystop(0), t["mH"].basket_entrystop(1),
                t["mH"].basket_entrystop(2)) == (3990, 7980, 11535)
        assert (t["mH"].basket_numentries(0), t["mH"].basket_numentries(1),
                t["mH"].basket_numentries(2)) == (3990, 3990, 3555)
        assert t.array("mH")[:10].tolist() == [
            125.3575896071691, 124.75819175713684, 124.79865223661515,
            125.13239376420276, 125.19612659731995, 125.33001837818416,
            124.93261741760551, 125.02903289132837, 124.65206649938854,
            125.50663519903532
        ]
        assert t.array("mH")[-10:].tolist() == [
            125.5150930345707, 125.00248572708085, 124.55838505657864,
            125.03766816520313, 125.27765299737514, 124.9976442776121,
            124.8339210081154, 124.62415638855144, 125.33988981473144,
            124.93384515492096
        ]

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
        assert h.values.tolist() == [
            4814.0, 45.0, 45.0, 25.0, 15.0, 4.0, 0.0, 6.0, 7.0, 5.0, 3.0, 3.0,
            6.0, 3.0, 7.0, 5.0, 7.0, 11.0, 9.0, 5.0, 4.0, 10.0, 12.0, 7.0,
            10.0, 8.0, 12.0, 11.0, 12.0, 12.0, 14.0, 15.0, 13.0, 14.0, 14.0,
            20.0, 20.0, 16.0, 21.0, 22.0, 22.0, 28.0, 25.0, 33.0, 26.0, 21.0,
            42.0, 36.0, 43.0, 42.0, 43.0, 39.0, 42.0, 56.0, 67.0, 50.0, 67.0,
            71.0, 59.0, 76.0, 73.0, 84.0, 63.0, 76.0, 84.0, 97.0, 91.0, 100.0,
            108.0, 121.0, 129.0, 137.0, 127.0, 141.0, 152.0, 147.0, 166.0,
            158.0, 166.0, 159.0, 146.0, 176.0, 189.0, 213.0, 212.0, 228.0,
            193.0, 232.0, 225.0, 210.0, 211.0, 229.0, 226.0, 237.0, 246.0,
            243.0, 265.0, 303.0, 248.0, 302.0, 326.0, 318.0, 340.0, 362.0,
            313.0, 366.0, 379.0, 376.0, 423.0, 433.0, 486.0, 486.0, 482.0,
            518.0, 548.0, 583.0, 628.0, 705.0, 735.0, 814.0, 852.0, 920.0,
            1000.0, 1095.0, 1184.0, 1296.0, 1544.0, 1700.0, 2091.0, 2738.0,
            3794.0, 5591.0, 8640.0, 13619.0, 20171.0, 11051.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]

    def test_issue70(self):
        f = uproot.open("tests/samples/issue70.root")
        assert f.keys() == []

    def test_issue74(self):
        t = uproot.open("tests/samples/issue74.root")["Events"]
        assert all(
            isinstance(x[0], uproot_methods.classes.TVector3.Methods)
            for x in t.array("bees.xyzPosition"))
        assert t.array("bees.xyzPosition"
                       )[0][0] == uproot_methods.classes.TVector3.TVector3(
                           1.0, 2.0, -1.0)

    def test_issue76(self):
        t = uproot.open("tests/samples/issue76.root")["Events"]
        assert list(t.array("rootStrings")[0]) == [b"2", b"4"]
        x, y = t.array("rootStrings")[0]
        assert isinstance(x, uproot.rootio.TString)

    def test_issue79(self):
        t = uproot.open("tests/samples/issue79.root")["taus"]
        assert t["pt"].numbaskets == 2
        baskets = numpy.concatenate([t["pt"].basket(0), t["pt"].basket(1)])
        assert baskets.shape == (t["pt"].numentries, )
        assert numpy.array_equal(baskets, t["pt"].array())

    def test_issue96(self):
        t = uproot.open("tests/samples/issue96.root")["tree"]
        assert all(
            isinstance(x, uproot_methods.classes.TLorentzVector.Methods)
            for x in t.array("jet1P4"))

    def test_geant4(self):
        f = uproot.open("tests/samples/from-geant4.root")
        arrays = f["Details"].arrays()
        assert arrays[b"numgood"][0] == 224
        assert [len(x) for x in f["HitStrips"].arrays().values()
                ] == [4808, 4808, 4808]
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
        pytest.importorskip("xxhash")
        t = uproot.open("tests/samples/issue213.root")["T"]
        assert t["fMCHits.fPosition"].array().x.tolist() == [
            [], [], [], [], [], [], [], [42.17024612426758, 50.63192367553711],
            [], [], [], [43.292755126953125], [], [], [], [], [], [], [], [],
            [42.15415954589844], [41.60139083862305], [42.95103454589844], [],
            [41.55511474609375], [], [], [], [], [], [], [42.549156188964844],
            [], [], [], [42.80044174194336,
                         46.136253356933594], [], [], [], [],
            [41.58171081542969], [], [], [42.741485595703125],
            [41.228477478027344], [], [], [], [], [], [], [], [], [],
            [42.518882751464844], [43.34626388549805], [], [],
            [43.214759826660156], [], [], [], [], [], [], [42.78463363647461],
            [], [], [], [], [], [], [], [41.927093505859375],
            [42.65863037109375], [], [42.66266632080078], [], [], [], [], [],
            [], [], [], [], [], [41.91042709350586,
                                 41.807674407958984], [], [42.79293441772461],
            [], [], [], [], [], [], [41.72440719604492], [], [],
            [41.609615325927734]
        ]

    def test_issue232(self):
        pytest.importorskip("pandas")
        t = uproot.open("tests/samples/issue232.root")["fTreeV0"]
        t.pandas.df(
            ["V0Hyper.fNsigmaHe3Pos", "V0Hyper.fDcaPos2PrimaryVertex"],
            flatten=True)

    def test_issue240(self):
        pytest.importorskip("pyxrootd")
        t = uproot.open(
            "root://eospublic.cern.ch//eos/root-eos/cms_opendata_2012_nanoaod/Run2012B_DoubleMuParked.root"
        )["Events"]
        assert (abs(t.array("nMuon", entrystop=100000)) < 50).all()

    def test_issue243(self):
        t = uproot.open("tests/samples/issue243.root")["triggerList"]
        for x in t.array("triggerMap", entrystop=100):
            assert all(y == 1.0 for y in x.values())

    def test_issue243_new(self):
        t = uproot.open("tests/samples/issue243-new.root")["triggerList"]
        first = t["triggerMap.first"].array()
        second = t["triggerMap.second"].array()
        for i in range(t.numentries):
            x = dict(zip(first[i], second[i]))
            assert all(y == 1.0 for y in x.values())

    def test_issue327(self):
        uproot.open("tests/samples/issue327.root")["DstTree"]

    def test_issue371(self):
        t = uproot.open("tests/samples/issue371.root")["Event"]
        obj = t["DRIFT_0."].array()[0]
        assert obj._samplerName == b'DRIFT_0'
        assert obj._n == 1
        assert obj._energy[0] == numpy.array([2.3371024],
                                             dtype=numpy.float32)[0]

    def test_issue376_simple(self):
        f = uproot.open("tests/samples/from-geant4.root")
        assert type(f).classname == 'TDirectory'
        assert f.classname == 'TDirectory'
        real_class_names = ['TTree'] * 4 + ['TH1D'] * 10 + ['TH2D'] * 5
        assert [
            classname_two_tuple[1] for classname_two_tuple in f.classnames()
        ] == real_class_names
        assert [
            class_two_tuple[1].classname for class_two_tuple in f.classes()
        ] == real_class_names
        assert [value.classname for value in f.values()] == real_class_names

    def test_issue376_nested(self):
        f = uproot.open("tests/samples/nesteddirs.root")
        top_level_class_names = ['TDirectory', 'TDirectory']
        recursive_class_names = [
            'TDirectory', 'TDirectory', 'TTree', 'TTree', 'TDirectory', 'TTree'
        ]
        assert [
            classname_two_tuple[1]
            for classname_two_tuple in f.classnames(recursive=False)
        ] == top_level_class_names
        assert [
            classname_two_tuple[1]
            for classname_two_tuple in f.classnames(recursive=True)
        ] == recursive_class_names
        assert [
            classname_two_tuple[1]
            for classname_two_tuple in f.allclassnames()
        ] == recursive_class_names

    def test_issue367(self):
        t = uproot.open("tests/samples/issue367.root")["tree"]
        assert awkward.fromiter(
            t.array("weights.second"))[0].counts.tolist() == [
                1000, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 1000, 1000,
                1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,
                100, 100, 100, 1
            ]

    def test_issue390(self):
        pytest.importorskip("pandas")
        t = uproot.open("tests/samples/issue390.root")["E"]
        t.pandas.df("hits.*")
        t.pandas.df("trks.*")

    def test_issue399(self):
        t = uproot.open("tests/samples/issue399.root")["Event"]
        a = t["Histos.histograms1D"].array()
        for i in range(t.numentries):
            assert [x.title for x in a[i]] == [
                b"Primary Hits", b"Primary Loss", b"Energy Loss",
                b"Primary Hits per Element", b"Primary Loss per Element",
                b"Energy Loss per Element"
            ]

    def test_issue404(self):
        t = uproot.open("tests/samples/issue404.root")["Beam"]
        assert t["Beam.GMAD::BeamBase.beamParticleName"].array().tolist() == [
            b"proton"
        ]

    def test_issue124_and_followup_issue419_with_pr420(self):
        f = uproot.open("tests/samples/issue124.root")
        branch = f[b'KM3NET_TIMESLICE;1'][b'KM3NET_TIMESLICE']
        assert branch.interpretation is None
        assert 0 == branch.compressedbytes()
        assert 0 == branch.uncompressedbytes()
        assert 0 == branch.numbaskets

    def test_issue429(self):
        if sys.version_info[0] >= 3:
            fix = lambda name: name.decode("utf-8")
        else:
            fix = lambda name: name

        file = uproot.open("tests/samples/issue429.root")
        tree = file["data_tr"]
        branch = tree["data_ana_kk"]
        # FIXME: how can uproot.interp.auto.interpret *infer* the 4 bytes of padding?
        dtype = [(fix(x._fName), "float32" if type(x).__name__ == "TLeafF" else "int32") for x in branch._fLeaves]
        array = branch.array(uproot.asdtype(dtype + [("padding", "S4")]))
        assert (array["padding"] == b"\xff\xff\xff\xff").all()

    def test_issue431(self):
        file = uproot.open("tests/samples/issue431.root")
        head = file["Head"]
        assert head._map_3c_string_2c_string_3e_ == {b'DAQ': b'394', b'PDF': b'4      58', b'XSecFile': b'', b'can': b'0 1027 888.4', b'can_user': b'0.00 1027.00  888.40', b'coord_origin': b'0 0 0', b'cut_in': b'0 0 0 0', b'cut_nu': b'100 1e+08 -1 1', b'cut_primary': b'0 0 0 0', b'cut_seamuon': b'0 0 0 0', b'decay': b'doesnt happen', b'detector': b'NOT', b'drawing': b'Volume', b'end_event': b'', b'genhencut': b'2000 0', b'genvol': b'0 1027 888.4 2.649e+09 100000', b'kcut': b'2', b'livetime': b'0 0', b'model': b'1       2       0       1      12', b'muon_desc_file': b'', b'ngen': b'0.1000E+06', b'norma': b'0 0', b'nuflux': b'0       3       0 0.500E+00 0.000E+00 0.100E+01 0.300E+01', b'physics': b'GENHEN 7.2-220514 181116 1138', b'seed': b'GENHEN 3  305765867         0         0', b'simul': b'JSirene 11012 11/17/18 07', b'sourcemode': b'diffuse', b'spectrum': b'-1.4', b'start_run': b'1', b'target': b'isoscalar', b'usedetfile': b'false', b'xlat_user': b'0.63297', b'xparam': b'OFF', b'zed_user': b'0.00 3450.00'}

    def test_issue434(self):
        f = uproot.open("tests/samples/issue434.root")
        fromdtype = [("pmt", "u1"), ("tdc", "<u4"), ("tot", "u1")]
        todtype = [("pmt", "u1"), ("tdc", ">u4"), ("tot", "u1")]
        tree = f[b'KM3NET_TIMESLICE_L1'][b'KM3NETDAQ::JDAQTimeslice']
        superframes = tree[b'vector<KM3NETDAQ::JDAQSuperFrame>']
        hits_buffer = superframes[b'vector<KM3NETDAQ::JDAQSuperFrame>.buffer']
        hits = hits_buffer.lazyarray(
                uproot.asjagged(
                    uproot.astable(
                        uproot.asdtype(fromdtype, todtype)), skipbytes=6))
        assert 486480 == hits['tdc'][0][0]

    def test_issue438_accessing_memory_mapped_objects_outside_of_context_raises(self):
        with uproot.open("tests/samples/issue434.root") as f:
            a = f['KM3NET_EVENT']['KM3NET_EVENT']['KM3NETDAQ::JDAQPreamble'].array()
            b = f['KM3NET_EVENT']['KM3NET_EVENT']['KM3NETDAQ::JDAQPreamble'].lazyarray()
        assert 4 == len(a[0])
        with pytest.raises(IOError):
            len(b[0])

    def test_issue448(self):
        pytest.importorskip("pyxrootd")
        f = uproot.open('root://eospublic.cern.ch//eos/opendata/cms/Run2010B/MuOnia/AOD/Apr21ReReco-v1/0000/02186E3C-D277-E011-8A05-00215E21D516.root')
        tree = f['Events']
        assert len(tree.arrays(entrystop=0)) == 4179
        assert len(tree.arrays('recoMuons_muons__RECO.*', entrystop=10)) == 93

    @pytest.mark.parametrize("treename, branchtest", [
        ('l1CaloTowerEmuTree/L1CaloTowerTree', b'L1CaloTowerTree/L1CaloCluster/phi'),
        ('l1CaloTowerTree/L1CaloTowerTree', b'L1CaloTowerTree/L1CaloTower/et'),
    ])
    def test_issue447_tree_arrays_omitting_variables(self, treename, branchtest):
        with uproot.open("tests/samples/issue447.root") as f:
            t1 = f[treename]
            arrays = t1.arrays(recursive=b'/')
            array_keys = arrays.keys()
            n_array_vars = len(array_keys)
            n_tree_vars = sum([len(t1[k].keys()) for k in t1.keys()])
            assert n_tree_vars == n_array_vars
            assert branchtest in array_keys

    def test_issue447_recursive_provenance(self):
        expectedKeys = [
            'tree/b1',
            'tree/b1/b2',
            'tree/b1/b2/b3',
            'tree/b1/b2/b3/b4',
        ]
        expectedKeys = sorted([k.encode(encoding='UTF-8') for k in expectedKeys])
        with uproot.open('tests/samples/issue447_recursive.root') as f:
            t1 = f['tree']
            arrays = t1.arrays(recursive=b'/')
            assert sorted(list(arrays.keys())) == expectedKeys

    def test_issue444_subbranche_lookup_with_slash(self):
        # Uses same test file as issue #447
        with uproot.open("tests/samples/issue447.root") as f:
            # Access subbranches directly from file
            assert numpy.all(f['l1CaloTowerEmuTree/L1CaloTowerTree/CaloTP']['nECALTP'].array()
                == f['l1CaloTowerEmuTree/L1CaloTowerTree/CaloTP/nECALTP'].array())
            # Access subbranches from TTree
            tree = f['l1CaloTowerEmuTree/L1CaloTowerTree']
            assert numpy.all(tree['CaloTP']['nECALTP'].array()
                == tree['CaloTP/nECALTP'].array())
            # Test different recursive schemes
            assert b'CaloTP/nECALTP' in tree.keys(recursive='/')
            assert b'CaloTP/nECALTP' not in tree.keys(recursive=True)
            assert b'CaloTP/nECALTP' not in tree.keys(recursive=False)
            assert b'nECALTP' not in tree.keys(recursive='/')
            assert b'nECALTP' in tree.keys(recursive=True)
            assert b'nECALTP' not in tree.keys(recursive=False)
        # Specify subbranches in iterate
        for arrays in uproot.iterate(["tests/samples/issue447.root"], 'l1CaloTowerEmuTree/L1CaloTowerTree', ['CaloTP/nECALTP']):
            pass
