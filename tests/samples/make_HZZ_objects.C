#include <vector>
#include "TLorentzVector.h"

void make_HZZ_objects() {
  TFile* file = new TFile("tests/samples/HZZ.root");
  TTree* tree;
  file->GetObject("events", tree);

  TTreeReader reader(tree);

  TTreeReaderValue<int> NJet(reader, "NJet");
  TTreeReaderArray<float> Jet_Px(reader, "Jet_Px");
  TTreeReaderArray<float> Jet_Py(reader, "Jet_Py");
  TTreeReaderArray<float> Jet_Pz(reader, "Jet_Pz");
  TTreeReaderArray<float> Jet_E(reader, "Jet_E");
  TTreeReaderArray<float> Jet_btag(reader, "Jet_btag");
  TTreeReaderArray<bool> Jet_ID(reader, "Jet_ID");

  TTreeReaderValue<int> NMuon(reader, "NMuon");
  TTreeReaderArray<float> Muon_Px(reader, "Muon_Px");
  TTreeReaderArray<float> Muon_Py(reader, "Muon_Py");
  TTreeReaderArray<float> Muon_Pz(reader, "Muon_Pz");
  TTreeReaderArray<float> Muon_E(reader, "Muon_E");
  TTreeReaderArray<int> Muon_Charge(reader, "Muon_Charge");
  TTreeReaderArray<float> Muon_Iso(reader, "Muon_Iso");

  TTreeReaderValue<int> NElectron(reader, "NElectron");
  TTreeReaderArray<float> Electron_Px(reader, "Electron_Px");
  TTreeReaderArray<float> Electron_Py(reader, "Electron_Py");
  TTreeReaderArray<float> Electron_Pz(reader, "Electron_Pz");
  TTreeReaderArray<float> Electron_E(reader, "Electron_E");
  TTreeReaderArray<int> Electron_Charge(reader, "Electron_Charge");
  TTreeReaderArray<float> Electron_Iso(reader, "Electron_Iso");

  TTreeReaderValue<int> NPhoton(reader, "NPhoton");
  TTreeReaderArray<float> Photon_Px(reader, "Photon_Px");
  TTreeReaderArray<float> Photon_Py(reader, "Photon_Py");
  TTreeReaderArray<float> Photon_Pz(reader, "Photon_Pz");
  TTreeReaderArray<float> Photon_E(reader, "Photon_E.Photons_E");
  TTreeReaderArray<float> Photon_Iso(reader, "Photon_Iso");

  TTreeReaderValue<float> MET_px(reader, "MET_px");
  TTreeReaderValue<float> MET_py(reader, "MET_py");

  TTreeReaderValue<float> MChadronicBottom_px(reader, "MChadronicBottom_px");
  TTreeReaderValue<float> MChadronicBottom_py(reader, "MChadronicBottom_py");
  TTreeReaderValue<float> MChadronicBottom_pz(reader, "MChadronicBottom_pz");

  TTreeReaderValue<float> MCleptonicBottom_px(reader, "MCleptonicBottom_px");
  TTreeReaderValue<float> MCleptonicBottom_py(reader, "MCleptonicBottom_py");
  TTreeReaderValue<float> MCleptonicBottom_pz(reader, "MCleptonicBottom_pz");

  TTreeReaderValue<float> MChadronicWDecayQuark_px(reader, "MChadronicWDecayQuark_px");
  TTreeReaderValue<float> MChadronicWDecayQuark_py(reader, "MChadronicWDecayQuark_py");
  TTreeReaderValue<float> MChadronicWDecayQuark_pz(reader, "MChadronicWDecayQuark_pz");
  TTreeReaderValue<float> MChadronicWDecayQuarkBar_px(reader, "MChadronicWDecayQuarkBar_px");
  TTreeReaderValue<float> MChadronicWDecayQuarkBar_py(reader, "MChadronicWDecayQuarkBar_py");
  TTreeReaderValue<float> MChadronicWDecayQuarkBar_pz(reader, "MChadronicWDecayQuarkBar_pz");

  TTreeReaderValue<float> MClepton_px(reader, "MClepton_px");
  TTreeReaderValue<float> MClepton_py(reader, "MClepton_py");
  TTreeReaderValue<float> MClepton_pz(reader, "MClepton_pz");
  TTreeReaderValue<int> MCleptonPDGid(reader, "MCleptonPDGid");

  TTreeReaderValue<float> MCneutrino_px(reader, "MCneutrino_px");
  TTreeReaderValue<float> MCneutrino_py(reader, "MCneutrino_py");
  TTreeReaderValue<float> MCneutrino_pz(reader, "MCneutrino_pz");

  TTreeReaderValue<int> NPrimaryVertices(reader, "NPrimaryVertices");
  TTreeReaderValue<bool> triggerIsoMu24(reader, "triggerIsoMu24");
  TTreeReaderValue<float> EventWeight(reader, "EventWeight");

  TFile* outfile = new TFile("HZZ-objects.root", "RECREATE");
  TTree outtree("events", "");

  std::vector<TLorentzVector> jetp4;
  std::vector<float> jetbtag;
  std::vector<bool> jetid;
  outtree.Branch("jetp4", "std::vector<TLorentzVector>", &jetp4);
  outtree.Branch("jetbtag", "std::vector<float>", &jetbtag);
  outtree.Branch("jetid", "std::vector<bool>", &jetid);

  std::vector<TLorentzVector> muonp4;
  std::vector<int> muonq;
  std::vector<float> muoniso;
  outtree.Branch("muonp4", "std::vector<TLorentzVector>", &muonp4);
  outtree.Branch("muonq", "std::vector<int>", &muonq);
  outtree.Branch("muoniso", "std::vector<float>", &muoniso);

  std::vector<TLorentzVector> electronp4;
  std::vector<int> electronq;
  std::vector<float> electroniso;
  outtree.Branch("electronp4", "std::vector<TLorentzVector>", &electronp4);
  outtree.Branch("electronq", "std::vector<int>", &electronq);
  outtree.Branch("electroniso", "std::vector<float>", &electroniso);

  std::vector<TLorentzVector> photonp4;
  std::vector<float> photoniso;
  outtree.Branch("photonp4", "std::vector<TLorentzVector>", &photonp4);
  outtree.Branch("photoniso", "std::vector<float>", &photoniso);

  TVector2 MET;
  outtree.Branch("MET", "TVector2", &MET);

  TVector3 MC_bquarkhadronic;
  outtree.Branch("MC_bquarkhadronic", "TVector3", &MC_bquarkhadronic);

  TVector3 MC_bquarkleptonic;
  outtree.Branch("MC_bquarkleptonic", "TVector3", &MC_bquarkleptonic);

  TVector3 MC_wdecayb;
  outtree.Branch("MC_wdecayb", "TVector3", &MC_wdecayb);

  TVector3 MC_wdecaybbar;
  outtree.Branch("MC_wdecaybbar", "TVector3", &MC_wdecaybbar);

  TVector3 MC_lepton;
  int32_t MC_leptonpdgid;
  outtree.Branch("MC_lepton", "TVector3", &MC_lepton);
  outtree.Branch("MC_leptonpdgid", &MC_leptonpdgid, "MC_leptonpdgid/I");

  TVector3 MC_neutrino;
  outtree.Branch("MC_neutrino", "TVector3", &MC_neutrino);

  int32_t num_primaryvertex;
  outtree.Branch("num_primaryvertex", &num_primaryvertex, "num_primaryvertex/I");

  bool trigger_isomu24;
  outtree.Branch("trigger_isomu24", &trigger_isomu24, "trigger_isomu24/O");

  float eventweight;
  outtree.Branch("eventweight", &eventweight, "eventweight/F");

  while (reader.Next()) {
    jetp4.clear();
    jetbtag.clear();
    jetid.clear();
    for (int i = 0;  i < *NJet;  i++) {
      jetp4.push_back(TLorentzVector(Jet_Px[i], Jet_Py[i], Jet_Pz[i], Jet_E[i]));
      jetbtag.push_back(Jet_btag[i]);
      jetid.push_back(Jet_ID[i]);
    }

    muonp4.clear();
    muonq.clear();
    muoniso.clear();
    for (int i = 0;  i < *NMuon;  i++) {
      muonp4.push_back(TLorentzVector(Muon_Px[i], Muon_Py[i], Muon_Pz[i], Muon_E[i]));
      muonq.push_back(Muon_Charge[i]);
      muoniso.push_back(Muon_Iso[i]);
    }

    electronp4.clear();
    electronq.clear();
    electroniso.clear();
    for (int i = 0;  i < *NElectron;  i++) {
      electronp4.push_back(TLorentzVector(Electron_Px[i], Electron_Py[i], Electron_Pz[i], Electron_E[i]));
      electronq.push_back(Electron_Charge[i]);
      electroniso.push_back(Electron_Iso[i]);
    }

    photonp4.clear();
    photoniso.clear();
    for (int i = 0;  i < *NPhoton;  i++) {
      photonp4.push_back(TLorentzVector(Photon_Px[i], Photon_Py[i], Photon_Pz[i], Photon_E[i]));
      photoniso.push_back(Photon_Iso[i]);
    }

    MET.Set(*MET_px, *MET_py);
    MC_bquarkhadronic.SetXYZ(*MChadronicBottom_px, *MChadronicBottom_py, *MChadronicBottom_pz);
    MC_bquarkleptonic.SetXYZ(*MCleptonicBottom_px, *MCleptonicBottom_py, *MCleptonicBottom_pz);
    MC_wdecayb.SetXYZ(*MChadronicWDecayQuark_px, *MChadronicWDecayQuark_py, *MChadronicWDecayQuark_pz);
    MC_wdecaybbar.SetXYZ(*MChadronicWDecayQuarkBar_px, *MChadronicWDecayQuarkBar_py, *MChadronicWDecayQuarkBar_pz);
    MC_lepton.SetXYZ(*MClepton_px, *MClepton_py, *MClepton_pz);
    MC_leptonpdgid = *MCleptonPDGid;
    MC_neutrino.SetXYZ(*MCneutrino_px, *MCneutrino_py, *MCneutrino_pz);
    num_primaryvertex = *NPrimaryVertices;
    trigger_isomu24 = *triggerIsoMu24;
    eventweight = *EventWeight;

    outtree.Fill();
  }

  outtree.Write();
  outfile->Close();
}
