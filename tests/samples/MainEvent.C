#ifndef ROOT_Event
#define ROOT_Event

//////////////////////////////////////////////////////////////////////////
//                                                                      //
// Event                                                                //
//                                                                      //
// Description of the event and track parameters                        //
//                                                                      //
//////////////////////////////////////////////////////////////////////////

#include "TObject.h"
#include "TClonesArray.h"
#include "TRefArray.h"
#include "TRef.h"
#include "TH1.h"
#include "TBits.h"
#include "TMath.h"


class TDirectory;

class Track : public TObject {

private:
   Float_t      fPx;           //X component of the momentum
   Float_t      fPy;           //Y component of the momentum
   Float_t      fPz;           //Z component of the momentum
   Float_t      fRandom;       //A random track quantity
   Float16_t    fMass2;        //[0,0,8] The mass square of this particle
   Float16_t    fBx;           //[0,0,10] X intercept at the vertex
   Float16_t    fBy;           //[0,0,10] Y intercept at the vertex
   Float_t      fMeanCharge;   //Mean charge deposition of all hits of this track
   Float16_t    fXfirst;       //X coordinate of the first point
   Float16_t    fXlast;        //X coordinate of the last point
   Float16_t    fYfirst;       //Y coordinate of the first point
   Float16_t    fYlast;        //Y coordinate of the last point
   Float16_t    fZfirst;       //Z coordinate of the first point
   Float16_t    fZlast;        //Z coordinate of the last point
   Double32_t   fCharge;       //[-1,1,2] Charge of this track
   Double32_t   fVertex[3];    //[-30,30,16] Track vertex position
   Int_t        fNpoint;       //Number of points for this track
   Short_t      fValid;        //Validity criterion
   Int_t        fNsp;          //Number of points for this track with a special value
   Double32_t*  fPointValue;   //[fNsp][0,3] a special quantity for some point.
   TBits        fTriggerBits;  //Bits triggered by this track.

public:
   Track() : fTriggerBits(64) { fNsp = 0; fPointValue = 0; }
   Track(const Track& orig);
   Track(Float_t random);
   virtual ~Track() {Clear(); delete [] fPointValue; fPointValue = nullptr; }
   Track &operator=(const Track &orig);

   void          Set(Float_t random);
   void          Clear(Option_t *option="");
   Float_t       GetPx() const { return fPx; }
   Float_t       GetPy() const { return fPy; }
   Float_t       GetPz() const { return fPz; }
   Float_t       GetPt() const { return TMath::Sqrt(fPx*fPx + fPy*fPy); }
   Float_t       GetRandom() const { return fRandom; }
   Float_t       GetBx() const { return fBx; }
   Float_t       GetBy() const { return fBy; }
   Float_t       GetMass2() const { return fMass2; }
   Float_t       GetMeanCharge() const { return fMeanCharge; }
   Float_t       GetXfirst() const { return fXfirst; }
   Float_t       GetXlast()  const { return fXlast; }
   Float_t       GetYfirst() const { return fYfirst; }
   Float_t       GetYlast()  const { return fYlast; }
   Float_t       GetZfirst() const { return fZfirst; }
   Float_t       GetZlast()  const { return fZlast; }
   Double32_t    GetCharge() const { return fCharge; }
   Double32_t    GetVertex(Int_t i=0) {return (i<3)?fVertex[i]:0;}
   Int_t         GetNpoint() const { return fNpoint; }
   TBits&        GetTriggerBits() { return fTriggerBits; }
   Short_t       GetValid()  const { return fValid; }
   virtual void  SetValid(Int_t valid=1) { fValid = valid; }
   Int_t         GetN() const { return fNsp; }
   Double32_t    GetPointValue(Int_t i=0) const { return (i<fNsp)?fPointValue[i]:0; }

   ClassDef(Track,2)  //A track segment
};

class EventHeader {

private:
   Int_t   fEvtNum;
   Int_t   fRun;
   Int_t   fDate;

public:
   EventHeader() : fEvtNum(0), fRun(0), fDate(0) { }
   virtual ~EventHeader() { }
   void   Set(Int_t i, Int_t r, Int_t d) { fEvtNum = i; fRun = r; fDate = d; }
   Int_t  GetEvtNum() const { return fEvtNum; }
   Int_t  GetRun() const { return fRun; }
   Int_t  GetDate() const { return fDate; }

   ClassDef(EventHeader,1)  //Event Header
};


class Event : public TObject {

private:
   char           fType[20];          //event type
   char          *fEventName;         //run+event number in character format
   Int_t          fNtrack;            //Number of tracks
   Int_t          fNseg;              //Number of track segments
   Int_t          fNvertex;
   UInt_t         fFlag;
   Double32_t     fTemperature;
   Int_t          fMeasures[10];
   Double32_t     fMatrix[4][4];
   Double32_t    *fClosestDistance;   //[fNvertex][0,0,6]
   EventHeader    fEvtHdr;
   TClonesArray  *fTracks;            //->array with all tracks
   TRefArray     *fHighPt;            //array of High Pt tracks only
   TRefArray     *fMuons;             //array of Muon tracks only
   TRef           fLastTrack;         //reference pointer to last track
   TRef           fWebHistogram;      //EXEC:GetWebHistogram reference to an histogram in a TWebFile
   TH1F          *fH;                 //->
   TBits          fTriggerBits;       //Bits triggered by this event.
   Bool_t         fIsValid;           //

