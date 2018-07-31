class Begin_Key(object):
    
    def __init__(self, fName):
        self.fNbytes = 0
        self.fVersion = 4
        self.fObjlen = 0
        self.fDatime = 1573188772
        self.fKeylen = 0
        self.fCycle = 1
        self.fSeekKey = 100
        self.fSeekPdir = 0
        self.packer = ">ihiIhhii"
        self.fClassName = b'TFile'
        self.fName = fName
        self.fTitle = b''
        
    def values(self):
        return self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle
    