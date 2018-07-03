void empty()
{

    TFile *tfile = new TFile("empty.root", "RECREATE");
    tfile->SetCompressionLevel(0);
    
    tfile -> Close();
}