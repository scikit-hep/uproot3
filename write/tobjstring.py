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
        
        
        #TStreamerInfo Streamer
        self.pointer.skip(1)

        cnt =  1073742146
        vers =  9
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)

        cnt =  1073741848
        vers =  1
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.numbers(self.pointer, packer, version)

        fUniqueID = 0
        fBits =  50397184
        packer = ">II"
        self.pusher.numbers(self.pointer, packer, fUniqueID, fBits)

        name = b'TObjString'
        title = b''
        self.pusher.stringer(self.pointer, name)
        self.pusher.stringer(self.pointer, title)

        fCheckSum =  2626570240
        fClassVersion = 1
        packer = ">Ii"
        self.pusher.numbers(self.pointer, packer, fCheckSum, fClassVersion)

        bcnt =  1073742104
        packer = ">I"
        self.pusher.numbers(self.pointer, packer, bcnt)

        tag =  4294967295
        packer = ">I"
        self.pusher.numbers(self.pointer, packer, tag)

        cname = b"TObjArray"
        self.pusher.cnamer(self.pointer, cname)
        
        
        #TObjArray Streamer
        self.pointer.skip(1)

        cnt =  1073742086
        vers =  3
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.numbers(self.pointer, packer, version)

        fUniqueID =  0
        fBits =  33554432
        packer = ">II"
        self.pusher.numbers(self.pointer, packer, fUniqueID, fBits)

        name =  b''
        self.pusher.stringer(self.pointer, name)
        size =  2
        low =  0
        packer = ">ii"
        self.pusher.numbers(self.pointer, packer, size, low)

        bcnt =  1073741941
        packer = ">I"
        self.pusher.numbers(self.pointer, packer, bcnt)

        tag =  4294967295
        packer = ">I"
        self.pusher.numbers(self.pointer, packer, tag)

        cname =  b"TStreamerBase"
        self.pusher.cnamer(self.pointer, cname)
        
        
        #TStreamerBase Streamer
        self.pointer.skip(1)

        cnt =  1073741919
        vers =  3
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)
        
        
        #TStreamerElement Streamer
        cnt =  1073741909
        vers =  4
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)

        cnt =  1073741862
        vers =  1
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.numbers(self.pointer, packer, version)

        fUniqueID =  0
        fBits =  50331648
        packer = ">II"
        self.pusher.numbers(self.pointer, packer, fUniqueID, fBits)

        name = b'TObject'
        title = b'Basic ROOT object'
        self.pusher.stringer(self.pointer, name)
        self.pusher.stringer(self.pointer, title)

        fType =  66
        fSize =  0
        fArrayLength =  0
        fArrayDim =  0
        packer = ">iiii"
        self.pusher.numbers(self.pointer, packer, fType, fSize, fArrayLength, fArrayDim)

        fMaxIndex =  [0, -1877229523, 0, 0, 0]
        packer = ">i"
        self.pusher.array_pusher(self.pointer, packer, fMaxIndex)

        fTypeName =  b'BASE'
        self.pusher.stringer(self.pointer, fTypeName)

        fBaseVersion =  1
        packer = ">i"
        self.pusher.numbers(self.pointer, packer, fBaseVersion)

        bcnt =  1073741940
        packer = ">I"
        self.pusher.numbers(self.pointer, packer, bcnt)

        tag =  4294967295
        packer = ">I"
        self.pusher.numbers(self.pointer, packer, tag)

        cname =  b"TStreamerString"
        self.pusher.cnamer(self.pointer, cname)
        
        
        #TStreamerString Streamer
        self.pointer.skip(1)

        cnt =  1073741916
        vers =  2
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)
        
        
        #TStreamerElement Streamer
        cnt =  1073741910
        vers =  4
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)

        cnt =  1073741860
        vers =  1
        packer = ">IH"
        self.pusher.numbers(self.pointer, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.numbers(self.pointer, packer, version)

        fUniqueID =  0
        fBits =  50331648
        packer = ">II"
        self.pusher.numbers(self.pointer, packer, fUniqueID, fBits)

        name = b'fString'
        title = b'wrapped TString'
        self.pusher.stringer(self.pointer, name)
        self.pusher.stringer(self.pointer, title)

        fType =  65
        fSize =  24
        fArrayLength =  0
        fArrayDim =  0
        packer = ">iiii"
        self.pusher.numbers(self.pointer, packer, fType, fSize, fArrayLength, fArrayDim)

        fMaxIndex =  [0, 0, 0, 0, 0]
        packer = ">i"
        self.pusher.array_pusher(self.pointer, packer, fMaxIndex)

        fTypeName =  b'TString'
        self.pusher.stringer(self.pointer, fTypeName)

        n =  0
        packer = ">B"
        self.pusher.numbers(self.pointer, packer, n)

        self.pusher.empty_array_pusher(self.pointer)



        
        

        
        
        