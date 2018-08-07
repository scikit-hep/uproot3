import numpy
from write.sink import Sink
from write.cursor import Cursor
from write.headkey import HeadKey
from write.TObjString.tobjstring import TObjString
from write.TObjString.key import Key as StringKey
from write.diskarray import DiskArray

class Writer(object):
    
    def __init__(self, filename):
        self.file = DiskArray(filename, shape = (0,), dtype = numpy.uint8)
        self.bytename = filename.encode("utf-8")
        
        self.pusher = Sink(self.file)
        self.pointer = Cursor(0)
        
        self.objects = []
        self.loc = []
        self.streamers = []

        from write.header import Header
        fCompress = 0 #Constant for now
        self.header = Header(self.bytename, fCompress)
        #self.header.fSeekInfo modified later
        self.pusher.head_push(self.pointer, self.header)
        
        from write.begin_key import Begin_Key
        self.pointer = Cursor(self.header.fBEGIN)
        pointcheck = self.pointer.index
        fName = self.bytename
        key = Begin_Key(fName)
        self.pusher.keyer(self.pointer, key)

        key.fKeylen = self.pointer.index - pointcheck
        key.fObjlen = key.fNbytes - key.fKeylen
        self.pusher.keyer(Cursor(pointcheck), key)
        
        #Junk
        self.pusher.stringer(self.pointer, fName)
        
        from write.directoryinfo import DirectoryInfo
        self.directory_pointcheck = self.pointer.index
        fNbytesKeys = 0
        fNbytesName = self.header.fNbytesName
        self.directory = DirectoryInfo(fNbytesKeys, fNbytesName, 0)
        #Update directory.fSeekKeys later
        self.pusher.director(self.pointer, self.directory)

        self.pointer.skip(30)

        self.header.fEND = self.pointer.index
        self.header.fSeekFree = self.pointer.index
        self.pusher.head_push(Cursor(0), self.header)

        self.create()
        
    def __setitem__(self, item):

        #item = TObjString("Hello World")

        if type(item) is TObjString:
            temp = str(item.string)
            temp = temp.encode("utf-8")
            self.objects.append(temp)
            self.loc.append(self.pointer.index)
        
            from write.TObjString.junkkey import JunkKey
            pointcheck = self.pointer.index
            junkkey = JunkKey(temp)
            self.pusher.keyer(self.pointer, junkkey)
            junkkey.fKeylen = self.pointer.index - pointcheck
            junkkey.fNbytes = junkkey.fKeylen + junkkey.fObjlen
            self.pusher.keyer(Cursor(pointcheck), junkkey)
        
            stringobject = TObjString(temp)
            self.pusher.push_object(self.pointer, stringobject)

            #Streamername
            if "TObjString" not in self.streamers:
                self.streamers.append("TObjString")

        self.create()

    def create(self):
        self.header.fSeekInfo = self.pointer.index
        self.pusher.head_push(Cursor(0), self.header)

        from write.first_key import First_Key
        pointcheck = self.pointer.index
        key = First_Key(self.pointer, 0)
        self.pusher.keyer(self.pointer, key)

        key.fKeylen = self.pointer.index - pointcheck
        key.fNbytes = key.fKeylen + key.fObjlen
        self.pusher.keyer(Cursor(pointcheck), key)

        self.header.fNbytesInfo = key.fNbytes
        self.pusher.head_push(Cursor(0), self.header)

        for x in self.streamers:
            if x == "TObjString":
                from write.TObjString.streamers import TObjString
                tobjstring = TObjString(self.pusher, self.pointer)
                tobjstring.write()

        fSeekKeys = self.pointer.index

        self.directory.fSeekKeys = self.pointer.index
        self.pusher.director(Cursor(self.directory_pointcheck), self.directory)

        head_key_pointcheck = self.pointer.index
        fNbytes = self.directory.fNbytesKeys
        fSeekKey = self.directory.fSeekKeys
        fName = self.bytename
        head_key = HeadKey(fNbytes, fSeekKey, fName)
        self.pusher.keyer(self.pointer, head_key)
        head_key_end = self.pointer.index

        nkeys = len(self.objects)
        packer = ">i"
        self.pusher.numbers(self.pointer, packer, nkeys)

        #TObjString stuff
        for x in range(nkeys):
            key = StringKey(self.objects[x], self.loc[x])
            pointcheck = self.pointer.index
            self.pusher.keyer(self.pointer, key)
            key.fKeylen = self.pointer.index - pointcheck
            key.fNbytes = key.fKeylen + key.fObjlen
            self.pusher.keyer(Cursor(pointcheck), key)

        self.header.fEND = self.pointer.index
        self.header.fSeekFree = self.pointer.index

        # Replacing Values
        self.directory.fNbytesKeys = self.header.fEND - fSeekKeys
        self.pusher.director(Cursor(self.directory_pointcheck), self.directory)

        head_key.fNbytes = self.directory.fNbytesKeys
        head_key.fKeylen = head_key_end - head_key_pointcheck
        head_key.fObjlen = head_key.fNbytes - head_key.fKeylen
        self.pusher.keyer(Cursor(head_key_pointcheck), head_key)


