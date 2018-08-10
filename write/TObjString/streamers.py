class TObjStringStreamers(object):
    
    def __init__(self, sink, pos):
        self.sink = sink
        self.pos = pos
        
    def write(self):

        bcnt =  1073742168
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag =  4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        cname = b"TStreamerInfo"
        self.sink.set_cname(self.pos, cname)
        self.pos = self.sink.file.tell()
        
        #TStreamerInfo Streamer
        self.pos += 1

        cnt =  1073742146
        vers =  9
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        cnt =  1073741848
        vers =  1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID = 0
        fBits =  50397184
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b'TObjString'
        title = b''
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()

        fCheckSum =  2626570240
        fClassVersion = 1
        packer = ">Ii"
        self.sink.set_numbers(self.pos, packer, fCheckSum, fClassVersion)
        self.pos = self.sink.file.tell()

        bcnt =  1073742104
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag =  4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        cname = b"TObjArray"
        self.sink.set_cname(self.pos, cname)
        self.pos = self.sink.file.tell()
        
        #TObjArray Streamer
        self.pos += 1

        cnt =  1073742086
        vers =  3
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID =  0
        fBits =  33554432
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name =  b''
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()
        size =  2
        low =  0
        packer = ">ii"
        self.sink.set_numbers(self.pos, packer, size, low)
        self.pos = self.sink.file.tell()

        bcnt =  1073741941
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag =  4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        cname =  b"TStreamerBase"
        self.sink.set_cname(self.pos, cname)
        self.pos = self.sink.file.tell()
        
        #TStreamerBase Streamer
        self.pos += 1

        cnt =  1073741919
        vers =  3
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        #TStreamerElement Streamer
        cnt =  1073741909
        vers =  4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        cnt =  1073741862
        vers =  1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID =  0
        fBits =  50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b'TObject'
        title = b'Basic ROOT object'
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()

        fType =  66
        fSize =  0
        fArrayLength =  0
        fArrayDim =  0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()

        fMaxIndex =  [0, -1877229523, 0, 0, 0]
        packer = ">i"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()

        fTypeName =  b'BASE'
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()

        fBaseVersion =  1
        packer = ">i"
        self.sink.set_numbers(self.pos, packer, fBaseVersion)
        self.pos = self.sink.file.tell()

        bcnt =  1073741940
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag =  4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        cname =  b"TStreamerString"
        self.sink.set_cname(self.pos, cname)
        self.pos = self.sink.file.tell()
        
        #TStreamerString Streamer
        self.pos += 1

        cnt =  1073741916
        vers =  2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        #TStreamerElement Streamer
        cnt =  1073741910
        vers =  4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        cnt =  1073741860
        vers =  1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID =  0
        fBits =  50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b'fString'
        title = b'wrapped TString'
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()

        fType =  65
        fSize =  24
        fArrayLength =  0
        fArrayDim =  0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()

        fMaxIndex =  [0, 0, 0, 0, 0]
        packer = ">i"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()

        fTypeName =  b'TString'
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()

        n =  0
        packer = ">B"
        self.sink.set_numbers(self.pos, packer, n)
        self.pos = self.sink.file.tell()

        self.sink.set_empty_array(self.pos)
        self.pos = self.sink.file.tell()

