import numpy
from write.pusher import Pusher
from write.pointer import Pointer
from write.key import Key as HeadKey
from write.TObjString.stringobject import StringObject
from write.TObjString.key import Key as StringKey

class Writer(object):
    
    def __init__(self, filename):
        self.file = numpy.memmap(filename = filename, dtype = numpy.uint8, mode = "w+", shape = (1,))
        self.bytename = filename.encode("utf-8")
        
        self.pusher = Pusher(self.file)
        self.pointer = Pointer(0)
        
        self.strings = []
        self.stringloc = []
        
        from write.header import Header
        fCompress = 0 #Constant for now
        self.header = Header(self.bytename, fCompress)
        #Have to add modified fSeekInfo later
        self.pusher.head_push(self.pointer, self.header)
        
        from write.begin_key import Begin_Key
        self.pointer = Pointer(self.header.fBEGIN)
        pointcheck = self.pointer.index
        fName = self.bytename
        key = Begin_Key(fName)
        self.pusher.keyer(self.pointer, key)

        key.fKeylen = self.pointer.index - pointcheck
        key.fObjlen = key.fNbytes - key.fKeylen
        self.pusher.keyer(Pointer(pointcheck), key)
        
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
        self.pusher.head_push(Pointer(0), self.header)
        
    def __setitem__(self, item):
        temp = str(item)
        temp = temp.encode("utf-8")
        self.strings.append(temp)
        self.stringloc.append(self.pointer.index)
        
        from write.TObjString.junkkey import JunkKey
        pointcheck = self.pointer.index
        junkkey = JunkKey(temp)
        self.pusher.keyer(self.pointer, junkkey)
        junkkey.fKeylen = self.pointer.index - pointcheck
        junkkey.fNbytes = junkkey.fKeylen + junkkey.fObjlen
        self.pusher.keyer(Pointer(pointcheck), junkkey)
        
        stringobject = StringObject(temp)
        self.pusher.push_object(self.pointer, stringobject)

    def create(self):
        self.header.fSeekInfo = self.pointer.index
        self.pusher.head_push(Pointer(0), self.header)

        from write.first_key import First_Key
        pointcheck = self.pointer.index
        key = First_Key(self.pointer, 0)
        self.pusher.keyer(self.pointer, key)

        key.fKeylen = self.pointer.index - pointcheck
        key.fNbytes = key.fKeylen + key.fObjlen
        self.pusher.keyer(Pointer(pointcheck), key)

        self.header.fNbytesInfo = key.fNbytes
        self.pusher.head_push(Pointer(0), self.header)

        from write.TObjString.streamers import TObjString
        tobjstring = TObjString(self.pusher, self.pointer)
        tobjstring.write()

        fSeekKeys = self.pointer.index

        self.directory.fSeekKeys = self.pointer.index
        self.pusher.director(Pointer(self.directory_pointcheck), self.directory)

        head_key_pointcheck = self.pointer.index
        fVersion = 4
        fNbytes = self.directory.fNbytesKeys
        fObjlen = 0
        fDatime = 1573188772
        fKeylen = 0
        fCycle = 1
        fSeekKey = self.directory.fSeekKeys
        fSeekPdir = 100
        fClassName = b'TFile'
        fName = self.bytename
        fTitle = b''
        packer = ">ihiIhhii"
        head_key = HeadKey(packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName,
                       fName, fTitle)
        self.pusher.keyer(self.pointer, head_key)
        head_key_end = self.pointer.index

        nkeys = len(self.strings)
        packer = ">i"
        self.pusher.numbers(self.pointer, packer, nkeys)

        for x in range(nkeys):
            key = StringKey(self.strings[x], self.stringloc[x])
            self.pusher.keyer(self.pointer, key)

        self.header.fEND = self.pointer.index
        self.header.fSeekFree = self.pointer.index

        # Replacing Values
        self.directory.fNbytesKeys = self.header.fEND - fSeekKeys
        self.pusher.director(Pointer(self.directory_pointcheck), self.directory)

        head_key.fNbytes = self.directory.fNbytesKeys
        head_key.fKeylen = head_key_end - head_key_pointcheck
        head_key.fObjlen = head_key.fNbytes - head_key.fKeylen
        self.pusher.keyer(Pointer(head_key_pointcheck), head_key)






        
        
                                
        