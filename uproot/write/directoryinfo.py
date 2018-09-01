class DirectoryInfo(object):
    
    def __init__(self, fNbytesName):
        self.fVersion = 5
        self.fDatimeC = 1573188772
        self.fDatimeM = 1573188772
        self.fNbytesKeys = 0
        self.fNbytesName = fNbytesName
        self.fSeekDir =  100
        self.fSeekParent =  0
        self.fSeekKeys = 0
        self.packer = ">hIIiiiii"
        
    def write_values(self, cursor, sink):
        cursor.write_fields(sink, packer, self.fVersion, self.fDatimeC, self.fDatimeM, self.fNbytesKeys, self.fNbytesName, self.fSeekDir, self.fSeekParent, self.fSeekKeys)
        
        