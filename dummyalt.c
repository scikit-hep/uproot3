#include <TFile.h>
#include <stdio.h>
#include <TString.h>

void dummyalt()
{
// Create a new ROOT file to contain TObjString

    TFile *tfile = new TFile("dummyalt.root", "RECREATE");
    tfile->SetCompressionLevel(0);

    TObjString  Comment("Hello");
	
    Comment.Write();
    
    tfile -> Close();
}
