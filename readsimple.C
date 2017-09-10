#include "TFile.h"
#include "TTree.h"
#include "TBranch.h"
#include <ctime>
#include <sys/time.h>
#include <iostream>

double diff(struct timeval endTime, struct timeval startTime) {
  return (1000L * 1000L * (endTime.tv_sec - startTime.tv_sec) + (endTime.tv_usec - startTime.tv_usec)) / 1000.0 / 1000.0;
}

void readsimple() {
  struct timeval startTime, endTime;

  TFile* f = new TFile("/home/pivarski/storage/data/TrackResonanceNtuple_compressed.root");
  TTree* t;
  f->GetObject("twoMuon", t);

  gettimeofday(&startTime, 0);

  float mass_mumu;
  float px;
  float py;
  float pz;

  t->GetBranch("mass_mumu")->SetAddress(&mass_mumu);
  t->GetBranch("px")->SetAddress(&px);
  t->GetBranch("py")->SetAddress(&py);
  t->GetBranch("pz")->SetAddress(&pz);

  float total = 0.0;
  for (Long64_t i = 0;  i < t->GetEntries();  i++) {
    t->GetEntry(i);
    total += mass_mumu + px + py + pz;
  }

  printf("total %g\n", total);

  gettimeofday(&endTime, 0);
  std::cout << diff(endTime, startTime) << " sec" << std::endl;

  exit(0);
}
