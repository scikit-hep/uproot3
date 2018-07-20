import numpy
import struct

class Pointer(object):

    def __init__(self, index, origin=0):
        self.index = index
        if origin is 0:
            self.origin = index
        else:
            self.origin = origin

    def skip(self, numbytes):
        self.index += numbytes
        self.origin += numbytes
        
    def push(self, packer, *args):
        toadd = numpy.frombuffer(struct.pack(packer, *args), dtype = numpy.uint8)
        self.index += len(toadd)
        return toadd
    
    def precheck(self, put):
        toadd = bytes(str(len(put)),"ascii")
        return toadd
    
    def string(self, put):
        toadd = numpy.frombuffer(put, dtype = numpy.uint8)
        self.index += len(toadd)
        return toadd
    
    def array_place(self, packer, array):
        buffer = bytearray()
        packer = ">i"
        for x in array:
            buffer = buffer + struct.pack(packer, x)
        toadd = numpy.frombuffer(buffer, dtype = numpy.uint8)
        self.index += len(toadd)
        return toadd
    
    def empty_array(self):
        data = bytearray()
        toadd = numpy.frombuffer(data, dtype = numpy.uint8)
        self.index += len(toadd)
        return toadd

    

