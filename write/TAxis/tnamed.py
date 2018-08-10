class TNamed(object):

    def __init__(self, sink, pos, string):
        self.sink = sink
        self.pos = pos
        self.string = string

    def write(self):
        cnt = 1073741930 #Check for bugs
        vers = 10
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        #TNamed
        cnt = 1073741840 #Check for bugs
        vers = 1
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
        self.sink.set_numbers(self.pos, fUniqueID, fBits, packer)
        self.pos = self.sink.file.tell()

        fName = self.string.encode("utf-8")
        self.sink.set_strings(self.pos, fName)
        self.pos = self.sink.file.tell()

        fTitle = b""
        self.sink.set_strings(self.pos, fTitle)
        self.pos = self.sink.file.tell()

        cnt = 1073741860
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        #TArray
        length = 0
        packer = ">i"
        self.sink.set_numbers(self.pos, packer, length)
        self.pos = self.sink.file.tell()

        bcnt = 0
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        bcnt = 0
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