   static TClonesArray *fgTracks;
   static TH1F         *fgHist;

   Event(const Event&) = delete;
   Event &operator=(const Event&) = delete;

public:
   Event();
   virtual ~Event();
   void          Build(Int_t ev, Int_t arg5=600, Float_t ptmin=1);
   void          Clear(Option_t *option ="");
   Bool_t        IsValid() const { return fIsValid; }
   static void   Reset(Option_t *option ="");
   void          ResetHistogramPointer() {fH=0;}
   void          SetNseg(Int_t n) { fNseg = n; }
   void          SetNtrack(Int_t n) { fNtrack = n; }
   void          SetNvertex(Int_t n) { fNvertex = n; SetRandomVertex(); }
   void          SetFlag(UInt_t f) { fFlag = f; }
   void          SetTemperature(Double32_t t) { fTemperature = t; }
   void          SetType(char *type) {strcpy(fType,type);}
   void          SetHeader(Int_t i, Int_t run, Int_t date, Float_t random);
   Track        *AddTrack(Float_t random, Float_t ptmin=1);
   void          SetMeasure(UChar_t which, Int_t what);
   void          SetMatrix(UChar_t x, UChar_t y, Double32_t what) { if (x<3&&y<3) fMatrix[x][y]=what;}
   void          SetRandomVertex();

   Float_t       GetClosestDistance(Int_t i) {return fClosestDistance[i];}
   char         *GetType() {return fType;}
   Int_t         GetNtrack() const { return fNtrack; }
   Int_t         GetNseg() const { return fNseg; }
   Int_t         GetNvertex() const { return fNvertex; }
   UInt_t        GetFlag() const { return fFlag; }
   Double32_t    GetTemperature() const { return fTemperature; }
   EventHeader  *GetHeader() { return &fEvtHdr; }
   TClonesArray *GetTracks() const {return fTracks;}
   TRefArray    *GetHighPt() const {return fHighPt;}
   TRefArray    *GetMuons()  const {return fMuons;}
   Track        *GetLastTrack() const {return (Track*)fLastTrack.GetObject();}
   TH1F         *GetHistogram() const {return fH;}
   TH1          *GetWebHistogram()  const {return (TH1*)fWebHistogram.GetObject();}
   Int_t         GetMeasure(UChar_t which) { return (which<10)?fMeasures[which]:0; }
   Double32_t    GetMatrix(UChar_t x, UChar_t y) { return (x<4&&y<4)?fMatrix[x][y]:0; }
   TBits&        GetTriggerBits() { return fTriggerBits; }

   ClassDef(Event,1)  //Event structure
};


class HistogramManager {

private:
   TH1F  *fNtrack;
   TH1F  *fNseg;
   TH1F  *fTemperature;
   TH1F  *fPx;
   TH1F  *fPy;
   TH1F  *fPz;
   TH1F  *fRandom;
   TH1F  *fMass2;
   TH1F  *fBx;
   TH1F  *fBy;
   TH1F  *fMeanCharge;
   TH1F  *fXfirst;
   TH1F  *fXlast;
   TH1F  *fYfirst;
   TH1F  *fYlast;
   TH1F  *fZfirst;
   TH1F  *fZlast;
   TH1F  *fCharge;
   TH1F  *fNpoint;
   TH1F  *fValid;

public:
   HistogramManager(TDirectory *dir);
   virtual ~HistogramManager();

   void Hfill(Event *event);

   ClassDef(HistogramManager,1)  //Manages all histograms
};

#endif
// @(#)root/test:$Id$
// Author: Rene Brun   19/08/96

