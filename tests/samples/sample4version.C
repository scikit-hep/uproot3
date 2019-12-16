#include "TFile.h"
#include "TTree.h"
#include "TBranch.h"
#include "stdio.h"

void sample4version(const char* version, const char* compression) {
  char filename[200];
  TFile *f;

  if (strcmp(compression, "uncompressed") == 0) {
    sprintf(filename, "sample-%s-uncompressed.root", version);
    f = new TFile(filename, "RECREATE");
    f->SetCompressionAlgorithm(1);
    f->SetCompressionLevel(0);
  }
  else if (strcmp(compression, "zlib") == 0) {
    sprintf(filename, "sample-%s-zlib.root", version);
    f = new TFile(filename, "RECREATE");
    f->SetCompressionAlgorithm(1);
    f->SetCompressionLevel(4);
  }
  else if (strcmp(compression, "lzma") == 0) {
    sprintf(filename, "sample-%s-lzma.root", version);
    f = new TFile(filename, "RECREATE");
    f->SetCompressionAlgorithm(2);
    f->SetCompressionLevel(4);
  }
  else if (strcmp(compression, "lz4") == 0) {
    sprintf(filename, "sample-%s-lz4.root", version);
    f = new TFile(filename, "RECREATE");
    f->SetCompressionAlgorithm(4);
    f->SetCompressionLevel(4);
  }
  else if (strcmp(compression, "zstd") == 0) {
    sprintf(filename, "sample-%s-zstd.root", version);
    f = new TFile(filename, "RECREATE");
    f->SetCompressionAlgorithm(5);
    f->SetCompressionLevel(5);
  }
  else
    exit(-1);

  TTree *t = new TTree("sample", "");
  Int_t n;
  t->Branch("n", &n, "n/I", 50);

  Bool_t b;
  t->Branch("b", &b, "b/O", 50);
  Bool_t ab[3];
  t->Branch("ab", ab, "ab[3]/O", 50);
  Bool_t Ab[10];
  t->Branch("Ab", Ab, "Ab[n]/O", 50);

  Char_t i1;
  t->Branch("i1", &i1, "i1/B", 50);
  Char_t ai1[3];
  t->Branch("ai1", ai1, "ai1[3]/B", 50);
  Char_t Ai1[10];
  t->Branch("Ai1", Ai1, "Ai1[n]/B", 50);

  UChar_t u1;
  t->Branch("u1", &u1, "u1/b", 50);
  UChar_t au1[3];
  t->Branch("au1", au1, "au1[3]/b", 50);
  UChar_t Au1[10];
  t->Branch("Au1", Au1, "Au1[n]/b", 50);

  Short_t i2;
  t->Branch("i2", &i2, "i2/S", 50);
  Short_t ai2[3];
  t->Branch("ai2", ai2, "ai2[3]/S", 50);
  Short_t Ai2[10];
  t->Branch("Ai2", Ai2, "Ai2[n]/S", 50);

  UShort_t u2;
  t->Branch("u2", &u2, "u2/s", 50);
  UShort_t au2[3];
  t->Branch("au2", au2, "au2[3]/s", 50);
  UShort_t Au2[10];
  t->Branch("Au2", Au2, "Au2[n]/s", 50);

  Int_t i4;
  t->Branch("i4", &i4, "i4/I", 50);
  Int_t ai4[3];
  t->Branch("ai4", ai4, "ai4[3]/I", 50);
  Int_t Ai4[10];
  t->Branch("Ai4", Ai4, "Ai4[n]/I", 50);

  UInt_t u4;
  t->Branch("u4", &u4, "u4/i", 50);
  UInt_t au4[3];
  t->Branch("au4", au4, "au4[3]/i", 50);
  UInt_t Au4[10];
  t->Branch("Au4", Au4, "Au4[n]/i", 50);

  Long64_t i8;
  t->Branch("i8", &i8, "i8/L", 50);
  Long64_t ai8[3];
  t->Branch("ai8", ai8, "ai8[3]/L", 50);
  Long64_t Ai8[10];
  t->Branch("Ai8", Ai8, "Ai8[n]/L", 50);

  ULong64_t u8;
  t->Branch("u8", &u8, "u8/l", 50);
  ULong64_t au8[3];
  t->Branch("au8", au8, "au8[3]/l", 50);
  ULong64_t Au8[10];
  t->Branch("Au8", Au8, "Au8[n]/l", 50);

  float f4;
  t->Branch("f4", &f4, "f4/F", 50);
  float af4[3];
  t->Branch("af4", af4, "af4[3]/F", 50);
  float Af4[10];
  t->Branch("Af4", Af4, "Af4[n]/F", 50);

  double f8;
  t->Branch("f8", &f8, "f8/D", 50);
  double af8[3];
  t->Branch("af8", af8, "af8[3]/D", 50);
  double Af8[10];
  t->Branch("Af8", Af8, "Af8[n]/D", 50);

  char str[100];
  t->Branch("str", &str, "str/C", 150);

  for (int i = 0;  i < 30;  i++) {
    n = (i % 5);

    for (int j = 0;  j < n + 1;  j++) {
      b = (i % 2 == 0);
      ab[0] = (i % 2 == 1);
      ab[1] = (i % 2 == 0);
      ab[2] = (i % 2 == 1);
      Ab[n] = ((i + j) % 2 == 0);

      i1 = i - 15;
      ai1[0] = i - 14;
      ai1[1] = i - 13;
      ai1[2] = i - 12;
      Ai1[n] = i - 15 + j;

      u1 = i;
      au1[0] = i + 1;
      au1[1] = i + 2;
      au1[2] = i + 3;
      Au1[n] = i + j;

      i2 = i - 15;
      ai2[0] = i - 14;
      ai2[1] = i - 13;
      ai2[2] = i - 12;
      Ai2[n] = i - 15 + j;

      u2 = i;
      au2[0] = i + 1;
      au2[1] = i + 2;
      au2[2] = i + 3;
      Au2[n] = i + j;

      i4 = i - 15;
      ai4[0] = i - 14;
      ai4[1] = i - 13;
      ai4[2] = i - 12;
      Ai4[n] = i - 15 + j;

      u4 = i;
      au4[0] = i + 1;
      au4[1] = i + 2;
      au4[2] = i + 3;
      Au4[n] = i + j;

      i8 = i - 15;
      ai8[0] = i - 14;
      ai8[1] = i - 13;
      ai8[2] = i - 12;
      Ai8[n] = i - 15 + j;

      u8 = i;
      au8[0] = i + 1;
      au8[1] = i + 2;
      au8[2] = i + 3;
      Au8[n] = i + j;

      f4 = i - 14.9;
      af4[0] = i - 13.9;
      af4[1] = i - 12.9;
      af4[2] = i - 11.9;
      Af4[n] = i - 15.0 + j*0.1;

      f8 = i - 14.9;
      af8[0] = i - 13.9;
      af8[1] = i - 12.9;
      af8[2] = i - 11.9;
      Af8[n] = i - 15.0 + j*0.1;

      sprintf(str, "hey-%d", i);
    }

    t->Fill();
  }

  t->Write();
  f->Close();

  exit(0);
}
