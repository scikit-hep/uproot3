from write.pointer import Pointer

class Pusher(object):
    
    def __init__(self, file):
        self.file = file
    
    def numbers(self, cursor, packer, *args):
        toadd = cursor.push(packer, *args)
        self.file[cursor.origin:cursor.index] = toadd
        cursor.origin = cursor.index
        
    def stringer(self, cursor, toput):
        cursor, self.file[cursor.index] = cursor.precheck(toput)
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
        
        
        
        
