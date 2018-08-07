class TObjStringStreamers(object):
    
    def __init__(self, pusher, cursor):
        self.pusher = pusher
        self.cursor = cursor
        
    def write(self):
        #TList Streamer
        cnt = 1073742190
        vers = 5
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.set_numbers(self.cursor, packer, version)

        fUniqueID =  0
        fBits =  33554432
        packer = ">II"
        self.pusher.set_numbers(self.cursor, packer, fUniqueID, fBits)
        
        name = b""
        self.pusher.set_strings(self.cursor, name)
        size = 1
        packer = ">i"
        self.pusher.set_numbers(self.cursor, packer, size)

        bcnt =  1073742168
        packer = ">I"
        self.pusher.set_numbers(self.cursor, packer, bcnt)

        tag =  4294967295
        packer = ">I"
        self.pusher.set_numbers(self.cursor, packer, tag)

        cname = b"TStreamerInfo"
        self.pusher.set_cname(self.cursor, cname)
        
        
        #TStreamerInfo Streamer
        self.cursor.skip(1)

        cnt =  1073742146
        vers =  9
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)

        cnt =  1073741848
        vers =  1
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.set_numbers(self.cursor, packer, version)

        fUniqueID = 0
        fBits =  50397184
        packer = ">II"
        self.pusher.set_numbers(self.cursor, packer, fUniqueID, fBits)

        name = b'TObjString'
        title = b''
        self.pusher.set_strings(self.cursor, name)
        self.pusher.set_strings(self.cursor, title)

        fCheckSum =  2626570240
        fClassVersion = 1
        packer = ">Ii"
        self.pusher.set_numbers(self.cursor, packer, fCheckSum, fClassVersion)

        bcnt =  1073742104
        packer = ">I"
        self.pusher.set_numbers(self.cursor, packer, bcnt)

        tag =  4294967295
        packer = ">I"
        self.pusher.set_numbers(self.cursor, packer, tag)

        cname = b"TObjArray"
        self.pusher.set_cname(self.cursor, cname)
        
        
        #TObjArray Streamer
        self.cursor.skip(1)

        cnt =  1073742086
        vers =  3
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.set_numbers(self.cursor, packer, version)

        fUniqueID =  0
        fBits =  33554432
        packer = ">II"
        self.pusher.set_numbers(self.cursor, packer, fUniqueID, fBits)

        name =  b''
        self.pusher.set_strings(self.cursor, name)
        size =  2
        low =  0
        packer = ">ii"
        self.pusher.set_numbers(self.cursor, packer, size, low)

        bcnt =  1073741941
        packer = ">I"
        self.pusher.set_numbers(self.cursor, packer, bcnt)

        tag =  4294967295
        packer = ">I"
        self.pusher.set_numbers(self.cursor, packer, tag)

        cname =  b"TStreamerBase"
        self.pusher.set_cname(self.cursor, cname)
        
        
        #TStreamerBase Streamer
        self.cursor.skip(1)

        cnt =  1073741919
        vers =  3
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)
        
        
        #TStreamerElement Streamer
        cnt =  1073741909
        vers =  4
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)

        cnt =  1073741862
        vers =  1
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.set_numbers(self.cursor, packer, version)

        fUniqueID =  0
        fBits =  50331648
        packer = ">II"
        self.pusher.set_numbers(self.cursor, packer, fUniqueID, fBits)

        name = b'TObject'
        title = b'Basic ROOT object'
        self.pusher.set_strings(self.cursor, name)
        self.pusher.set_strings(self.cursor, title)

        fType =  66
        fSize =  0
        fArrayLength =  0
        fArrayDim =  0
        packer = ">iiii"
        self.pusher.set_numbers(self.cursor, packer, fType, fSize, fArrayLength, fArrayDim)

        fMaxIndex =  [0, -1877229523, 0, 0, 0]
        packer = ">i"
        self.pusher.set_array(self.cursor, packer, fMaxIndex)

        fTypeName =  b'BASE'
        self.pusher.set_strings(self.cursor, fTypeName)

        fBaseVersion =  1
        packer = ">i"
        self.pusher.set_numbers(self.cursor, packer, fBaseVersion)

        bcnt =  1073741940
        packer = ">I"
        self.pusher.set_numbers(self.cursor, packer, bcnt)

        tag =  4294967295
        packer = ">I"
        self.pusher.set_numbers(self.cursor, packer, tag)

        cname =  b"TStreamerString"
        self.pusher.set_cname(self.cursor, cname)
        
        
        #TStreamerString Streamer
        self.cursor.skip(1)

        cnt =  1073741916
        vers =  2
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)
        
        
        #TStreamerElement Streamer
        cnt =  1073741910
        vers =  4
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)

        cnt =  1073741860
        vers =  1
        packer = ">IH"
        self.pusher.set_numbers(self.cursor, packer, cnt, vers)

        version = 1
        packer = ">h"
        self.pusher.set_numbers(self.cursor, packer, version)

        fUniqueID =  0
        fBits =  50331648
        packer = ">II"
        self.pusher.set_numbers(self.cursor, packer, fUniqueID, fBits)

        name = b'fString'
        title = b'wrapped TString'
        self.pusher.set_strings(self.cursor, name)
        self.pusher.set_strings(self.cursor, title)

        fType =  65
        fSize =  24
        fArrayLength =  0
        fArrayDim =  0
        packer = ">iiii"
        self.pusher.set_numbers(self.cursor, packer, fType, fSize, fArrayLength, fArrayDim)

        fMaxIndex =  [0, 0, 0, 0, 0]
        packer = ">i"
        self.pusher.set_array(self.cursor, packer, fMaxIndex)

        fTypeName =  b'TString'
        self.pusher.set_strings(self.cursor, fTypeName)

        n =  0
        packer = ">B"
        self.pusher.set_numbers(self.cursor, packer, n)

        self.pusher.set_empty_array(self.cursor)

