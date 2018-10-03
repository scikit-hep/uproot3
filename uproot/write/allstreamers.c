//Need TObjString, TH*, TProfile*, TTree with all primitive type branches, char*, all STL vector<>, string, vector<strings>, std::bitset, TLorentzVector, TVector2, TGraph, TMultiGraph.
//Check streamers for TBranchElement, TLeafElement, TLeaf0, TLeafC.

void allstreamers(){
    TFile *tfile = new TFile("allstreamers.root", "RECREATE");
    tfile->SetCompressionLevel(0);
    
    TH1F* hist1 = new TH1F("habla1f", "th1f title", 10, 2.1, 3.1);
    TH1C* hist2 = new TH1C("habla1c", "th1c title", 10, 2.1, 3.1);
    TH1I* hist3 = new TH1I("habla1i", "th1i title", 10, 2.1, 3.1);
    TH1D* hist4 = new TH1D("habla1d", "th1d title", 10, 2.1, 3.1);
    TH1S* hist5 = new TH1S("habla1s", "th1s title", 10, 2.1, 3.1);
	
	TH2C* hist6 = new TH2C("habla2c", "th2c title", 10, 2.1, 3.1, 5, 1.1, 2.1);
	TH2S* hist7 = new TH2S("habla2s", "th2s title", 10, 2.1, 3.1, 5, 1.1, 2.1);
	TH2I* hist8 = new TH2I("habla2i", "th2i title", 10, 2.1, 3.1, 5, 1.1, 2.1);
	TH2F* hist9 = new TH2F("habla2f", "th2f title", 10, 2.1, 3.1, 5, 1.1, 2.1);
	TH2D* hist10 = new TH2D("habla2d", "th2d title", 10, 2.1, 3.1, 5, 1.1, 2.1);
    
    TH3C* hist11 = new TH3C("habla3c", "th3c title", 10, 2.1, 3.1, 5, 1.1, 2.1, 5, 1.1, 2.1);
    TH3S* hist12 = new TH3S("habla3s", "th3s title", 10, 2.1, 3.1, 5, 1.1, 2.1, 5, 1.1, 2.1);
    TH3I* hist13 = new TH3I("habla3i", "th3i title", 10, 2.1, 3.1, 5, 1.1, 2.1, 5, 1.1, 2.1);
    TH3D* hist14 = new TH3D("habla3d", "th3d title", 10, 2.1, 3.1, 5, 1.1, 2.1, 5, 1.1, 2.1);
    TH3F* hist15 = new TH3F("habla3f", "th3f title", 10, 2.1, 3.1, 5, 1.1, 2.1, 5, 1.1, 2.1);
    
    TObjString* comment = new TObjString("Hello World");
    comment->Write();
    
    TLorentzVector v2(1., 1., 1., 1.);
    v2.Write();
    
    TVector2 tvector2(5.0, 6.0);
    tvector2.Write();
    
    TProfile profile1("hprof","Profile of pz versus px",100,-4,4,0,20);
    profile1.Write();
    
    TProfile2D profile2("hprof2d","Profile of pz versus px and py",40,-4,4,40,-4,4,0,20);
    profile2.Write();
    
    TProfile3D profile3("hprof3d","Profile of pt versus px, py and pz",40,-4,4,40,-4,4,40,0,20);
    profile3.Write();
    
    std::vector<int> g1; 
    for (int i = 1; i <= 5; i++){ 
        g1.push_back(i); 
    }
    
    tfile -> Write();
    tfile -> Close();
}
