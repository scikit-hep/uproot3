class TAxisStreamers(object):

    def __init__(self, sink, pos):
        self.sink = sink
        self.pos = pos

    def write(self):
        bcnt = 1073743484
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag = 4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        cname = "TStreamerInfo"
        self.sink.set_cname(self.pos, cname)
        self.pos = self.sink.file.tell()

        # TStreamerInfo Streamer
        cnt = 1073743462
        vers = 9
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # Name Title
        cnt = 1073741843
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID = 0
        fBits = 50397184
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b"TAxis"
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()

        title = b""
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()

        fCheckSum = 1514761840
        fClassVersion = 10
        packer = ">Ii"
        self.sink.set_numbers(self.pos, packer, fCheckSum, fClassVersion)
        self.pos = self.sink.file.tell()

        bcnt = 1073743425
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag = 4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        # TObjArray Streamer
        cnt = 1073743407
        vers = 3
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # skiptobj
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
        self.sink.set_string(self.pos, name)
        self.pos = self.sink.file.tell()

        size = 13
        low = 0
        packer = ">ii"
        self.sink.set_numbers(self.pos, packer, size, low)
        self.pos = self.sink.file.tell()

        bcnt = 1073741965
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag = 4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        cname = "TStreamerBase"
        self.sink.set_cname(self.pos, cname)
        self.pos = self.sink.file.tell()

        # TStreamerBase
        cnt = 1073741943
        vers = 3
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # TStreamerElement
        cnt = 1073741933
        vers = 3
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # Name Title
        cnt = 1073741886
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID = 0
        fBits = 50331648
        packer = "II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b"TNamed"
        self.sink.set_string(self.pos, name)
        self.pos = self.sink.file.tell()

        title = b"The basis for a named object (name, title)"
        self.sink.set_string(self.pos, title)
        self.pos = self.sink.file.tell()

        fType = 67
        fSize = 0
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()

        fMaxIndex = [0, -541636036, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()

        fTypeName = b"BASE"
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()

        fBaseVersion = 1
        packer = ">i"
        self.sink.set_strings(self.pos, packer, fBaseVersion)
        self.pos = self.sink.file.tell()

        bcnt = 1073741926
        packer = ">I"
        self.sink.set_strings(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag = 2147483841
        packer = ">I"
        self.sink.set_strings(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        # TStreamerBase Streamer
        cnt = 1073741918
        vers = 3
        packer = ">IH"
        self.sink.set_strings(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # TStreamerElement Streamer
        cnt = 1073741908
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # Name Title
        cnt = 1073741861
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b"TAttAxis"
        self.sink.set_string(self.pos, name)
        self.pos = self.sink.file.tell()

        title = b"Axis attributes"
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()

        fType = 0
        fSize = 0
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()

        fMaxIndex = [0, 1550843710, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()
        
        fTypeName = b"BASE"
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()
        
        fBaseVersion = 4
        packer = ">i"
        self.sink.set_numbers(self.pos, packer, fBaseVersion)
        self.pos = self.sink.file.tell()
        
        bcnt = 1073741937
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()
        
        tag = 4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()
        
        cname = "TStreamerBasicType"
        self.sink.set_cname(self.pos, cname)
        self.pos = self.sink.file.tell()
        
        # TStreamerBasicType Streamer
        cnt = 1073741910
        vers = 2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # TStreamerElement Streamer
        cnt = 1073741904
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # Name Title
        cnt = 1073741848
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()
        
        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()
        
        name = b"fNbins"
        self.sink.set_string(self.pos, name)
        self.pos = self.sink.file.tell()
         
        title = b"Number of bins"
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()
        
        fType = 3
        fSize = 4
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()
        
        fMaxIndex = [0, 0, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()
        
        fTypeName = b"int"
        self.sink.set_string(self.pos, fTypeName)
        self.pos = self.sink.file.tell()
        
        bcnt = 1073741927
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()
        
        tag = 2147484092
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()
        
        # TStreamerBasicType
        cnt = 1073741919
        vers = 2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # TStreamerElement
        cnt = 1073741913
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # Name Title
        cnt = 1073741864
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()
        
        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()
        
        name = b"fXmin"
        self.sink.set_string(self.pos, name)
        self.pos = self.sink.file.tell()
        
        title = b"low edge of first bin"
        self.sink.set_string(self.pos, title)
        self.pos = self.sink.file.tell()
        
        fType = 8
        fSize = 8
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()
        
        fMaxIndex = [0, 0, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()
        
        fTypeName = b"double"
        self.sink.set_string(self.pos, fTypeName)
        self.pos = self.sink.file.tell()
        
        bcnt = 1073741928
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()
        
        tag = 2147484092
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()
        
        # TStreamerBasicType
        cnt = 1073741920
        vers = 2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # TStreamerElement
        cnt = 1073741914
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # Name Title
        cnt = 1073741865
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()
        
        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()
        
        name = b"fXmax"
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()
        
        title = b"upper edge of last bin"
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()
        
        fType = 8
        fSize = 8
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_strings(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()
        
        fMaxIndex = [0, 0, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()
        
        fTypeName = b"double"
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()
      
        bcnt = 1073741947
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()
        
        tag = 4294967295
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()
        
        cname = "TStreamerObjectAny"
        self.sink.set_string(self.pos, cname)
        self.pos = self.sink.file.tell()
        
        # TStreamerObjectAny
        cnt = 1073741920
        vers = 2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # TStreamerElement
        cnt = 1073741914
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # Name Title
        cnt = 1073741864
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()
        
        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()
        
        name = b"fXbins"
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()
        
        title = b"Bin edges array in X"
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()
        
        fType = 62
        fSize = 24
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()
        
        fMaxIndex = [0, 0, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()
        
        fTypeName = b"TArrayD"
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()
        
        bcnt = 1073741924
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()
        
        tag = 2147484092
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()
        
        # TStreamerBasicType
        cnt = 1073741916
        vers = 2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # TStreamerElement
        cnt = 1073741910
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # Name Title
        cnt = 1073741864
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()
        
        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()
        
        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()
        
        name = b"fFirst"
        self.sink.set_string(self.pos, name)
        self.pos = self.sink.file.tell()
        
        title = b"first bin to display"
        self.sink.set_string(self.pos, title)
        self.pos = self.sink.file.tell()
        
        fType = 3
        fSize = 4
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()

        fMaxIndex = [0, 0, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()

        fTypeName = b"int"
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()

        bcnt = 1073741922
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag = 2147484092
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        # TStreamerBasicType
        cnt = 1073741914
        vers = 2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # TStreamerElement
        cnt = 1073741908
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # Name Title
        cnt = 1073741862
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b"fLast"
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()

        title = b"last bin to display"
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()

        fType = 3
        fSize = 4
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()

        fMaxIndex = [0, 0, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()

        fTypeName = b"int"
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()

        bcnt = 1073741937
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag = 2147484092
        packer = ">I"
        self.sink.set_numbers(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        # TStreamerBasicType
        cnt = 1073741929
        vers = 2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # TStreamerElement
        cnt = 1073741923
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # Name Title
        cnt = 1073741866
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        # skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numbers(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        name = b"fBits2"
        self.sink.set_strings(self.pos, name)
        self.pos = self.sink.file.tell()

        title = b"second bit status word"
        self.sink.set_strings(self.pos, title)
        self.pos = self.sink.file.tell()

        fType = 12
        fSize = 2
        fArrayLength = 0
        fArrayDim = 0
        packer = ">iiii"
        self.sink.set_numbers(self.pos, packer, fType, fSize, fArrayLength, fArrayDim)
        self.pos = self.sink.file.tell()

        fMaxIndex = [0, 0, 0, 0, 0]
        packer = ">i4"
        self.sink.set_array(self.pos, packer, fMaxIndex)
        self.pos = self.sink.file.tell()

        fTypeName = b"unsigned short"
        self.sink.set_strings(self.pos, fTypeName)
        self.pos = self.sink.file.tell()

        bcnt = 1073741960
        packer = ">I"
        self.sink.set_strings(self.pos, packer, bcnt)
        self.pos = self.sink.file.tell()

        tag = 2147484092
        packer = ">I"
        self.sink.set_strings(self.pos, packer, tag)
        self.pos = self.sink.file.tell()

        #TStreamerBasicType
        cnt = 1073741952
        vers = 2
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        #TStreamerElement
        cnt = 1073741946
        vers = 4
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        #Name Title
        cnt = 1073741899
        vers = 1
        packer = ">IH"
        self.sink.set_numbers(self.pos, packer, cnt, vers)
        self.pos = self.sink.file.tell()

        #skiptobj
        version = 1
        packer = ">h"
        self.sink.set_numbers(self.pos, packer, version)
        self.pos = self.sink.file.tell()

        fUniqueID = 0
        fBits = 50331648
        packer = ">II"
        self.sink.set_numebrs(self.pos, packer, fUniqueID, fBits)
        self.pos = self.sink.file.tell()

        



        
