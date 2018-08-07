import numpy

class Sink(object):
    
    def __init__(self, file):
        self.file = file
    
    def numbers(self, cursor, packer, *args):
        toadd = cursor.push(packer, *args)
        if cursor.index > len(self.file):
            self.file.resize(cursor.index+1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def stringer(self, cursor, toput):
        self.file.resize(len(self.file) + 1)
        try:
            self.file[cursor.index] = cursor.precheck(toput)
        except(IndexError):
            self.file.resize(len(self.file) + 1)
            self.file[cursor.index] = cursor.precheck(toput)
        cursor.skip(1)
        toadd = cursor.read_string(toput)
        if cursor.index > len(self.file):
            self.file.resize(cursor.index + 1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
    
    def cnamer(self, cursor, toput):
        toadd = cursor.read_string(toput)
        if cursor.index > len(self.file):
            self.file.resize(cursor.index + 1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def array_pusher(self, cursor, packer, array):
        toadd = cursor.array_place(packer, array)
        if cursor.index > len(self.file):
            self.file.resize(cursor.index + 1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def empty_array_pusher(self, cursor):
        toadd = cursor.empty_array()
        if cursor.index > len(self.file):
            self.file.resize(cursor.index + 1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def keyer(self, cursor, key):
        packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle = key.values()
        self.numbers(cursor, packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir)
        self.stringer(cursor, fClassName)
        self.stringer(cursor, fName)
        self.stringer(cursor, fTitle)
        
    def director(self, cursor, directory):
        cursor.skip(1)
        packer, fVersion, fDatimeC, fDatimeM, fNbytesKeys, fNbytesName = directory.first()
        self.numbers(cursor, packer, fVersion, fDatimeC, fDatimeM, fNbytesKeys, fNbytesName)
        packer, fSeekDir, fSeekParent, fSeekKeys = directory.second()
        self.numbers(cursor, packer, fSeekDir, fSeekParent, fSeekKeys)
        
    def head_push(self, cursor, header):
        packer, magic, fVersion = header.valuestop()
        self.numbers(cursor, packer, magic, fVersion)
        packer, fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo, fUUID = header.valuesbot()
        self.numbers(cursor, packer, fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo, fUUID)
        
    def push_object(self, cursor, Object):
        packer, cnt, vers = Object.values1()
        self.numbers(cursor, packer, cnt, vers)
        version, packer = Object.values2()
        self.numbers(cursor, packer, version)
        fUniqueID, fBits, packer = Object.values3()
        self.numbers(cursor, packer, fUniqueID, fBits)
        self.stringer(cursor, Object.string)