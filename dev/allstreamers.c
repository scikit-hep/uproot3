void allstreamers(){
    TFile *tfile = new TFile("dev/allstreamers.root", "RECREATE");
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
    
    TTree *t = new TTree("tvec","Tree with vectors");
    
    int i1;
    double d1;
    float f1;
    Long64_t l1;
    char c1;
    short s1;
    bool b1;
    
    t -> Branch("intBranch", &i1);
    t -> Branch("doubleBranch", &d1);
    t -> Branch("floatBranch", &f1);
    t -> Branch("longBranch", &l1);
    t -> Branch("charBranch", &c1);
    t -> Branch("shortBranch", &s1);
    t -> Branch("boolBranch", &b1);
    
    std::vector<int> i2; 
    std::vector<double> d2;
    std::vector<float> f2;
    std::vector<long> l2;
    std::vector<char> c2;
    std::vector<short> s2;
    
    t -> Branch("intvector", &i2);
    t -> Branch("doublevector", &d2);
    t -> Branch("floatvector", &f2);
    t -> Branch("longVector", &l2);
    t -> Branch("charVector", &c2);
    t -> Branch("shortVector", &s2);

    char* s;
    // ? - Warning in <TBranch::TBranch>: Extra characters after type tag 'C/B' for branch 'character star/C'; must be one character.
    t -> Branch("character star/C", s);
    
    std::string a_string("blah");
    t -> Branch("str_branch_name", &a_string);
    
    std::vector<string> sample;
    t -> Branch("sample string", &sample);
    
    t -> Fill();
    t -> Write();
     
    TGraph g(10);
    g.Write();
    
    TMultiGraph *mg = new TMultiGraph();
    mg -> Write();
    
    tfile -> Write();
    tfile -> Close();
}
