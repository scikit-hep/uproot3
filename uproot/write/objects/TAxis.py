from uproot.write.key import Key

class JunkKey(Key):

    def __init__(self, string):
        self.string = string
        self.fVersion = 4
        self.fObjlen = 108 + len(self.string)
        self.fDatime = 1573188772
        self.fKeylen = 0
        self.fNbytes = self.fObjlen + self.fKeylen
        self.fCycle = 1
        self.fSeekKey = 0
        self.fSeekPdir = 100
        self.packer = ">ihiIhhii"
        self.fClassName = b"TAxis"
        self.fName = self.string
        self.fTitle = b""
        Key.__init__(self, self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle,
                     self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle)


from uproot.write.key import Key as SuperKey

class Key(SuperKey):

    def __init__(self, string, stringloc):
        self.string = string
        self.fVersion = 4
        self.fObjlen = 108 + len(self.string)
        self.fDatime = 1573188772
        self.fKeylen = 0
        self.fNbytes = self.fObjlen + self.fKeylen
        self.fCycle = 1
        self.fSeekKey = stringloc
        self.fSeekPdir = 100
        self.packer = ">ihiIhhii"
        self.fClassName = b"TAxis"
        self.fName = self.string
        self.fTitle = b""
        SuperKey.__init__(self, self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle,
                     self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle)


import numpy

class TAxis(object):

    def __init__(self, fNbins, fXmin, fXmax):
        self.string = ""
        self.fNbins = fNbins
        self.fXmin = fXmin
        self.fXmax = fXmax

    def write_bytes(self, cursor, sink):
        cnt = 1073741928 + len(self.string)
        vers = 10
        packer = ">IH"
        cursor.write_fields(sink, packer, cnt, vers)
        
        cnt = 1073741838 + len(self.string)
        vers = 1
        packer = ">IH"
        cursor.write_fields(sink, packer, cnt, vers)
        
        bytestream = [0, 1, 0, 0, 0, 0, 2, 0, 0, 0]
        sink.write(numpy.frombuffer(bytes(bytestream), dtype=numpy.uint8), cursor.index)
        cursor.index += len(bytestream)
        
        cursor.write_strings(self.string)
        
        bytestream = [64, 0, 0, 36, 0, 4, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0, 61, 76, 204, 205, 0, 1, 0,
                      42, 0]
        sink.write(numpy.frombuffer(bytes(bytestream), dtype=numpy.uint8), cursor.index)
        cursor.index += len(bytestream)
        
        cursor.write_fields(sink, ">idd", self.fNbins, self.fXmin, self.fXmax)
        
        bytestream = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sink.write(numpy.frombuffer(bytes(bytestream), dtype = numpy.uint8), cursor.index)
        cursor.index += len(bytestream)
