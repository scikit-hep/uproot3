class AllStreamers(object):

    def __init__(self, sink, cursor, size=0):
        self.sink = sink
        self.cursor = cursor
        self.size = size

    def write(self):
        # TList Streamer
        cnt = 1073742190
        vers = 5
        packer = ">IH"
        self.sink.set_numbers(self.cursor, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.sink.set_numbers(self.cursor, packer, version)

        fUniqueID = 0
        fBits = 33554432
        packer = ">II"
        self.sink.set_numbers(self.cursor, packer, fUniqueID, fBits)

        name = b""
        self.sink.set_strings(self.cursor, name)
        packer = ">i"
        self.sink.set_numbers(self.cursor, packer, self.size)