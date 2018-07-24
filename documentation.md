# ROOT File Trends

## Header

fVersion = Version of ROOT being used(Follow ROOT)  
fBEGIN = 100 (Follow ROOT)  
fEND = Size of file = fSeekFree + fNbytesFree  
fSeekFree = Last useful byte location = fBEGIN + (Summation of fNbytes of all TKeys)  
fNbytesFree = No. of junk bytes in the file  
nfree = 1 ?  
fNbytesName = Starting position of DirectoryInfo - fBEGIN  = 36 + 2 times the length of the name of the file in bytes  
fUnits = 4 ?  
fCompress = Compression(Can be set manually while writing ROOT file)  
fSeekInfo = Points to first key = Where branch informations end  
fNbytesInfo = fNBytes of first key  
fUUID = Identifier unique to each ROOT file  
  
## TKey
There is a streamer key, a header key and 1 more key.  
The streamer key has the same fClassName, fName and fTitle for all files.  
  
Starting point = fSeekInfo  
fNbytes = fNbytesInfo = fObjlen + fKeylen = Number of bytes occupied by this TKey  
fObjlen = ?  
fDatime = Date and time (Need to figure out format)  
fKeylen = ?(64 for TList streamer key)  
fCycle = Instance of creation of the key  
fSeekKey = ?  
fVersion = Version of that instance(Follow ROOT)  
fSeekPdir = 100? (0 for first cursor location?)  
fClassName = Name of class of objects being pointed to.  
fName = ?  
fTitle = Title of the object.(Not important)  
  
## Directory

TKey before Directory information -> fTitle = b""  
  
Start position = Pointer after fName of previous key is added to the end of that key + 1  = fBEGIN + fNbytesName  
fVersion = Version of that instance(Follow ROOT)  
fDatimeC = Date and time (Need to figure out format)  
fDatimeM = Date and time (Need to figure out format)  
fNbytesKeys = ?  
fNbytesName = fNbytesName of Header  
fSeekDir = 100 ?  
fSeekParent = 0 ?  
fSeekKeys = fSeekKey of header key ?  

## Streamer Trends

### Startcheck
When is it called?  

cnt = ?  
vers = Version of that instance (Follow ROOT)  

### skiptobj
When is it called?  

version = Version of that instance (Follow ROOT)  
fUniqueID = ?  
fBits = ?  

### TStreamer Element
TStreamerBase, TStreamerString is followed by TStreamer Element
- Cursor = end of previous cursor
- No indication to show that it is followed by TStreamer Element  

name = ?  
title = ?  

fType = ?  
fSize = ?  
fArrayLength = ?  
fArrayDim = ?  
fMaxIndex = ?  

fTypeName = C++ type Name.   

fBaseVersion = ?  

### Number of keys

Starting position = ?  
nkeys = Number of extra keys in the file  = Starting position of the keys  


name = ?  
size = ?  

bcnt = ?  

tag = ?  

cname = Points to next streamer  

fCheckSum = ?  
fClassVersion = ?  


StreamerKey fClassName points to first streamer  

First Cursor = Streamer Key -> Initial cursor + fKeyLen = End of previous cursor  
Cursor = Previous end of pointer + 1