////////////////////////////////////////////////////////////////////////
//
//                       Event and Track classes
//                       =======================
//
//  The Event class is a naive/simple example of an event structure.
//     public:
//        char           fType[20];
//        char          *fEventName;         //run+event number in character format
//        Int_t          fNtrack;
//        Int_t          fNseg;
//        Int_t          fNvertex;
//        UInt_t         fFlag;
//        Double32_t     fTemperature;
//        Int_t          fMeasures[10];
//        Double32_t     fMatrix[4][4];
//        Double32_t    *fClosestDistance; //[fNvertex] indexed array!
//        EventHeader    fEvtHdr;
//        TClonesArray  *fTracks;
//        TRefArray     *fHighPt;            //array of High Pt tracks only
//        TRefArray     *fMuons;             //array of Muon tracks only
//        TRef           fLastTrack;         //pointer to last track
//        TRef           fHistoWeb;          //EXEC:GetHistoWeb reference to an histogram in a TWebFile
//        TH1F          *fH;
//        TBits          fTriggerBits;       //Bits triggered by this event.
//
//   The EventHeader class has 3 data members (integers):
//     public:
//        Int_t          fEvtNum;
//        Int_t          fRun;
//        Int_t          fDate;
//
//
//   The Event data member fTracks is a pointer to a TClonesArray.
//   It is an array of a variable number of tracks per event.
//   Each element of the array is an object of class Track with the members:
//     private:
//        Float_t      fPx;           //X component of the momentum
//        Float_t      fPy;           //Y component of the momentum
//        Float_t      fPz;           //Z component of the momentum
//        Float_t      fRandom;       //A random track quantity
//        Float_t      fMass2;        //The mass square of this particle
//        Float_t      fBx;           //X intercept at the vertex
//        Float_t      fBy;           //Y intercept at the vertex
//        Float_t      fMeanCharge;   //Mean charge deposition of all hits of this track
//        Float_t      fXfirst;       //X coordinate of the first point
//        Float_t      fXlast;        //X coordinate of the last point
//        Float_t      fYfirst;       //Y coordinate of the first point
//        Float_t      fYlast;        //Y coordinate of the last point
//        Float_t      fZfirst;       //Z coordinate of the first point
//        Float_t      fZlast;        //Z coordinate of the last point
//        Double32_t   fCharge;       //Charge of this track
//        Double32_t   fVertex[3];    //Track vertex position
//        Int_t        fNpoint;       //Number of points for this track
//        Short_t      fValid;        //Validity criterion
//        Int_t        fNsp;          //Number of points for this track with a special value
//        Double32_t  *fPointValue;   //[fNsp] a special quantity for some point.
//        TBits        fTriggerBits;  //Bits triggered by this track.
//
//   An example of a batch program to use the Event/Track classes is given
//   in this directory: MainEvent.
//   Look also in the same directory at the following macros:
//     - eventa.C  an example how to read the tree
//     - eventb.C  how to read events conditionally
//
//   During the processing of the event (optionally) also a large number
//   of histograms can be filled. The creation and handling of the
//   histograms is taken care of by the HistogramManager class.
//
//   Note:  This version of the class Event (see EventMT.h and EventMT.cxx
//   for an alternative) uses static variables to improve performance (by
//   reducing the number of memory allocations).  Consequently, only one
//   instance of the class Event should be in use at a time (a 2nd instance
//   would share the array of Tracks with the first instance).
//
////////////////////////////////////////////////////////////////////////

#include "RVersion.h"
#include "TRandom.h"
#include "TDirectory.h"
#include "TProcessID.h"

#include "Event.h"


ClassImp(EventHeader);
ClassImp(Event);
ClassImp(Track);
ClassImp(HistogramManager);

TClonesArray *Event::fgTracks = 0;
TH1F *Event::fgHist = 0;

////////////////////////////////////////////////////////////////////////////////
/// Create an Event object.
/// When the constructor is invoked for the first time, the class static
/// variable fgTracks is 0 and the TClonesArray fgTracks is created.

Event::Event() : fIsValid(kFALSE)
{
   if (!fgTracks) fgTracks = new TClonesArray("Track", 1000);
   fTracks = fgTracks;
   fHighPt = new TRefArray;
   fMuons  = new TRefArray;
   fNtrack = 0;
   fH      = 0;
   Int_t i0,i1;
   for (i0 = 0; i0 < 4; i0++) {
      for (i1 = 0; i1 < 4; i1++) {
         fMatrix[i0][i1] = 0.0;
      }
   }
   for (i0 = 0; i0 <10; i0++) fMeasures[i0] = 0;
   for (i0 = 0; i0 <20; i0++) fType[i0] = 0;
   fClosestDistance = 0;
   fEventName = 0;
   fWebHistogram.SetAction(this);
}

////////////////////////////////////////////////////////////////////////////////

Event::~Event()
{
   Clear();
   if (fH == fgHist) fgHist = 0;
   delete fH; fH = 0;
   delete fHighPt; fHighPt = 0;
   delete fMuons;  fMuons = 0;
   delete [] fClosestDistance;
   if (fEventName) delete [] fEventName;
}

////////////////////////////////////////////////////////////////////////////////

void Event::Build(Int_t ev, Int_t arg5, Float_t ptmin) {
  fIsValid = kTRUE;
  char etype[20];
  Float_t sigmat, sigmas;
  gRandom->Rannor(sigmat,sigmas);
  Int_t ntrack   = Int_t(arg5 +arg5*sigmat/120.);
  Float_t random = gRandom->Rndm();

  //Save current Object count
  Int_t ObjectNumber = TProcessID::GetObjectCount();
  Clear();
  fHighPt->Delete();
  fMuons->Delete();

  Int_t nch = 15;
  if (ev >= 100)   nch += 3;
  if (ev >= 10000) nch += 3;
  if (fEventName) delete [] fEventName;
  fEventName = new char[nch];
  snprintf(fEventName,nch,"Event%d_Run%d",ev,200);
  snprintf(etype,20,"type%d",ev%5);
  SetType(etype);
  SetHeader(ev, 200, 960312, random);
  SetNseg(Int_t(10*ntrack+20*sigmas));
  SetNvertex(Int_t(1+20*gRandom->Rndm()));
  SetFlag(UInt_t(random+0.5));
  SetTemperature(random+20.);

  for(UChar_t m = 0; m < 10; m++) {
     SetMeasure(m, Int_t(gRandom->Gaus(m,m+1)));
  }
  for(UChar_t i0 = 0; i0 < 4; i0++) {
    for(UChar_t i1 = 0; i1 < 4; i1++) {
       SetMatrix(i0,i1,gRandom->Gaus(i0*i1,1));
    }
  }

  fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));
  fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));
  fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));

  //  Create and Fill the Track objects
  for (Int_t t = 0; t < ntrack; t++) AddTrack(random,ptmin);

  //Restore Object count
  //To save space in the table keeping track of all referenced objects
  //we assume that our events do not address each other. We reset the
  //object count to what it was at the beginning of the event.
  TProcessID::SetObjectCount(ObjectNumber);
}

