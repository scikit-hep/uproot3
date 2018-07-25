#include <TFile.h>
#include <stdio.h>
#include <TString.h>

void dummy2()
{
// Create a new ROOT file to contain TObjString

    TFile *tfile = new TFile("dummy2.root", "RECREATE");
    tfile->SetCompressionLevel(0);

    TObjString  Comment1("Hello World");
	TObjString  Comment2("Pratyush");
	
    Comment1.Write();
	Comment2.Write();
    
    tfile -> Close();
}
