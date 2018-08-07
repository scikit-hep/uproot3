import numpy
from write.sink import Sink
from write.cursor import Cursor
from write.headkey import HeadKey
from write.TObjString.tobjstring import TObjString
from write.TObjString.key import Key as StringKey
from write.diskarray import DiskArray
from write.header import Header
from write.begin_key import Begin_Key
from write.directoryinfo import DirectoryInfo
from write.TObjString.junkkey import JunkKey
from write.first_key import First_Key
from write.TObjString.streamers import TObjStringStreamers

class Writer(object):
    
    def __init__(self, filename):
        self.file = DiskArray(filename, shape = (0,), dtype = numpy.uint8)
        self.bytename = filename.encode("utf-8")
        
        self.pusher = Sink(self.file)
        self.pointer = Cursor(0)

        self.objects = []
        self.loc = []
        self.streamers = []

        fCompress = 0 #Constant for now
        self.header = Header(self.bytename, fCompress)
        #self.header.fSeekInfo modified later
        self.pusher.set_header(self.pointer, self.header)

        self.pointer = Cursor(self.header.fBEGIN)
        pointcheck = self.pointer.index
        fName = self.bytename
        key = Begin_Key(fName)
        self.pusher.set_key(self.pointer, key)

        key.fKeylen = self.pointer.index - pointcheck
        key.fObjlen = key.fNbytes - key.fKeylen
        self.pusher.set_key(Cursor(pointcheck), key)

        #Junk
        self.pusher.set_strings(self.pointer, fName)

        self.directory_pointcheck = self.pointer.index
        fNbytesKeys = 0
        fNbytesName = self.header.fNbytesName
        self.directory = DirectoryInfo(fNbytesKeys, fNbytesName, 0)
        #Update directory.fSeekKeys later
        self.pusher.set_directoryinfo(self.pointer, self.directory)

        self.pointer.skip(30)

        self.header.fEND = self.pointer.index
        self.header.fSeekFree = self.pointer.index
        self.pusher.set_header(Cursor(0), self.header)

        self.create()

    def __setitem__(self, item):

        #item = TObjString("Hello World")

        if type(item) is TObjString:
            temp = str(item.string)
            temp = temp.encode("utf-8")
            self.objects.append(temp)
            self.loc.append(self.pointer.index)

            pointcheck = self.pointer.index
            junkkey = JunkKey(temp)
            self.pusher.set_key(self.pointer, junkkey)
            junkkey.fKeylen = self.pointer.index - pointcheck
            junkkey.fNbytes = junkkey.fKeylen + junkkey.fObjlen
            self.pusher.set_key(Cursor(pointcheck), junkkey)

            stringobject = TObjString(temp)
            self.pusher.set_object(self.pointer, stringobject)

            #Streamername
            if "TObjString" not in self.streamers:
                self.streamers.append("TObjString")

        self.create()

    def create(self):
        self.header.fSeekInfo = self.pointer.index
        self.pusher.set_header(Cursor(0), self.header)

        pointcheck = self.pointer.index
        key = First_Key(self.pointer, 0)
        self.pusher.set_key(self.pointer, key)

        key.fKeylen = self.pointer.index - pointcheck
        key.fNbytes = key.fKeylen + key.fObjlen
        self.pusher.set_key(Cursor(pointcheck), key)

        self.header.fNbytesInfo = key.fNbytes
        self.pusher.set_header(Cursor(0), self.header)

        for x in self.streamers:
            if x == "TObjString":
                tobjstring = TObjStringStreamers(self.pusher, self.pointer)
                tobjstring.write()

        fSeekKeys = self.pointer.index

        self.directory.fSeekKeys = self.pointer.index
        self.pusher.set_directoryinfo(Cursor(self.directory_pointcheck), self.directory)

        head_key_pointcheck = self.pointer.index
        fNbytes = self.directory.fNbytesKeys
        fSeekKey = self.directory.fSeekKeys
        fName = self.bytename
        head_key = HeadKey(fNbytes, fSeekKey, fName)
        self.pusher.set_key(self.pointer, head_key)
        head_key_end = self.pointer.index

        nkeys = len(self.objects)
        packer = ">i"
        self.pusher.set_numbers(self.pointer, packer, nkeys)

        #TObjString stuff
        for x in range(nkeys):
            key = StringKey(self.objects[x], self.loc[x])
            pointcheck = self.pointer.index
            self.pusher.set_key(self.pointer, key)
            key.fKeylen = self.pointer.index - pointcheck
            key.fNbytes = key.fKeylen + key.fObjlen
            self.pusher.set_key(Cursor(pointcheck), key)

        self.header.fEND = self.pointer.index
        self.header.fSeekFree = self.pointer.index

        # Replacing Values
        self.directory.fNbytesKeys = self.header.fEND - fSeekKeys
        self.pusher.set_directoryinfo(Cursor(self.directory_pointcheck), self.directory)

        head_key.fNbytes = self.directory.fNbytesKeys
        head_key.fKeylen = head_key_end - head_key_pointcheck
        head_key.fObjlen = head_key.fNbytes - head_key.fKeylen
        self.pusher.set_key(Cursor(head_key_pointcheck), head_key)