////////////////////////////////////////////////////////////////////////////////
/// Add a new track to the list of tracks for this event.
/// To avoid calling the very time consuming operator new for each track,
/// the standard but not well know C++ operator "new with placement"
/// is called. If tracks[i] is 0, a new Track object will be created
/// otherwise the previous Track[i] will be overwritten.

Track *Event::AddTrack(Float_t random, Float_t ptmin)
{
#if ROOT_VERSION_CODE >= ROOT_VERSION(5,32,0)
   Track *track = (Track*)fTracks->ConstructedAt(fNtrack++);
   track->Set(random);
#else
   TClonesArray &tracks = *fTracks;
   Track *track = new(tracks[fNtrack++]) Track(random);
#endif
   //Save reference to last Track in the collection of Tracks
   fLastTrack = track;
   //Save reference in fHighPt if track is a high Pt track
   if (track->GetPt() > ptmin)   fHighPt->Add(track);
   //Save reference in fMuons if track is a muon candidate
   if (track->GetMass2() < 0.11) fMuons->Add(track);
   return track;
}

////////////////////////////////////////////////////////////////////////////////

void Event::Clear(Option_t * /*option*/)
{
   fTracks->Clear("C"); //will also call Track::Clear
   fHighPt->Delete();
   fMuons->Delete();
   fTriggerBits.Clear();
}

////////////////////////////////////////////////////////////////////////////////
/// Static function to reset all static objects for this event
///   fgTracks->Delete(option);

void Event::Reset(Option_t * /*option*/)
{
   delete fgTracks; fgTracks = 0;
   fgHist   = 0;
}

////////////////////////////////////////////////////////////////////////////////

void Event::SetHeader(Int_t i, Int_t run, Int_t date, Float_t random)
{
   fNtrack = 0;
   fEvtHdr.Set(i, run, date);
   if (!fgHist) fgHist = new TH1F("hstat","Event Histogram",100,0,1);
   fH = fgHist;
   fH->Fill(random);
}

////////////////////////////////////////////////////////////////////////////////

void Event::SetMeasure(UChar_t which, Int_t what) {
   if (which<10) fMeasures[which] = what;
}

////////////////////////////////////////////////////////////////////////////////
/// This delete is to test the relocation of variable length array

void Event::SetRandomVertex() {
   if (fClosestDistance) delete [] fClosestDistance;
   if (!fNvertex) {
      fClosestDistance = 0;
      return;
   }
   fClosestDistance = new Double32_t[fNvertex];
   for (Int_t k = 0; k < fNvertex; k++ ) {
      fClosestDistance[k] = gRandom->Gaus(1,1);
   }
}

////////////////////////////////////////////////////////////////////////////////
/// Copy a track object

Track::Track(const Track &orig) : TObject(orig),fTriggerBits(orig.fTriggerBits)
{
   fPx = orig.fPx;
   fPy = orig.fPy;
   fPz = orig.fPx;
   fRandom = orig.fRandom;
   fMass2 = orig.fMass2;
   fBx = orig.fBx;
   fBy = orig.fBy;
   fMeanCharge = orig.fMeanCharge;
   fXfirst = orig.fXfirst;
   fXlast  = orig.fXlast;
   fYfirst = orig.fYfirst;
   fYlast  = orig.fYlast;
   fZfirst = orig.fZfirst;
   fZlast  = orig.fZlast;
   fCharge = orig.fCharge;

   fVertex[0] = orig.fVertex[0];
   fVertex[1] = orig.fVertex[1];
   fVertex[2] = orig.fVertex[2];
   fNpoint = orig.fNpoint;
   fNsp = orig.fNsp;
   if (fNsp) {
      fPointValue = new Double32_t[fNsp];
      for(int i=0; i<fNsp; i++) {
         fPointValue[i] = orig.fPointValue[i];
      }
   } else {
      fPointValue = 0;
   }
   fValid  = orig.fValid;
}

////////////////////////////////////////////////////////////////////////////////
/// Create a track object.
/// Note that in this example, data members do not have any physical meaning.

Track::Track(Float_t random) : TObject(),fTriggerBits(64)
{
   Float_t a,b,px,py;
   gRandom->Rannor(px,py);
   fPx = px;
   fPy = py;
   fPz = TMath::Sqrt(px*px+py*py);
   fRandom = 1000*random;
   if (fRandom < 10) fMass2 = 0.106;
   else if (fRandom < 100) fMass2 = 0.8;
   else if (fRandom < 500) fMass2 = 4.5;
   else if (fRandom < 900) fMass2 = 8.9;
   else  fMass2 = 9.8;
   gRandom->Rannor(a,b);
   fBx = 0.1*a;
   fBy = 0.1*b;
   fMeanCharge = 0.01*gRandom->Rndm();
   gRandom->Rannor(a,b);
   fXfirst = a*10;
   fXlast  = b*10;
   gRandom->Rannor(a,b);
   fYfirst = a*12;
   fYlast  = b*16;
   gRandom->Rannor(a,b);
   fZfirst = 50 + 5*a;
   fZlast  = 200 + 10*b;
   fCharge = Double32_t(Int_t(3*gRandom->Rndm()) - 1);

   fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));
   fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));
   fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));

   fVertex[0] = gRandom->Gaus(0,0.1);
   fVertex[1] = gRandom->Gaus(0,0.2);
   fVertex[2] = gRandom->Gaus(0,10);
   fNpoint = Int_t(60+10*gRandom->Rndm());
   fNsp = Int_t(3*gRandom->Rndm());
   if (fNsp) {
      fPointValue = new Double32_t[fNsp];
      for(int i=0; i<fNsp; i++) {
         fPointValue[i] = i+1;
      }
   } else {
      fPointValue = 0;
   }
   fValid  = Int_t(0.6+gRandom->Rndm());
}

