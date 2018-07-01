#include <TFile.h>
#include <stdio.h>

void dummy()
{
// Create a new ROOT file to contain TObjString

    TFile *tfile = new TFile("dummy.root", "RECREATE");
    Char_t  large_str[1];

    TObjString  Comment;
    large_str[0] = '\0';
    //sprintf(large_str, "testing TObjString");
    Comment.SetString(large_str);
    Comment.Write();
    tfile -> Write("Comment");

    tfile -> Close();
}