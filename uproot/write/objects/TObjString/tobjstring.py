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