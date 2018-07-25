#include <TFile.h>
#include <stdio.h>
#include <TString.h>

void dummy()
{
// Create a new ROOT file to contain TObjString

    TFile *tfile = new TFile("dummy.root", "RECREATE");
    tfile->SetCompressionLevel(0);

    TObjString  Comment("Hello World");
	
    Comment.Write();
    
    tfile -> Close();
}
