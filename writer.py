import numpy

from write.diskarray import DiskArray
from write.sink import Sink
from write.cursor import Cursor
from write.headkey import HeadKey
from write.header import Header
from write.begin_key import Begin_Key
from write.directoryinfo import DirectoryInfo
from write.first_key import First_Key

from write.TObjString.tobjstring import TObjString
from write.TObjString.key import Key as StringKey
from write.TObjString.junkkey import JunkKey
from write.TObjString.streamers import TObjStringStreamers

class Writer(object):
    
    def __init__(self, filename):
        self.file = DiskArray(filename, shape = (0,), dtype = numpy.uint8)
        self.bytename = filename.encode("utf-8")
        
        self.sink = Sink(self.file)
        self.cursor = Cursor(0)

        self.objects = []
        self.loc = []
        self.streamers = []

        fCompress = 0 #Constant for now
        self.header = Header(self.bytename, fCompress)
        #self.header.fSeekInfo modified later
        self.sink.set_header(self.cursor, self.header)

        self.cursor = Cursor(self.header.fBEGIN)
        pointcheck = self.cursor.index
        fName = self.bytename
        key = Begin_Key(fName)
        self.sink.set_key(self.cursor, key)

        key.fKeylen = self.cursor.index - pointcheck
        key.fObjlen = key.fNbytes - key.fKeylen
        self.sink.set_key(Cursor(pointcheck), key)

        #Junk
        self.sink.set_strings(self.cursor, fName)

        self.directory_pointcheck = self.cursor.index
        fNbytesKeys = 0
        fNbytesName = self.header.fNbytesName
        self.directory = DirectoryInfo(fNbytesKeys, fNbytesName, 0)
        #Update directory.fSeekKeys later
        self.sink.set_directoryinfo(self.cursor, self.directory)

        self.cursor.skip(30)

        self.header.fEND = self.cursor.index
        self.header.fSeekFree = self.cursor.index
        self.sink.set_header(Cursor(0), self.header)

        self.create()

    def __setitem__(self, item):

        #item = TObjString("Hello World")

        if type(item) is TObjString:
            temp = str(item.string)
            temp = temp.encode("utf-8")
            self.objects.append(temp)
            self.loc.append(self.cursor.index)

            pointcheck = self.cursor.index
            junkkey = JunkKey(temp)
            self.sink.set_key(self.cursor, junkkey)
            junkkey.fKeylen = self.cursor.index - pointcheck
            junkkey.fNbytes = junkkey.fKeylen + junkkey.fObjlen
            self.sink.set_key(Cursor(pointcheck), junkkey)

            stringobject = TObjString(temp)
            self.sink.set_object(self.cursor, stringobject)

            #Streamername
            if "TObjString" not in self.streamers:
                self.streamers.append("TObjString")

        self.create()

    def create(self):
        self.header.fSeekInfo = self.cursor.index
        self.sink.set_header(Cursor(0), self.header)

        pointcheck = self.cursor.index
        key = First_Key(self.cursor, 0)
        self.sink.set_key(self.cursor, key)

        key.fKeylen = self.cursor.index - pointcheck
        key.fNbytes = key.fKeylen + key.fObjlen
        self.sink.set_key(Cursor(pointcheck), key)

        self.header.fNbytesInfo = key.fNbytes
        self.sink.set_header(Cursor(0), self.header)

        for x in self.streamers:
            if x == "TObjString":
                tobjstring = TObjStringStreamers(self.sink, self.cursor)
                tobjstring.write()

        fSeekKeys = self.cursor.index

        self.directory.fSeekKeys = self.cursor.index
        self.sink.set_directoryinfo(Cursor(self.directory_pointcheck), self.directory)

        head_key_pointcheck = self.cursor.index
        fNbytes = self.directory.fNbytesKeys
        fSeekKey = self.directory.fSeekKeys
        fName = self.bytename
        head_key = HeadKey(fNbytes, fSeekKey, fName)
        self.sink.set_key(self.cursor, head_key)
        head_key_end = self.cursor.index

        nkeys = len(self.objects)
        packer = ">i"
        self.sink.set_numbers(self.cursor, packer, nkeys)

        #TObjString stuff
        for x in range(nkeys):
            key = StringKey(self.objects[x], self.loc[x])
            pointcheck = self.cursor.index
            self.sink.set_key(self.cursor, key)
            key.fKeylen = self.cursor.index - pointcheck
            key.fNbytes = key.fKeylen + key.fObjlen
            self.sink.set_key(Cursor(pointcheck), key)

        self.header.fEND = self.cursor.index
        self.header.fSeekFree = self.cursor.index

        # Replacing Values
        self.directory.fNbytesKeys = self.header.fEND - fSeekKeys
        self.sink.set_directoryinfo(Cursor(self.directory_pointcheck), self.directory)

        head_key.fNbytes = self.directory.fNbytesKeys
        head_key.fKeylen = head_key_end - head_key_pointcheck
        head_key.fObjlen = head_key.fNbytes - head_key.fKeylen
        self.sink.set_key(Cursor(head_key_pointcheck), head_key)


