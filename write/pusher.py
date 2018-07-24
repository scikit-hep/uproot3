from write.utils import resizer

class Pusher(object):
    
    def __init__(self, file):
        self.file = file
    
    def numbers(self, cursor, packer, *args):
        toadd = cursor.push(packer, *args)
        if cursor.index > self.file.size:
            self.file = resizer(self.file, cursor.index+1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def stringer(self, cursor, toput):
        self.file[cursor.index] = cursor.precheck(toput)
        cursor.skip(1)
        toadd = cursor.string(toput)
        if cursor.index > self.file.size:
            self.file = resizer(self.file, cursor.index+1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
    
    def cnamer(self, cursor, toput):
        toadd = cursor.string(toput)
        if cursor.index > self.file.size:
            self.file = resizer(self.file, cursor.index+1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def array_pusher(self, cursor, packer, array):
        toadd = cursor.array_place(packer, array)
        if cursor.index > self.file.size:
            self.file = resizer(self.file, cursor.index+1)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def empty_array_pusher(self, cursor):
        toadd = cursor.empty_array()
        if cursor.index > self.file.size:
            self.file = resizer(self.file, cursor.index+1)
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
        
    def empty_fill(self, size):
        self.file = resizer(self.file, size+1)
        
        