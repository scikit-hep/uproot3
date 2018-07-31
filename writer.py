import numpy
from write.pusher import Pusher
from write.pointer import Pointer
from write.key import Key

class Writer(object):
    
    def __init__(self, filename):
        self.file = numpy.memmap(filename = filename, dtype = numpy.uint8, mode = "w+", shape = (1,))
        self.bytename = filename.encode("utf-8")
        
        self.pusher = Pusher(self.file)
        self.pointer = Pointer(0)
        
        from write.header import Header
        fCompress = 0 #Constant for now
        header = Header(self.bytename, fCompress)
        #Have to add modified fSeekInfo later
        self.pusher.head_push(self.pointer, header)
        
        from write.begin_key import Begin_Key
        self.pointer = Pointer(header.fBEGIN)
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
        directory_pointcheck = self.pointer.index
        fNbytesKeys = 0
        fNbytesName = header.fNbytesName
        directory = DirectoryInfo(fNbytesKeys, fNbytesName, 0)
        #Update directory.fSeekKeys later
        self.pusher.director(self.pointer, directory)

        directory_end = self.pointer.index
        
        self.pointer.skip(30)

        header.fEND = self.pointer.index
        header.fSeekFree = self.pointer.index
        self.pusher.head_push(Pointer(0), header)
        
    def 
        
    def __setitem__():
        
        
        
                                
        