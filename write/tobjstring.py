class TObjString(object):
    
    def __init__(self, pusher, pointer):
        self.pusher = pusher
        self.pointer = pointer
        
    def write(self):
        #TList Streamer
        cnt = 1073742190
        vers = 5
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.numbers(self.pointer, packer, version)

        fUniqueID =  0
        fBits =  33554432
        packer = ">II"
        self.pusher.numbers(self.pointer, packer, fUniqueID, fBits)
        
        name = b""
        self.pusher.stringer(self.pointer, name)
        size = 1
        packer = ">i"
        self.pusher.numbers(self.pointer, packer, size)

        bcnt =  1073742168
        packer = ">I"
        self.pusher.numbers(self.pointer, packer, bcnt)

        tag =  4294967295
        packer = ">I"
        self.pusher.numbers(self.pointer, packer, tag)

        cname = b"TStreamerInfo"
        self.pusher.cnamer(self.pointer, cname)
        
        