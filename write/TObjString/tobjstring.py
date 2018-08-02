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
        version = 1
        packer = ">h"
        return version, packer
    
    def values3(self):
        fUniqueID = 0
        fBits = 33554432
        packer = ">II"
        return fUniqueID, fBits, packer