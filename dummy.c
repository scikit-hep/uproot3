#include <TFile.h>
#include <stdio.h>
#include <TString.h>

void dummy()
{
// Create a new ROOT file to contain TObjString

    TFile *tfile = new TFile("dummy.root", "RECREATE");
    tfile->SetCompressionLevel(0);

    TObjString  Comment("Hello World");
    printf(">>>%s<<<", Comment.GetName());
    printf(">>>%s<<<", Comment.GetString().Data());

    Comment.Write();
    
    tfile -> Close();
}