////////////////////////////////////////////////////////////////////////////////
/// Copy a track

Track &Track::operator=(const Track &orig)
{
   TObject::operator=(orig);
   fPx = orig.fPx;
   fPy = orig.fPy;
   fPz = orig.fPx;
   fRandom = orig.fRandom;
   fMass2 = orig.fMass2;
   fBx = orig.fBx;
   fBy = orig.fBy;
   fMeanCharge = orig.fMeanCharge;
   fXfirst = orig.fXfirst;
   fXlast  = orig.fXlast;
   fYfirst = orig.fYfirst;
   fYlast  = orig.fYlast;
   fZfirst = orig.fZfirst;
   fZlast  = orig.fZlast;
   fCharge = orig.fCharge;

   fVertex[0] = orig.fVertex[0];
   fVertex[1] = orig.fVertex[1];
   fVertex[2] = orig.fVertex[2];
   fNpoint = orig.fNpoint;
   if (fNsp > orig.fNsp) {
      fNsp = orig.fNsp;
      if (fNsp == 0) {
         delete [] fPointValue;
         fPointValue = 0;
      } else {
         for(int i=0; i<fNsp; i++) {
            fPointValue[i] = orig.fPointValue[i];
         }
      }
   } else {
      if (fNsp) {
         delete [] fPointValue;
      }
      fNsp = orig.fNsp;
      if (fNsp) {
         fPointValue = new Double32_t[fNsp];
         for(int i=0; i<fNsp; i++) {
            fPointValue[i] = orig.fPointValue[i];
         }
      } else {
         fPointValue = 0;
      }
   }
   fValid  = orig.fValid;

   fTriggerBits = orig.fTriggerBits;

   return *this;
}

////////////////////////////////////////////////////////////////////////////////
/// Note that we intend on using TClonesArray::ConstructedAt, so we do not
/// need to delete any of the arrays.

void Track::Clear(Option_t * /*option*/)
{
   TObject::Clear();
   fTriggerBits.Clear();
}

////////////////////////////////////////////////////////////////////////////////
/// Set the values of the Track data members.

void Track::Set(Float_t random)
{
   Float_t a,b,px,py;
   gRandom->Rannor(px,py);
   fPx = px;
   fPy = py;
   fPz = TMath::Sqrt(px*px+py*py);
   fRandom = 1000*random;
   if (fRandom < 10) fMass2 = 0.106;
   else if (fRandom < 100) fMass2 = 0.8;
   else if (fRandom < 500) fMass2 = 4.5;
   else if (fRandom < 900) fMass2 = 8.9;
   else  fMass2 = 9.8;
   gRandom->Rannor(a,b);
   fBx = 0.1*a;
   fBy = 0.1*b;
   fMeanCharge = 0.01*gRandom->Rndm();
   gRandom->Rannor(a,b);
   fXfirst = a*10;
   fXlast  = b*10;
   gRandom->Rannor(a,b);
   fYfirst = a*12;
   fYlast  = b*16;
   gRandom->Rannor(a,b);
   fZfirst = 50 + 5*a;
   fZlast  = 200 + 10*b;
   fCharge = Double32_t(Int_t(3*gRandom->Rndm()) - 1);

   fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));
   fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));
   fTriggerBits.SetBitNumber((UInt_t)(64*gRandom->Rndm()));

   fVertex[0] = gRandom->Gaus(0,0.1);
   fVertex[1] = gRandom->Gaus(0,0.2);
   fVertex[2] = gRandom->Gaus(0,10);
   fNpoint = Int_t(60+10*gRandom->Rndm());
   Int_t newNsp = Int_t(3*gRandom->Rndm());
   if (fNsp > newNsp) {
      fNsp = newNsp;
      if (fNsp == 0) {
         delete [] fPointValue;
         fPointValue = 0;
      } else {
         for(int i=0; i<fNsp; i++) {
            fPointValue[i] = i+1;
         }
      }

   } else {
      if (fNsp) {
         delete [] fPointValue;
      }
      fNsp = newNsp;
      if (fNsp) {
         fPointValue = new Double32_t[fNsp];
         for(int i=0; i<fNsp; i++) {
            fPointValue[i] = i+1;
         }
      } else {
         fPointValue = 0;
      }
   }
   fValid  = Int_t(0.6+gRandom->Rndm());
}

////////////////////////////////////////////////////////////////////////////////
/// Create histogram manager object. Histograms will be created
/// in the "dir" directory.

