import numpy

class Sink(object):
    
    def __init__(self, file):
        self.file = file
    
    def set_numbers(self, cursor, packer, *args):
        toadd = cursor.push(packer, *args)
        if cursor.index > len(self.file):
            self.file.resize(cursor.index+1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def set_strings(self, cursor, toput):
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
    
    def set_cname(self, cursor, toput):
        toadd = cursor.read_string(toput)
        if cursor.index > len(self.file):
            self.file.resize(cursor.index + 1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def set_array(self, cursor, packer, array):
        toadd = cursor.array_place(packer, array)
        if cursor.index > len(self.file):
            self.file.resize(cursor.index + 1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def set_empty_array(self, cursor):
        toadd = cursor.empty_array()
        if cursor.index > len(self.file):
            self.file.resize(cursor.index + 1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def set_key(self, cursor, key):
        packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle = key.values()
        self.set_numbers(cursor, packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir)
        self.set_strings(cursor, fClassName)
        self.set_strings(cursor, fName)
        self.set_strings(cursor, fTitle)
        
    def set_directoryinfo(self, cursor, directory):
        cursor.skip(1)
        packer, fVersion, fDatimeC, fDatimeM, fNbytesKeys, fNbytesName = directory.first()
        self.set_numbers(cursor, packer, fVersion, fDatimeC, fDatimeM, fNbytesKeys, fNbytesName)
        packer, fSeekDir, fSeekParent, fSeekKeys = directory.second()
        self.set_numbers(cursor, packer, fSeekDir, fSeekParent, fSeekKeys)
        
    def set_header(self, cursor, header):
        packer, magic, fVersion = header.valuestop()
        self.set_numbers(cursor, packer, magic, fVersion)
        packer, fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo, fUUID = header.valuesbot()
        self.set_numbers(cursor, packer, fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo, fUUID)
        
    def set_object(self, cursor, Object):
        packer, cnt, vers = Object.values1()
        self.set_numbers(cursor, packer, cnt, vers)
        version, packer = Object.values2()
        self.set_numbers(cursor, packer, version)
        fUniqueID, fBits, packer = Object.values3()
        self.set_numbers(cursor, packer, fUniqueID, fBits)
        self.set_strings(cursor, Object.string)