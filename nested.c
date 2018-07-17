
void nested(){
	TFile *tfile = new TFile("nested.root", "RECREATE");
	tfile -> SetCompressionLevel(0);

	TDirectory *cdtof = tfile -> mkdir("tof");
	cdtof -> cd();
	
	TDirectory *into = cdtof -> mkdir("in");
	
	tfile -> Close();
}