HistogramManager::HistogramManager(TDirectory *dir)
{
   // Save current directory and cd to "dir".
   TDirectory *saved = gDirectory;
   dir->cd();

   fNtrack      = new TH1F("hNtrack",    "Ntrack",100,575,625);
   fNseg        = new TH1F("hNseg",      "Nseg",100,5800,6200);
   fTemperature = new TH1F("hTemperature","Temperature",100,19.5,20.5);
   fPx          = new TH1F("hPx",        "Px",100,-4,4);
   fPy          = new TH1F("hPy",        "Py",100,-4,4);
   fPz          = new TH1F("hPz",        "Pz",100,0,5);
   fRandom      = new TH1F("hRandom",    "Random",100,0,1000);
   fMass2       = new TH1F("hMass2",     "Mass2",100,0,12);
   fBx          = new TH1F("hBx",        "Bx",100,-0.5,0.5);
   fBy          = new TH1F("hBy",        "By",100,-0.5,0.5);
   fMeanCharge  = new TH1F("hMeanCharge","MeanCharge",100,0,0.01);
   fXfirst      = new TH1F("hXfirst",    "Xfirst",100,-40,40);
   fXlast       = new TH1F("hXlast",     "Xlast",100,-40,40);
   fYfirst      = new TH1F("hYfirst",    "Yfirst",100,-40,40);
   fYlast       = new TH1F("hYlast",     "Ylast",100,-40,40);
   fZfirst      = new TH1F("hZfirst",    "Zfirst",100,0,80);
   fZlast       = new TH1F("hZlast",     "Zlast",100,0,250);
   fCharge      = new TH1F("hCharge",    "Charge",100,-1.5,1.5);
   fNpoint      = new TH1F("hNpoint",    "Npoint",100,50,80);
   fValid       = new TH1F("hValid",     "Valid",100,0,1.2);

   // cd back to original directory
   saved->cd();
}

////////////////////////////////////////////////////////////////////////////////
/// Clean up all histograms.

HistogramManager::~HistogramManager()
{
   // Nothing to do. Histograms will be deleted when the directory
   // in which tey are stored is closed.
}

////////////////////////////////////////////////////////////////////////////////
/// Fill histograms.

void HistogramManager::Hfill(Event *event)
{
   fNtrack->Fill(event->GetNtrack());
   fNseg->Fill(event->GetNseg());
   fTemperature->Fill(event->GetTemperature());

   for (Int_t itrack = 0; itrack < event->GetNtrack(); itrack++) {
      Track *track = (Track*)event->GetTracks()->UncheckedAt(itrack);
      fPx->Fill(track->GetPx());
      fPy->Fill(track->GetPy());
      fPz->Fill(track->GetPz());
      fRandom->Fill(track->GetRandom());
      fMass2->Fill(track->GetMass2());
      fBx->Fill(track->GetBx());
      fBy->Fill(track->GetBy());
      fMeanCharge->Fill(track->GetMeanCharge());
      fXfirst->Fill(track->GetXfirst());
      fXlast->Fill(track->GetXlast());
      fYfirst->Fill(track->GetYfirst());
      fYlast->Fill(track->GetYlast());
      fZfirst->Fill(track->GetZfirst());
      fZlast->Fill(track->GetZlast());
      fCharge->Fill(track->GetCharge());
      fNpoint->Fill(track->GetNpoint());
      fValid->Fill(track->GetValid());
   }
}
// @(#)root/test:$Id$
// Author: Rene Brun   19/01/97

////////////////////////////////////////////////////////////////////////
//
//             A simple example with a ROOT tree
//             =================================
//
//  This program creates :
//    - a ROOT file
//    - a tree
//  Additional arguments can be passed to the program to control the flow
//  of execution. (see comments describing the arguments in the code).
//      Event  nevent comp split fill tracks IMT compression
//  All arguments are optional. Default is:
//      Event  400      1    1     1     400   0           1
//
//  In this example, the tree consists of one single "super branch"
//  The statement ***tree->Branch("event", &event, 64000,split);*** below
//  will parse the structure described in Event.h and will make
//  a new branch for each data member of the class if split is set to 1.
//    - 9 branches corresponding to the basic types fType, fNtrack,fNseg,
//           fNvertex,fFlag,fTemperature,fMeasures,fMatrix,fClosesDistance.
//    - 3 branches corresponding to the members of the subobject EventHeader.
//    - one branch for each data member of the class Track of TClonesArray.
//    - one branch for the TRefArray of high Pt tracks
//    - one branch for the TRefArray of muon tracks
//    - one branch for the reference pointer to the last track
//    - one branch for the object fH (histogram of class TH1F).
//
//  if split = 0 only one single branch is created and the complete event
//  is serialized in one single buffer.
//  if split = -2 the event is split using the old TBranchObject mechanism
//  if split = -1 the event is streamed using the old TBranchObject mechanism
//  if split > 0  the event is split using the new TBranchElement mechanism.
//
//  if comp = 0 no compression at all.
//  if comp = 1 event is compressed.
//  if comp = 2 same as 1. In addition branches with floats in the TClonesArray
//                         are also compressed.
//  The 4th argument fill can be set to 0 if one wants to time
//     the percentage of time spent in creating the event structure and
//     not write the event in the file.
//  The 5th argument will enable IMT mode (Implicit Multi-Threading), allowing
//  ROOT to use multiple threads internally, if enabled.
//  The 6th argument allows the user to specify the compression algorithm:
//  - 1 - zlib.
//  - 2 - LZMA.
//  - 3 - "old ROOT algorithm"  A variant of zlib; do not use, kept for
//        backwards compatability.
//  - 4 - LZ4.
//  In this example, one loops over nevent events.
//  The branch "event" is created at the first event.
//  The branch address is set for all other events.
//  For each event, the event header is filled and ntrack tracks
//  are generated and added to the TClonesArray list.
//  For each event the event histogram is saved as well as the list
//  of all tracks.
//
//  The two TRefArray contain only references to the original tracks owned by
//  the TClonesArray fTracks.
//
//  The number of events can be given as the first argument to the program.
//  By default 400 events are generated.
//  The compression option can be activated/deactivated via the second argument.
//
//  Additionally, if the environment ENABLE_TTREEPERFSTATS is set, then detailed
//  statistics about IO performance will be reported.
//
//   ---Running/Linking instructions----
//  This program consists of the following files and procedures.
//    - Event.h event class description
//    - Event.C event class implementation
//    - MainEvent.C the main program to demo this class might be used (this file)
//    - EventCint.C  the CINT dictionary for the event and Track classes
//        this file is automatically generated by rootcint (see Makefile),
//        when the class definition in Event.h is modified.
//
//   ---Analyzing the Event.root file with the interactive root
//        example of a simple session
//   Root > TFile f("Event.root")
//   Root > T.Draw("fNtrack")   //histogram the number of tracks per event
//   Root > T.Draw("fPx")       //histogram fPx for all tracks in all events
//   Root > T.Draw("fXfirst:fYfirst","fNtrack>600")
//                              //scatter-plot for x versus y of first point of each track
//   Root > T.Draw("fH.GetRMS()")  //histogram of the RMS of the event histogram
//
//   Look also in the same directory at the following macros:
//     - eventa.C  an example how to read the tree
//     - eventb.C  how to read events conditionally
//
////////////////////////////////////////////////////////////////////////

