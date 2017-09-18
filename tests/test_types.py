#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy

import uproot

class TestTypes(unittest.TestCase):
    def runTest(self):
        pass

    @staticmethod
    def check(x, y):
        return x.dtype == y.dtype and x.shape == y.shape and numpy.array_equal(x, y)

    def test_socalled_flat(self):
        tree = uproot.open("tests/small-flat-tree.root")["tree"]

        hundred = list(range(100))
        self.assertTrue(self.check(tree.array("Int32"), numpy.array(hundred, dtype=">i4")))
        self.assertTrue(self.check(tree.array("Int64"), numpy.array(hundred, dtype=">i8")))
        self.assertTrue(self.check(tree.array("UInt32"), numpy.array(hundred, dtype=">u4")))
        self.assertTrue(self.check(tree.array("UInt64"), numpy.array(hundred, dtype=">u8")))
        self.assertTrue(self.check(tree.array("Float32"), numpy.array(hundred, dtype=">f4")))
        self.assertTrue(self.check(tree.array("Float64"), numpy.array(hundred, dtype=">f8")))

        hundredstrings = ["evt-{0:03d}".format(x).encode("ascii") for x in range(100)]
        self.assertTrue(self.check(tree.array("Str"), numpy.array(hundredstrings, dtype=object)))

        hundredarrays = [[x] * 10 for x in range(100)]
        self.assertTrue(self.check(tree.array("ArrayInt32"), numpy.array(hundredarrays, dtype=">i4")))
        self.assertTrue(self.check(tree.array("ArrayInt64"), numpy.array(hundredarrays, dtype=">i8")))
        self.assertTrue(self.check(tree.array("ArrayUInt32"), numpy.array(hundredarrays, dtype=">u4")))
        self.assertTrue(self.check(tree.array("ArrayUInt64"), numpy.array(hundredarrays, dtype=">u8")))
        self.assertTrue(self.check(tree.array("ArrayFloat32"), numpy.array(hundredarrays, dtype=">f4")))
        self.assertTrue(self.check(tree.array("ArrayFloat64"), numpy.array(hundredarrays, dtype=">f8")))

        self.assertTrue(self.check(tree.array("N"), numpy.array(list(range(10)) * 10, dtype=">i4")))

        sliced = [[x] * (x % 10) for x in range(100)]
        flattened = [y for x in sliced for y in x]

        self.assertTrue(self.check(tree.array("SliceInt32"), numpy.array(flattened, dtype=">i4")))
        self.assertTrue(self.check(tree.array("SliceInt64"), numpy.array(flattened, dtype=">i8")))
        self.assertTrue(self.check(tree.array("SliceUInt32"), numpy.array(flattened, dtype=">u4")))
        self.assertTrue(self.check(tree.array("SliceUInt64"), numpy.array(flattened, dtype=">u8")))
        self.assertTrue(self.check(tree.array("SliceFloat32"), numpy.array(flattened, dtype=">f4")))
        self.assertTrue(self.check(tree.array("SliceFloat64"), numpy.array(flattened, dtype=">f8")))

    def test_splitobject(self):
        tree = uproot.open("tests/small-evnt-tree-fullsplit.root")["tree"]
        
        self.assertTrue(self.check(tree.array("Beg"), numpy.array(["beg-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))

        hundred = list(range(100))
        self.assertTrue(self.check(tree.array("I16"), numpy.array(hundred, dtype=">i2")))
        self.assertTrue(self.check(tree.array("I32"), numpy.array(hundred, dtype=">i4")))
        self.assertTrue(self.check(tree.array("I64"), numpy.array(hundred, dtype=">i8")))
        self.assertTrue(self.check(tree.array("U16"), numpy.array(hundred, dtype=">u2")))
        self.assertTrue(self.check(tree.array("U32"), numpy.array(hundred, dtype=">u4")))
        self.assertTrue(self.check(tree.array("U64"), numpy.array(hundred, dtype=">u8")))
        self.assertTrue(self.check(tree.array("F32"), numpy.array(hundred, dtype=">f4")))
        self.assertTrue(self.check(tree.array("F64"), numpy.array(hundred, dtype=">f8")))

        self.assertTrue(self.check(tree.array("Str"), numpy.array(["evt-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))

        self.assertTrue(self.check(tree.array("P3.Px"), numpy.array(list(range(-1, 99)), dtype=">i4")))
        self.assertTrue(self.check(tree.array("P3.Py"), numpy.array(list(range(0, 100)), dtype=">f8")))
        self.assertTrue(self.check(tree.array("P3.Pz"), numpy.array(list(range(-1, 99)), dtype=">i4")))

        hundredarrays = [[x] * 10 for x in range(100)]
        self.assertTrue(self.check(tree.array("ArrayI16[10]"), numpy.array(hundredarrays, dtype=">i2")))
        self.assertTrue(self.check(tree.array("ArrayI32[10]"), numpy.array(hundredarrays, dtype=">i4")))
        self.assertTrue(self.check(tree.array("ArrayI64[10]"), numpy.array(hundredarrays, dtype=">i8")))
        self.assertTrue(self.check(tree.array("ArrayU32[10]"), numpy.array(hundredarrays, dtype=">u4")))
        self.assertTrue(self.check(tree.array("ArrayU64[10]"), numpy.array(hundredarrays, dtype=">u8")))
        self.assertTrue(self.check(tree.array("ArrayF32[10]"), numpy.array(hundredarrays, dtype=">f4")))
        self.assertTrue(self.check(tree.array("ArrayF64[10]"), numpy.array(hundredarrays, dtype=">f8")))

        self.assertTrue(self.check(tree.array("N"), numpy.array(list(range(10)) * 10, dtype=">i4")))

        sliced = [[x] * (x % 10) for x in range(100)]
        flattened = [y for x in sliced for y in x]

        self.assertTrue(self.check(tree.array("SliceI16"), numpy.array(flattened, dtype=">i2")))
        self.assertTrue(self.check(tree.array("SliceI32"), numpy.array(flattened, dtype=">i4")))
        self.assertTrue(self.check(tree.array("SliceI64"), numpy.array(flattened, dtype=">i8")))
        self.assertTrue(self.check(tree.array("SliceU16"), numpy.array(flattened, dtype=">u2")))
        self.assertTrue(self.check(tree.array("SliceU32"), numpy.array(flattened, dtype=">u4")))
        self.assertTrue(self.check(tree.array("SliceU64"), numpy.array(flattened, dtype=">u8")))
        self.assertTrue(self.check(tree.array("SliceF32"), numpy.array(flattened, dtype=">f4")))
        self.assertTrue(self.check(tree.array("SliceF64"), numpy.array(flattened, dtype=">f8")))

        self.assertTrue(self.check(tree.array("End"), numpy.array(["end-{0:03d}".format(x).encode("ascii") for x in range(100)], dtype=object)))

    def test_tclonesarray(self):
        tree = uproot.open("tests/mc10events.root")["Events"]
        self.assertEqual(tree.branchnames, [b"Info", b"GenEvtInfo", b"GenParticle", b"Electron", b"Muon", b"Tau", b"Photon", b"PV", b"AK4CHS", b"AK8CHS", b"AddAK8CHS", b"CA15CHS", b"AddCA15CHS", b"AK4Puppi", b"CA8Puppi", b"AddCA8Puppi", b"CA15Puppi", b"AddCA15Puppi"])

        self.assertEqual(tree.allbranchnames, [b"Info", b"runNum", b"evtNum", b"lumiSec", b"metFilterFailBits", b"nPU", b"nPUm", b"nPUp", b"nPUmean", b"nPUmeanm", b"nPUmeanp", b"pvx", b"pvy", b"pvz", b"bsx", b"bsy", b"bsz", b"pfMET", b"pfMETphi", b"pfMETCov00", b"pfMETCov01", b"pfMETCov11", b"pfMETC", b"pfMETCphi", b"pfMETCCov00", b"pfMETCCov01", b"pfMETCCov11", b"puppET", b"puppETphi", b"puppETCov00", b"puppETCov01", b"puppETCov11", b"puppETC", b"puppETCphi", b"puppETCCov00", b"puppETCCov01", b"puppETCCov11", b"alpacaMET", b"alpacaMETphi", b"pcpMET", b"pcpMETphi", b"rhoIso", b"rhoJet", b"triggerBits", b"hasGoodPV", b"GenEvtInfo", b"id_1", b"id_2", b"x_1", b"x_2", b"scalePDF", b"xs", b"weight", b"GenParticle", b"GenParticle.parent", b"GenParticle.pdgId", b"GenParticle.status", b"GenParticle.pt", b"GenParticle.eta", b"GenParticle.phi", b"GenParticle.mass", b"GenParticle.y", b"Electron", b"Electron.pt", b"Electron.eta", b"Electron.phi", b"Electron.scEt", b"Electron.scEta", b"Electron.scPhi", b"Electron.ecalEnergy", b"Electron.pfPt", b"Electron.pfEta", b"Electron.pfPhi", b"Electron.trkIso", b"Electron.ecalIso", b"Electron.hcalIso", b"Electron.hcalDepth1Iso", b"Electron.chHadIso", b"Electron.gammaIso", b"Electron.neuHadIso", b"Electron.puIso", b"Electron.ecalPFClusIso", b"Electron.hcalPFClusIso", b"Electron.puppiChHadIso", b"Electron.puppiGammaIso", b"Electron.puppiNeuHadIso", b"Electron.puppiChHadIsoNoLep", b"Electron.puppiGammaIsoNoLep", b"Electron.puppiNeuHadIsoNoLep", b"Electron.d0", b"Electron.dz", b"Electron.sip3d", b"Electron.sieie", b"Electron.e1x5", b"Electron.e2x5", b"Electron.e5x5", b"Electron.r9", b"Electron.eoverp", b"Electron.hovere", b"Electron.fbrem", b"Electron.dEtaInSeed", b"Electron.dEtaIn", b"Electron.dPhiIn", b"Electron.mva", b"Electron.q", b"Electron.isConv", b"Electron.nMissingHits", b"Electron.typeBits", b"Electron.fiducialBits", b"Electron.classification", b"Electron.scID", b"Electron.trkID", b"Electron.hltMatchBits", b"Muon", b"Muon.pt", b"Muon.eta", b"Muon.phi", b"Muon.ptErr", b"Muon.staPt", b"Muon.staEta", b"Muon.staPhi", b"Muon.pfPt", b"Muon.pfEta", b"Muon.pfPhi", b"Muon.trkIso", b"Muon.ecalIso", b"Muon.hcalIso", b"Muon.chHadIso", b"Muon.gammaIso", b"Muon.neuHadIso", b"Muon.puIso", b"Muon.puppiChHadIso", b"Muon.puppiGammaIso", b"Muon.puppiNeuHadIso", b"Muon.puppiChHadIsoNoLep", b"Muon.puppiGammaIsoNoLep", b"Muon.puppiNeuHadIsoNoLep", b"Muon.d0", b"Muon.dz", b"Muon.sip3d", b"Muon.tkNchi2", b"Muon.muNchi2", b"Muon.trkKink", b"Muon.glbKink", b"Muon.trkHitFrac", b"Muon.chi2LocPos", b"Muon.segComp", b"Muon.caloComp", b"Muon.q", b"Muon.nValidHits", b"Muon.typeBits", b"Muon.selectorBits", b"Muon.pogIDBits", b"Muon.nTkHits", b"Muon.nPixHits", b"Muon.nTkLayers", b"Muon.nPixLayers", b"Muon.nMatchStn", b"Muon.trkID", b"Muon.hltMatchBits", b"Tau", b"Tau.pt", b"Tau.eta", b"Tau.phi", b"Tau.m", b"Tau.e", b"Tau.q", b"Tau.dzLeadChHad", b"Tau.nSignalChHad", b"Tau.nSignalGamma", b"Tau.antiEleMVA5", b"Tau.antiEleMVA5Cat", b"Tau.rawMuonRejection", b"Tau.rawIso3Hits", b"Tau.rawIsoMVA3oldDMwoLT", b"Tau.rawIsoMVA3oldDMwLT", b"Tau.rawIsoMVA3newDMwoLT", b"Tau.rawIsoMVA3newDMwLT", b"Tau.puppiChHadIso", b"Tau.puppiGammaIso", b"Tau.puppiNeuHadIso", b"Tau.puppiChHadIsoNoLep", b"Tau.puppiGammaIsoNoLep", b"Tau.puppiNeuHadIsoNoLep", b"Tau.hpsDisc", b"Tau.hltMatchBits", b"Photon", b"Photon.pt", b"Photon.eta", b"Photon.phi", b"Photon.scEt", b"Photon.scEta", b"Photon.scPhi", b"Photon.trkIso", b"Photon.ecalIso", b"Photon.hcalIso", b"Photon.chHadIso", b"Photon.gammaIso", b"Photon.neuHadIso", b"Photon.mva", b"Photon.hovere", b"Photon.sthovere", b"Photon.sieie", b"Photon.sipip", b"Photon.r9", b"Photon.fiducialBits", b"Photon.typeBits", b"Photon.scID", b"Photon.hasPixelSeed", b"Photon.passElectronVeto", b"Photon.isConv", b"Photon.hltMatchBits", b"PV", b"PV.nTracksFit", b"PV.ndof", b"PV.chi2", b"PV.x", b"PV.y", b"PV.z", b"AK4CHS", b"AK4CHS.pt", b"AK4CHS.eta", b"AK4CHS.phi", b"AK4CHS.mass", b"AK4CHS.ptRaw", b"AK4CHS.unc", b"AK4CHS.area", b"AK4CHS.d0", b"AK4CHS.dz", b"AK4CHS.csv", b"AK4CHS.bmva", b"AK4CHS.cvb", b"AK4CHS.cvl", b"AK4CHS.qgid", b"AK4CHS.axis2", b"AK4CHS.ptD", b"AK4CHS.mult", b"AK4CHS.q", b"AK4CHS.mva", b"AK4CHS.beta", b"AK4CHS.betaStar", b"AK4CHS.dR2Mean", b"AK4CHS.pullY", b"AK4CHS.pullPhi", b"AK4CHS.chPullY", b"AK4CHS.chPullPhi", b"AK4CHS.neuPullY", b"AK4CHS.neuPullPhi", b"AK4CHS.chEmFrac", b"AK4CHS.neuEmFrac", b"AK4CHS.chHadFrac", b"AK4CHS.neuHadFrac", b"AK4CHS.muonFrac", b"AK4CHS.genpt", b"AK4CHS.geneta", b"AK4CHS.genphi", b"AK4CHS.genm", b"AK4CHS.partonFlavor", b"AK4CHS.hadronFlavor", b"AK4CHS.nCharged", b"AK4CHS.nNeutrals", b"AK4CHS.nParticles", b"AK4CHS.hltMatchBits", b"AK8CHS", b"AK8CHS.pt", b"AK8CHS.eta", b"AK8CHS.phi", b"AK8CHS.mass", b"AK8CHS.ptRaw", b"AK8CHS.unc", b"AK8CHS.area", b"AK8CHS.d0", b"AK8CHS.dz", b"AK8CHS.csv", b"AK8CHS.bmva", b"AK8CHS.cvb", b"AK8CHS.cvl", b"AK8CHS.qgid", b"AK8CHS.axis2", b"AK8CHS.ptD", b"AK8CHS.mult", b"AK8CHS.q", b"AK8CHS.mva", b"AK8CHS.beta", b"AK8CHS.betaStar", b"AK8CHS.dR2Mean", b"AK8CHS.pullY", b"AK8CHS.pullPhi", b"AK8CHS.chPullY", b"AK8CHS.chPullPhi", b"AK8CHS.neuPullY", b"AK8CHS.neuPullPhi", b"AK8CHS.chEmFrac", b"AK8CHS.neuEmFrac", b"AK8CHS.chHadFrac", b"AK8CHS.neuHadFrac", b"AK8CHS.muonFrac", b"AK8CHS.genpt", b"AK8CHS.geneta", b"AK8CHS.genphi", b"AK8CHS.genm", b"AK8CHS.partonFlavor", b"AK8CHS.hadronFlavor", b"AK8CHS.nCharged", b"AK8CHS.nNeutrals", b"AK8CHS.nParticles", b"AK8CHS.hltMatchBits", b"AddAK8CHS", b"AddAK8CHS.index", b"AddAK8CHS.mass_prun", b"AddAK8CHS.mass_trim", b"AddAK8CHS.mass_sd0", b"AddAK8CHS.c2_0", b"AddAK8CHS.c2_0P2", b"AddAK8CHS.c2_0P5", b"AddAK8CHS.c2_1P0", b"AddAK8CHS.c2_2P0", b"AddAK8CHS.qjet", b"AddAK8CHS.tau1", b"AddAK8CHS.tau2", b"AddAK8CHS.tau3", b"AddAK8CHS.tau4", b"AddAK8CHS.doublecsv", b"AddAK8CHS.sj1_pt", b"AddAK8CHS.sj1_eta", b"AddAK8CHS.sj1_phi", b"AddAK8CHS.sj1_m", b"AddAK8CHS.sj1_csv", b"AddAK8CHS.sj1_qgid", b"AddAK8CHS.sj1_q", b"AddAK8CHS.sj2_pt", b"AddAK8CHS.sj2_eta", b"AddAK8CHS.sj2_phi", b"AddAK8CHS.sj2_m", b"AddAK8CHS.sj2_csv", b"AddAK8CHS.sj2_qgid", b"AddAK8CHS.sj2_q", b"AddAK8CHS.sj3_pt", b"AddAK8CHS.sj3_eta", b"AddAK8CHS.sj3_phi", b"AddAK8CHS.sj3_m", b"AddAK8CHS.sj3_csv", b"AddAK8CHS.sj3_qgid", b"AddAK8CHS.sj3_q", b"AddAK8CHS.sj4_pt", b"AddAK8CHS.sj4_eta", b"AddAK8CHS.sj4_phi", b"AddAK8CHS.sj4_m", b"AddAK8CHS.sj4_csv", b"AddAK8CHS.sj4_qgid", b"AddAK8CHS.sj4_q", b"AddAK8CHS.pullAngle", b"AddAK8CHS.topTagType", b"AddAK8CHS.top_n_subjets", b"AddAK8CHS.top_m_min", b"AddAK8CHS.top_m_123", b"AddAK8CHS.top_fRec", b"AddAK8CHS.topchi2", b"CA15CHS", b"CA15CHS.pt", b"CA15CHS.eta", b"CA15CHS.phi", b"CA15CHS.mass", b"CA15CHS.ptRaw", b"CA15CHS.unc", b"CA15CHS.area", b"CA15CHS.d0", b"CA15CHS.dz", b"CA15CHS.csv", b"CA15CHS.bmva", b"CA15CHS.cvb", b"CA15CHS.cvl", b"CA15CHS.qgid", b"CA15CHS.axis2", b"CA15CHS.ptD", b"CA15CHS.mult", b"CA15CHS.q", b"CA15CHS.mva", b"CA15CHS.beta", b"CA15CHS.betaStar", b"CA15CHS.dR2Mean", b"CA15CHS.pullY", b"CA15CHS.pullPhi", b"CA15CHS.chPullY", b"CA15CHS.chPullPhi", b"CA15CHS.neuPullY", b"CA15CHS.neuPullPhi", b"CA15CHS.chEmFrac", b"CA15CHS.neuEmFrac", b"CA15CHS.chHadFrac", b"CA15CHS.neuHadFrac", b"CA15CHS.muonFrac", b"CA15CHS.genpt", b"CA15CHS.geneta", b"CA15CHS.genphi", b"CA15CHS.genm", b"CA15CHS.partonFlavor", b"CA15CHS.hadronFlavor", b"CA15CHS.nCharged", b"CA15CHS.nNeutrals", b"CA15CHS.nParticles", b"CA15CHS.hltMatchBits", b"AddCA15CHS", b"AddCA15CHS.index", b"AddCA15CHS.mass_prun", b"AddCA15CHS.mass_trim", b"AddCA15CHS.mass_sd0", b"AddCA15CHS.c2_0", b"AddCA15CHS.c2_0P2", b"AddCA15CHS.c2_0P5", b"AddCA15CHS.c2_1P0", b"AddCA15CHS.c2_2P0", b"AddCA15CHS.qjet", b"AddCA15CHS.tau1", b"AddCA15CHS.tau2", b"AddCA15CHS.tau3", b"AddCA15CHS.tau4", b"AddCA15CHS.doublecsv", b"AddCA15CHS.sj1_pt", b"AddCA15CHS.sj1_eta", b"AddCA15CHS.sj1_phi", b"AddCA15CHS.sj1_m", b"AddCA15CHS.sj1_csv", b"AddCA15CHS.sj1_qgid", b"AddCA15CHS.sj1_q", b"AddCA15CHS.sj2_pt", b"AddCA15CHS.sj2_eta", b"AddCA15CHS.sj2_phi", b"AddCA15CHS.sj2_m", b"AddCA15CHS.sj2_csv", b"AddCA15CHS.sj2_qgid", b"AddCA15CHS.sj2_q", b"AddCA15CHS.sj3_pt", b"AddCA15CHS.sj3_eta", b"AddCA15CHS.sj3_phi", b"AddCA15CHS.sj3_m", b"AddCA15CHS.sj3_csv", b"AddCA15CHS.sj3_qgid", b"AddCA15CHS.sj3_q", b"AddCA15CHS.sj4_pt", b"AddCA15CHS.sj4_eta", b"AddCA15CHS.sj4_phi", b"AddCA15CHS.sj4_m", b"AddCA15CHS.sj4_csv", b"AddCA15CHS.sj4_qgid", b"AddCA15CHS.sj4_q", b"AddCA15CHS.pullAngle", b"AddCA15CHS.topTagType", b"AddCA15CHS.top_n_subjets", b"AddCA15CHS.top_m_min", b"AddCA15CHS.top_m_123", b"AddCA15CHS.top_fRec", b"AddCA15CHS.topchi2", b"AK4Puppi", b"AK4Puppi.pt", b"AK4Puppi.eta", b"AK4Puppi.phi", b"AK4Puppi.mass", b"AK4Puppi.ptRaw", b"AK4Puppi.unc", b"AK4Puppi.area", b"AK4Puppi.d0", b"AK4Puppi.dz", b"AK4Puppi.csv", b"AK4Puppi.bmva", b"AK4Puppi.cvb", b"AK4Puppi.cvl", b"AK4Puppi.qgid", b"AK4Puppi.axis2", b"AK4Puppi.ptD", b"AK4Puppi.mult", b"AK4Puppi.q", b"AK4Puppi.mva", b"AK4Puppi.beta", b"AK4Puppi.betaStar", b"AK4Puppi.dR2Mean", b"AK4Puppi.pullY", b"AK4Puppi.pullPhi", b"AK4Puppi.chPullY", b"AK4Puppi.chPullPhi", b"AK4Puppi.neuPullY", b"AK4Puppi.neuPullPhi", b"AK4Puppi.chEmFrac", b"AK4Puppi.neuEmFrac", b"AK4Puppi.chHadFrac", b"AK4Puppi.neuHadFrac", b"AK4Puppi.muonFrac", b"AK4Puppi.genpt", b"AK4Puppi.geneta", b"AK4Puppi.genphi", b"AK4Puppi.genm", b"AK4Puppi.partonFlavor", b"AK4Puppi.hadronFlavor", b"AK4Puppi.nCharged", b"AK4Puppi.nNeutrals", b"AK4Puppi.nParticles", b"AK4Puppi.hltMatchBits", b"CA8Puppi", b"CA8Puppi.pt", b"CA8Puppi.eta", b"CA8Puppi.phi", b"CA8Puppi.mass", b"CA8Puppi.ptRaw", b"CA8Puppi.unc", b"CA8Puppi.area", b"CA8Puppi.d0", b"CA8Puppi.dz", b"CA8Puppi.csv", b"CA8Puppi.bmva", b"CA8Puppi.cvb", b"CA8Puppi.cvl", b"CA8Puppi.qgid", b"CA8Puppi.axis2", b"CA8Puppi.ptD", b"CA8Puppi.mult", b"CA8Puppi.q", b"CA8Puppi.mva", b"CA8Puppi.beta", b"CA8Puppi.betaStar", b"CA8Puppi.dR2Mean", b"CA8Puppi.pullY", b"CA8Puppi.pullPhi", b"CA8Puppi.chPullY", b"CA8Puppi.chPullPhi", b"CA8Puppi.neuPullY", b"CA8Puppi.neuPullPhi", b"CA8Puppi.chEmFrac", b"CA8Puppi.neuEmFrac", b"CA8Puppi.chHadFrac", b"CA8Puppi.neuHadFrac", b"CA8Puppi.muonFrac", b"CA8Puppi.genpt", b"CA8Puppi.geneta", b"CA8Puppi.genphi", b"CA8Puppi.genm", b"CA8Puppi.partonFlavor", b"CA8Puppi.hadronFlavor", b"CA8Puppi.nCharged", b"CA8Puppi.nNeutrals", b"CA8Puppi.nParticles", b"CA8Puppi.hltMatchBits", b"AddCA8Puppi", b"AddCA8Puppi.index", b"AddCA8Puppi.mass_prun", b"AddCA8Puppi.mass_trim", b"AddCA8Puppi.mass_sd0", b"AddCA8Puppi.c2_0", b"AddCA8Puppi.c2_0P2", b"AddCA8Puppi.c2_0P5", b"AddCA8Puppi.c2_1P0", b"AddCA8Puppi.c2_2P0", b"AddCA8Puppi.qjet", b"AddCA8Puppi.tau1", b"AddCA8Puppi.tau2", b"AddCA8Puppi.tau3", b"AddCA8Puppi.tau4", b"AddCA8Puppi.doublecsv", b"AddCA8Puppi.sj1_pt", b"AddCA8Puppi.sj1_eta", b"AddCA8Puppi.sj1_phi", b"AddCA8Puppi.sj1_m", b"AddCA8Puppi.sj1_csv", b"AddCA8Puppi.sj1_qgid", b"AddCA8Puppi.sj1_q", b"AddCA8Puppi.sj2_pt", b"AddCA8Puppi.sj2_eta", b"AddCA8Puppi.sj2_phi", b"AddCA8Puppi.sj2_m", b"AddCA8Puppi.sj2_csv", b"AddCA8Puppi.sj2_qgid", b"AddCA8Puppi.sj2_q", b"AddCA8Puppi.sj3_pt", b"AddCA8Puppi.sj3_eta", b"AddCA8Puppi.sj3_phi", b"AddCA8Puppi.sj3_m", b"AddCA8Puppi.sj3_csv", b"AddCA8Puppi.sj3_qgid", b"AddCA8Puppi.sj3_q", b"AddCA8Puppi.sj4_pt", b"AddCA8Puppi.sj4_eta", b"AddCA8Puppi.sj4_phi", b"AddCA8Puppi.sj4_m", b"AddCA8Puppi.sj4_csv", b"AddCA8Puppi.sj4_qgid", b"AddCA8Puppi.sj4_q", b"AddCA8Puppi.pullAngle", b"AddCA8Puppi.topTagType", b"AddCA8Puppi.top_n_subjets", b"AddCA8Puppi.top_m_min", b"AddCA8Puppi.top_m_123", b"AddCA8Puppi.top_fRec", b"AddCA8Puppi.topchi2", b"CA15Puppi", b"CA15Puppi.pt", b"CA15Puppi.eta", b"CA15Puppi.phi", b"CA15Puppi.mass", b"CA15Puppi.ptRaw", b"CA15Puppi.unc", b"CA15Puppi.area", b"CA15Puppi.d0", b"CA15Puppi.dz", b"CA15Puppi.csv", b"CA15Puppi.bmva", b"CA15Puppi.cvb", b"CA15Puppi.cvl", b"CA15Puppi.qgid", b"CA15Puppi.axis2", b"CA15Puppi.ptD", b"CA15Puppi.mult", b"CA15Puppi.q", b"CA15Puppi.mva", b"CA15Puppi.beta", b"CA15Puppi.betaStar", b"CA15Puppi.dR2Mean", b"CA15Puppi.pullY", b"CA15Puppi.pullPhi", b"CA15Puppi.chPullY", b"CA15Puppi.chPullPhi", b"CA15Puppi.neuPullY", b"CA15Puppi.neuPullPhi", b"CA15Puppi.chEmFrac", b"CA15Puppi.neuEmFrac", b"CA15Puppi.chHadFrac", b"CA15Puppi.neuHadFrac", b"CA15Puppi.muonFrac", b"CA15Puppi.genpt", b"CA15Puppi.geneta", b"CA15Puppi.genphi", b"CA15Puppi.genm", b"CA15Puppi.partonFlavor", b"CA15Puppi.hadronFlavor", b"CA15Puppi.nCharged", b"CA15Puppi.nNeutrals", b"CA15Puppi.nParticles", b"CA15Puppi.hltMatchBits", b"AddCA15Puppi", b"AddCA15Puppi.index", b"AddCA15Puppi.mass_prun", b"AddCA15Puppi.mass_trim", b"AddCA15Puppi.mass_sd0", b"AddCA15Puppi.c2_0", b"AddCA15Puppi.c2_0P2", b"AddCA15Puppi.c2_0P5", b"AddCA15Puppi.c2_1P0", b"AddCA15Puppi.c2_2P0", b"AddCA15Puppi.qjet", b"AddCA15Puppi.tau1", b"AddCA15Puppi.tau2", b"AddCA15Puppi.tau3", b"AddCA15Puppi.tau4", b"AddCA15Puppi.doublecsv", b"AddCA15Puppi.sj1_pt", b"AddCA15Puppi.sj1_eta", b"AddCA15Puppi.sj1_phi", b"AddCA15Puppi.sj1_m", b"AddCA15Puppi.sj1_csv", b"AddCA15Puppi.sj1_qgid", b"AddCA15Puppi.sj1_q", b"AddCA15Puppi.sj2_pt", b"AddCA15Puppi.sj2_eta", b"AddCA15Puppi.sj2_phi", b"AddCA15Puppi.sj2_m", b"AddCA15Puppi.sj2_csv", b"AddCA15Puppi.sj2_qgid", b"AddCA15Puppi.sj2_q", b"AddCA15Puppi.sj3_pt", b"AddCA15Puppi.sj3_eta", b"AddCA15Puppi.sj3_phi", b"AddCA15Puppi.sj3_m", b"AddCA15Puppi.sj3_csv", b"AddCA15Puppi.sj3_qgid", b"AddCA15Puppi.sj3_q", b"AddCA15Puppi.sj4_pt", b"AddCA15Puppi.sj4_eta", b"AddCA15Puppi.sj4_phi", b"AddCA15Puppi.sj4_m", b"AddCA15Puppi.sj4_csv", b"AddCA15Puppi.sj4_qgid", b"AddCA15Puppi.sj4_q", b"AddCA15Puppi.pullAngle", b"AddCA15Puppi.topTagType", b"AddCA15Puppi.top_n_subjets", b"AddCA15Puppi.top_m_min", b"AddCA15Puppi.top_m_123", b"AddCA15Puppi.top_fRec", b"AddCA15Puppi.topchi2"])

        for singleton in b"Info", b"GenEvtInfo":
            for branchname in tree.branch(singleton).branchnames:
                self.assertTrue(branchname not in tree.counter)
                if hasattr(tree.branch(singleton).branch(branchname), "dtype"):
                    self.assertEqual(tree.branch(singleton).branch(branchname).array().shape, (tree.numentries,))
                
        for tclonesarray in b"GenParticle", b"Electron", b"Muon", b"Tau", b"Photon", b"PV", b"AK4CHS", b"AK8CHS", b"AddAK8CHS", b"CA15CHS", b"AddCA15CHS", b"AK4Puppi", b"CA8Puppi", b"AddCA8Puppi", b"CA15Puppi", b"AddCA15Puppi":
            length = sum(tree.branch(tclonesarray).array())
            for branchname in tree.branch(tclonesarray).branchnames:
                self.assertEqual(tree.counter[branchname], tree.Counter(tclonesarray, tclonesarray + b"_"))
                if hasattr(tree.branch(tclonesarray).branch(branchname), "dtype"):
                    self.assertEqual(tree.branch(tclonesarray).branch(branchname).array().shape, (length,))
