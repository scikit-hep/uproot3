from write.sink import Sink
from write.headkey import HeadKey
from write.header import Header
from write.begin_key import Begin_Key
from write.directoryinfo import DirectoryInfo
from write.streamerkey import StreamerKey
from write.allstreamer import AllStreamers
from write.utils import resize

from write.TObjString.tobjstring import TObjString
from write.TObjString.key import Key as StringKey
from write.TObjString.junkkey import JunkKey as TObjStringJunkKey

from write.TAxis.taxis import TAxis
from write.TAxis.key import Key as AxisKey
from write.TAxis.junkkey import JunkKey as TAxisJunkKey

import pickle

class Writer(object):

    def __init__(self, filename):
        self.file = open(filename, "wb+")
        filename = filename[(filename.rfind("/") + 1):]
        self.bytename = filename.encode("utf-8")

        self.sink = Sink(self.file)
        self.pos = 0

        self.streamers = []
        self.expander = 1000
        self.expandermultiple = 2

        self.nkeypos = 0

        #Header Bytes
        fCompress = 0 #Constant for now
        self.header = Header(self.bytename, fCompress)
        self.sink.set_header(self.header)

        #Key
        self.pos = self.header.fBEGIN
        pointcheck = self.pos
        fName = self.bytename
        key = Begin_Key(fName)
        self.sink.set_key(self.pos, key)
        self.pos = self.file.tell()
        key.fKeylen = self.pos - pointcheck
        key.fObjlen = key.fNbytes - key.fKeylen
        self.sink.set_key(pointcheck, key)

        #Junk
        self.sink.set_strings(self.pos, fName)
        self.pos = self.file.tell()

        #DirectoryInfo
        self.directory_pointcheck = self.pos
        fNbytesKeys = 0
        fNbytesName = self.header.fNbytesName
        self.directory = DirectoryInfo(fNbytesKeys, fNbytesName, 0)
        self.sink.set_directoryinfo(self.pos, self.directory)
        self.pos = self.file.tell()

        #header.fSeekInfo points to begin of StreamerKey
        self.header.fSeekInfo = self.pos

        #StreamerKey
        pointcheck = self.pos
        streamerkey = StreamerKey(self.pos, 0)
        self.sink.set_key(self.pos, streamerkey)
        self.pos = self.file.tell()
        streamerkey.fKeylen = self.pos - pointcheck
        streamerkey.fNbytes = streamerkey.fKeylen + streamerkey.fObjlen
        self.sink.set_key(pointcheck, streamerkey)

        self.header.fNbytesInfo = streamerkey.fNbytes
        self.sink.set_header(self.header)

        #Allocate space for streamers
        streamerstart = self.pos
        self.file = resize(self.file, self.pos + self.expander)
        streamers = AllStreamers(self.sink, self.pos, size = 1)
        streamers.write()
        self.pos = self.file.tell()
        self.streamerend = self.pos
        self.streamerlimit = self.pos + self.expander

        #Starting after space allocated for streamers
        self.pos = streamerstart + self.expander

        #directory.fSeekKeys points to Header key
        self.directory.fSeekKeys = self.pos
        self.sink.set_directoryinfo(self.directory_pointcheck, self.directory)

        #Allocate space for keys
        self.keystart = self.pos
        self.file = resize(self.file, self.pos + self.expander)
        self.keyend = self.pos
        self.keylimit = self.keystart + self.expander

        #Head Key
        self.head_key_pointcheck = self.pos
        fNbytes = self.directory.fNbytesKeys
        fSeekKey = self.directory.fSeekKeys
        fName = self.bytename
        self.head_key = HeadKey(fNbytes, fSeekKey, fName)
        self.sink.set_key(self.pos, self.head_key)
        self.pos = self.file.tell()
        self.head_key_end = self.pos

        #Number of Keys
        self.nkeys = 0
        packer = ">i"
        self.sink.set_numbers(self.pos, packer, self.nkeys)
        self.pos = self.file.tell()

        self.keyend = self.pos

        self.header.fSeekFree = self.pos
        self.header.fEND = self.header.fSeekFree + self.expander
        self.sink.set_header(self.header)

    def __setitem__(self, keyname, item):

        self.pos = self.header.fEND
        pointcheck = self.pos

        if type(item) is TObjString:
            junkkey = TObjStringJunkKey(keyname.encode("utf-8"))
            key = StringKey(keyname.encode("utf-8"), pointcheck)

            streamers = ["TObjString"]
            streamers_toadd = []
            for x in streamers:
                if x not in self.streamers:
                    self.streamers.append(x)
                    streamers_toadd.append(x)

        if type(item) is TAxis:
            junkkey = TAxisJunkKey(keyname.encode("utf-8"))
            key = AxisKey(keyname.encode("utf-8"), pointcheck)

            streamers = ["TNamed", "TObject", "TAttAxis", "THashList", "TCollection", "TString", "TAxis", "TSeqCollection", "TList"]
            streamers_toadd = []
            for x in streamers:
                if x not in self.streamers:
                    self.streamers.append(x)
                    streamers_toadd.append(x)


        self.sink.set_key(self.pos, junkkey)
        self.pos = self.file.tell()
        junkkey.fKeylen = self.pos - pointcheck
        junkkey.fNbytes = junkkey.fKeylen + junkkey.fObjlen
        self.sink.set_key(pointcheck, junkkey)
        self.pos = self.file.tell()

        if type(item.string) is str:
            item.string = item.string.encode("utf-8")

        self.sink.set_object(self.pos, item)
        self.pos = self.file.tell()

        # Updating Header Bytes
        if self.pos > self.header.fEND:
            self.header.fSeekFree = self.pos
            self.header.fEND = self.pos

        self.sink.set_header(self.header)

        #Check for Key Re-alocation
        if self.keylimit - self.keyend < 200:
            self.file.seek(self.directory.fSeekKeys)
            temp = self.file.read(self.expander)
            self.expander = self.expander * self.expandermultiple
            self.file = resize(self.file, self.header.fEND + self.expander)
            self.file.seek(self.header.fEND)
            self.file.write(temp)
            self.keyend = self.header.fEND + self.keyend - self.directory.fSeekKeys
            self.directory.fSeekKeys = self.header.fEND
            self.keylimit = self.header.fEND + self.expander
            self.header.fEND = self.keylimit
            self.header.fSeekFree = self.keylimit
            self.sink.set_directoryinfo(self.directory_pointcheck, self.directory)
            self.head_key_end = self.directory.fSeekKeys + self.nkeypos

        pointcheck = self.keyend
        self.sink.set_key(self.keyend, key)
        self.keyend = self.file.tell()
        key.fKeylen = self.keyend - pointcheck
        key.fNbytes = key.fKeylen + key.fObjlen
        self.sink.set_key(pointcheck, key)


        # Updating Header Bytes
        if self.pos > self.header.fEND:
            self.header.fSeekFree = self.pos
            self.header.fEND = self.pos

        self.sink.set_header(self.header)

        self.sink.file.seek(self.streamerend)
        for x in streamers_toadd:
            streamer = pickle.load(open("write/streamers.pickle", "rb"))

            # Check for streamer reallocation - UNTESTED
            if self.streamerlimit - self.streamerend < 500:
                self.file.seek(self.header.fSeekInfo)
                temp = self.file.read(self.expander)
                self.expander = self.expander * self.expandermultiple
                self.file = resize(self.file, self.header.fEND + self.expander)
                self.file.seek(self.header.fEND)
                self.file.write(temp)
                self.streamerend = self.header.fEND + self.streamerend - self.header.fSeekInfo
                self.header.fSeekInfo = self.header.fEND
                self.streamerlimit = self.header.fEND + self.expander
                self.header.fEND = self.streamerlimit
                self.header.fSeekFree = self.streamerlimit

            self.sink.file.write(streamer[x])
        self.streamerend = self.file.tell()

        #Update number of keys
        self.nkeypos = self.head_key_end - self.directory.fSeekKeys
        self.nkeys += 1
        packer = ">i"
        self.sink.set_numbers(self.head_key_end, packer, self.nkeys)

        #Update DirectoryInfo
        self.directory.fNbytesKeys = self.header.fEND - self.keyend
        self.sink.set_directoryinfo(self.directory_pointcheck, self.directory)

        #Update Head Key
        self.head_key.fNbytes = self.directory.fNbytesKeys
        self.head_key.fKeylen = self.head_key_end - self.head_key_pointcheck
        self.head_key.fObjlen = self.head_key.fNbytes - self.head_key.fKeylen
        self.sink.set_key(self.head_key_pointcheck, self.head_key)

        #Updating Header Bytes
        if self.pos > self.header.fEND:
            self.header.fSeekFree = self.pos
            self.header.fEND = self.pos

        self.sink.set_header(self.header)

        self.file.flush()

    def close(self):
        self.file.close()
