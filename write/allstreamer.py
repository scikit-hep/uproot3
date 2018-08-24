import numpy

class AllStreamers(object):

    def __init__(self, sink, pos, size=0):
        self.sink = sink
        self.pos = pos
        self.size = size
        self.cnt = 1073741845

    def write(self):
        # TList Streamer
        cnt = self.cnt - 4
        kByteCountMask = numpy.int64(0x40000000)
        cnt = cnt | kByteCountMask
        vers = 5
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID = 0
        fBits = 33554432
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b""
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()
        packer = ">i"
        self.sink.set_numbers(self.pos, packer, self.size)