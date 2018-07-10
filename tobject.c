#include <TFile.h>
#include <stdio.h>
#include <TObject.h>

void tobject()
{
// Create a new ROOT file to contain TObjString

    TFile *tfile = new TFile("tobject.root", "RECREATE");
    tfile->SetCompressionLevel(0);

    TObject *object = new TObject;
	object -> Write(0, 1, 0);
    
    tfile -> Close();
	tfile -> ls();
}