#include <stdlib.h>

#include "Riostream.h"
#include "TROOT.h"
#include "TFile.h"
#include "TNetFile.h"
#include "TRandom.h"
#include "TTree.h"
#include "TTreePerfStats.h"
#include "TBranch.h"
#include "TClonesArray.h"
#include "TStopwatch.h"

#include "Event.h"

using namespace std;

////////////////////////////////////////////////////////////////////////////////

int main(int argc, char **argv)
{
   Int_t nevent = 400;     // by default create 400 events
   Int_t comp   = 1;       // by default file is compressed
   Int_t split  = 1;       // by default, split Event in sub branches
   Int_t write  = 1;       // by default the tree is filled
   Int_t hfill  = 0;       // by default histograms are not filled
   Int_t read   = 0;
   Int_t arg4   = 1;
   Int_t arg5   = 600;     //default number of tracks per event
   Int_t enable_imt = 0;   // Whether to enable IMT mode.
#ifdef R__HAS_DEFAULT_LZ4
   Int_t compAlg = 4; // Allow user to specify underlying compression algorithm.
#else
   Int_t compAlg = 1;
#endif
   Int_t netf   = 0;
   Int_t punzip = 0;

   if (argc > 1)  nevent = atoi(argv[1]);
   if (argc > 2)  comp   = atoi(argv[2]);
   if (argc > 3)  split  = atoi(argv[3]);
   if (argc > 4)  arg4   = atoi(argv[4]);
   if (argc > 5)  arg5   = atoi(argv[5]);
   if (argc > 6)  enable_imt = atoi(argv[6]);
   if (argc > 7) compAlg = atoi(argv[7]);
   if (arg4 ==  0) { write = 0; hfill = 0; read = 1;}
   if (arg4 ==  1) { write = 1; hfill = 0;}
   if (arg4 ==  2) { write = 0; hfill = 0;}
   if (arg4 == 10) { write = 0; hfill = 1;}
   if (arg4 == 11) { write = 1; hfill = 1;}
   if (arg4 == 20) { write = 0; read  = 1;}  //read sequential
   if (arg4 == 21) { write = 0; read  = 1;  punzip = 1;}  //read sequential + parallel unzipping
   if (arg4 == 25) { write = 0; read  = 2;}  //read random
   if (arg4 >= 30) { netf  = 1; }            //use TNetFile
   if (arg4 == 30) { write = 0; read  = 1;}  //netfile + read sequential
   if (arg4 == 35) { write = 0; read  = 2;}  //netfile + read random
   if (arg4 == 36) { write = 1; }            //netfile + write sequential
   Int_t branchStyle = 1; //new style by default
   if (split < 0) {branchStyle = 0; split = -1-split;}

#ifdef R__USE_IMT
   if (enable_imt) {
     ROOT::EnableImplicitMT();
   }
#else
   if (enable_imt) {
     std::cerr << "IMT mode requested, but this version of ROOT "
                  "is built without IMT support." << std::endl;
     return 1;
   }
#endif

   TFile *hfile;
   TTree *tree;
   TTreePerfStats *ioperf = nullptr;
   Event *event = 0;

   // Fill event, header and tracks with some random numbers
   //   Create a timer object to benchmark this loop
   TStopwatch timer;
   timer.Start();
   Long64_t nb = 0;
   Int_t ev;
   Int_t bufsize;
   Double_t told = 0;
   Double_t tnew = 0;
   Int_t printev = 100;
   if (arg5 < 100) printev = 1000;
   if (arg5 < 10)  printev = 10000;

//         Read case
   if (read) {
      if (netf) {
         hfile = new TNetFile("root://localhost/root/test/EventNet.root");
      } else
         hfile = new TFile("Event.root");
      tree = (TTree*)hfile->Get("T");
      TBranch *branch = tree->GetBranch("event");
      branch->SetAddress(&event);
      Int_t nentries = (Int_t)tree->GetEntries();
      nevent = TMath::Min(nevent,nentries);
      if (read == 1) {  //read sequential
         ioperf = getenv("ENABLE_TTREEPERFSTATS") ? new TTreePerfStats("Perf Stats", tree) : nullptr;
         //by setting the read cache to -1 we set it to the AutoFlush value when writing
         Int_t cachesize = -1;
         if (punzip) tree->SetParallelUnzip();
         tree->SetCacheSize(cachesize);
         tree->SetCacheLearnEntries(1); //one entry is sufficient to learn
         tree->SetCacheEntryRange(0,nevent);
         for (ev = 0; ev < nevent; ev++) {
            tree->LoadTree(ev);  //this call is required when using the cache
            if (ev%printev == 0) {
               tnew = timer.RealTime();
               printf("event:%d, rtime=%f s\n",ev,tnew-told);
               told=tnew;
               timer.Continue();
            }
            nb += tree->GetEntry(ev);        //read complete event in memory
         }
         if (ioperf) {
            ioperf->Finish();
         }
      } else {    //read random
         Int_t evrandom;
         for (ev = 0; ev < nevent; ev++) {
            if (ev%printev == 0) std::cout<<"event="<<ev<<std::endl;
            evrandom = Int_t(nevent*gRandom->Rndm());
            nb += tree->GetEntry(evrandom);  //read complete event in memory
         }
      }
   } else {
//         Write case
      // Create a new ROOT binary machine independent file.
      // Note that this file may contain any kind of ROOT objects, histograms,
      // pictures, graphics objects, detector geometries, tracks, events, etc..
      // This file is now becoming the current directory.
      if (netf) {
         hfile = new TNetFile("root://localhost/root/test/EventNet.root","RECREATE","TTree benchmark ROOT file");
      } else
         hfile = new TFile("Event.root","RECREATE","TTree benchmark ROOT file");
      hfile->SetCompressionLevel(comp);
      hfile->SetCompressionAlgorithm(compAlg);

      // Create histogram to show write_time in function of time
      Float_t curtime = -0.5;
      Int_t ntime = nevent / printev;
      TH1F *htime = new TH1F("htime", "Real-Time to write versus time", ntime, 0, ntime);
      HistogramManager *hm = 0;
      if (hfill) {
         TDirectory *hdir = new TDirectory("histograms", "all histograms");
         hm = new HistogramManager(hdir);
      }

      // Create a ROOT Tree and one superbranch
      tree = new TTree("T","An example of a ROOT tree");
      tree->SetAutoSave(1000000000); // autosave when 1 Gbyte written
      tree->SetCacheSize(10000000);  // set a 10 MBytes cache (useless when writing local files)
      bufsize = 64000;
      if (split)  bufsize /= 4;
      event = new Event();           // By setting the value, we own the pointer and must delete it.
      TTree::SetBranchStyle(branchStyle);
      TBranch *branch = tree->Branch("event", &event, bufsize,split);
      branch->SetAutoDelete(kFALSE);
      if(split >= 0 && branchStyle) tree->BranchRef();
      Float_t ptmin = 1;

      for (ev = 0; ev < nevent; ev++) {
         if (ev%printev == 0) {
            tnew = timer.RealTime();
            printf("event:%d, rtime=%f s\n",ev,tnew-told);
            htime->Fill(curtime,tnew-told);
            curtime += 1;
            told=tnew;
            timer.Continue();
         }

         event->Build(ev, arg5, ptmin);

         if (write) nb += tree->Fill();  //fill the tree

         if (hm) hm->Hfill(event);      //fill histograms
      }
      if (write) {
         hfile = tree->GetCurrentFile(); //just in case we switched to a new file
         hfile->Write();
         tree->Print();
      }
   }
   // We own the event (since we set the branch address explicitly), we need to delete it.
   delete event;  event = 0;

   //  Stop timer and print results
   timer.Stop();
   Float_t mbytes = 0.000001*nb;
   Double_t rtime = timer.RealTime();
   Double_t ctime = timer.CpuTime();


   printf("\n%d events and %lld bytes processed.\n",nevent,nb);
   printf("RealTime=%f seconds, CpuTime=%f seconds\n",rtime,ctime);
   if (read) {
      tree->PrintCacheStats();
      if (ioperf) {
         ioperf->Print();
      }
      printf("You read %f Mbytes/Realtime seconds\n", mbytes / rtime);
      printf("You read %f Mbytes/Cputime seconds\n", mbytes / ctime);
   } else {
      printf("compression level=%d, split=%d, arg4=%d, IMT=%d, compression algorithm=%d\n", comp, split, arg4,
             enable_imt, compAlg);
      printf("You write %f Mbytes/Realtime seconds\n",mbytes/rtime);
      printf("You write %f Mbytes/Cputime seconds\n",mbytes/ctime);
      //printf("file compression factor = %f\n",hfile.GetCompressionFactor());
   }
   hfile->Close();
   return 0;
}
