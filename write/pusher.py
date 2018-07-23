from write.pointer import Pointer
from write.first_key import First_Key

class Pusher(object):
    
    def __init__(self, file):
        self.file = file
    
    def numbers(self, cursor, packer, *args):
        toadd = cursor.push(packer, *args)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def stringer(self, cursor, toput):
        self.file[cursor.index] = cursor.precheck(toput)
        cursor.skip(1)
        toadd = cursor.string(toput)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
    
    def cnamer(self, cursor, toput):
        toadd = cursor.string(toput)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def array_pusher(self, cursor, packer, array):
        toadd = cursor.array_place(packer, array)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def empty_array_pusher(self, cursor):
        toadd = cursor.empty_array()
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def first_keyer(self, cursor, fNbytes, fObjlen):
        packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle = First_Key(cursor, fNbytes, fObjlen).values()
        self.numbers(cursor, packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir)
        self.stringer(cursor, fClassName)
        self.stringer(cursor, fName)
        self.stringer(cursor, fTitle)
        
        
        
        
