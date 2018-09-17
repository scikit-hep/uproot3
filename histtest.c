
void histtest(){
    TFile *tfile = new TFile("histtest.root", "RECREATE");
    tfile->SetCompressionLevel(0);
    
    TH1F* hist = new TH1F("th1f name", "th1f title", 10, 2.1, 3.1);
    hist->AddBinContent(1, 6);
    hist->AddBinContent(2, 3);
    hist->AddBinContent(3, 5);
    hist->AddBinContent(4, 7);
    hist->AddBinContent(5, 4);
    hist->AddBinContent(6, 2);
    hist->AddBinContent(7, 10);
    hist->AddBinContent(8, 5);
    hist->AddBinContent(9, 5);
    hist->AddBinContent(10, 1);
    
    tfile -> Write();
    tfile -> Close();
}