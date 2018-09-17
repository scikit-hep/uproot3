from uproot.write.key import Key

class JunkKey(Key):
    
    def __init__(self, string):
        self.string = string
        self.fVersion = 4
        self.fObjlen = 17 + len(self.string)
        self.fDatime = 1573188772
        self.fKeylen = 0
        self.fNbytes = self.fObjlen + self.fKeylen
        self.fCycle = 1
        self.fSeekKey = 0
        self.fSeekPdir = 100
        self.packer = ">ihiIhhii"
        self.fClassName = b'TObjString'
        self.fName = self.string
        self.fTitle = b'Collectable string class'
        Key.__init__(self, self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle,
                     self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle)

from uproot.write.key import Key as SuperKey

class Key(SuperKey):

    def __init__(self, string, stringloc):
        self.string = string
        self.fVersion = 4
        self.fObjlen = 17 + len(self.string)
        self.fDatime = 1573188772
        self.fKeylen = 0
        self.fNbytes = self.fObjlen + self.fKeylen
        self.fCycle = 1
        self.fSeekKey = stringloc
        self.fSeekPdir = 100
        self.packer = ">ihiIhhii"
        self.fClassName = b'TObjString'
        self.fName = self.string
        self.fTitle = b'Collectable string class'
        SuperKey.__init__(self, self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle,
                     self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle)


import numpy

class TObjString(object):
    
    def __init__(self, string):
        if type(string) is str:
            string = string.encode("utf-8")
        self.string = string
        
    def write_bytes(self, cursor, sink):
        cnt = 17 + len(self.string) - 4
        kByteCountMask = numpy.int64(0x40000000)
        cnt = cnt | kByteCountMask
        vers = 1
        cursor.write_fields(sink, ">IH", cnt, vers)
        
        bytestream =[0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 11, 72, 101, 108, 108, 111, 32, 87, 111, 114, 108, 100]
        sink.write(numpy.frombuffer(bytes(bytestream), dtype=numpy.uint8), cursor.index)
        cursor.index += len(bytestream)
        
        fUniqueID = 0
        fBits = 33554432
        cursor.write_fields(sink, ">II", fUniqueID, fBits)
