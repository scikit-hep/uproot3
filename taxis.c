#include <TFile.h>
#include <stdio.h>
#include <TAxis.h>

void taxis()
{
// Create a new ROOT file to contain TAxis

    TFile *tfile = new TFile("taxis.root", "RECREATE");
    tfile->SetCompressionLevel(0);

	TAxis axis(5, 1.0, 2.0);
	axis.SetName("hi");
	axis.Write();
    
    tfile -> Close();
}
