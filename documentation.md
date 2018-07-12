#ROOT File Trends

##Header

fBEGIN = 100 (Follow ROOT)

fNbytesFree = No. of junk bytes in the file

fVersion = Version of ROOT being used(Follow ROOT)

fUUID = Identifier unique to each ROOT file

fEND = Size of file

fSeekFree = Last userful byte location

nfree = 1 ?

fUnits = 4 ?

fCompress = Compression(Can be set manually while writing ROOT file)

fSeekInfo ?

fNbytesInfo = fNBytes of Streamer Key


##TKey

fNbytes = fObjlen + fKeylen = Number of bytes occupied by this TKey

(Summation of fNbytes of all TKey) + fBEGIN + fNbytesFree = fEND

fVersion = Version of that instance(Follow ROOT)

fDatime = Date and time (Need to figure out format)

fSeekKey = cursor?

fSeekPdir = 100? (0 for first cursor location?)

fCycle = Recursive Iteration level?


##Streamer Trends

StreamerKey fClassName points to first streamer
cname points to next Streamer

First Cursor = Streamer Key -> Initial cursor + fKeyLen = End of previous cursor
Cursor = Previous end of pointer + 1

TStreamerBase, TStreamerString is followed by TStreamer Element 
*Cursor = end of previous cursor
*No indication to show that it is followed by TStreamer Element








