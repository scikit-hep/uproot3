class Header(object):
    
    def __init__(self, bytename, fCompress, fSeekInfo = 0):
        self.magic = b"root"
        self.fVersion = 61400
        self.fBEGIN = 100
        self.fEND = 1
        self.fSeekFree = 1
        self.fNbytesFree = self.fEND - self.fSeekFree
        self.nfree = 1
        self.fNbytesName = 36 + (2*(len(bytename)))
        self.fUnits = 4
        self.fCompress = fCompress
        self.fSeekInfo = fSeekInfo
        self.fNbytesInfo = 0
        self.fUUID = b"\x00\x010\xd5\xf5\xea~\x0b\x11\xe8\xa2D~S\x1f\xac\xbe\xef"
        
    def get_values1(self):
        packer = ">4si"
        return packer, self.magic, self.fVersion
    
    def get_values2(self):
        if self.fVersion < 1000000:
            packer = ">iiiiiiBiii18s"
        else:                
            packer = ">iqqiiiBiqi18s"
        return packer, self.fBEGIN, self.fEND, self.fSeekFree, self.fNbytesFree, self.nfree, self.fNbytesName, self.fUnits, self.fCompress, self.fSeekInfo, self.fNbytesInfo, self.fUUID
        
        