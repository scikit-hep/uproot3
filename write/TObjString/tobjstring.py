import numpy

class TObjString(object):
    
    def __init__(self, string):
        self.string = string
        
    def values1(self):
        cnt = 17 + len(self.string) - 4
        kByteCountMask = numpy.int64(0x40000000)
        cnt = cnt | kByteCountMask
        vers = 1
        packer = ">IH"
        return packer, cnt, vers
    
    def values2(self):
        bytestream =[0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 11, 72, 101, 108, 108, 111, 32, 87, 111, 114, 108, 100]
        toadd = numpy.frombuffer(bytes(bytestream), dtype=numpy.uint8)
        return toadd
    
    def values3(self):
        fUniqueID = 0
        fBits = 33554432
        packer = ">II"
        return fUniqueID, fBits, packer