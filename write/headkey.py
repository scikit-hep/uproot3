class HeadKey(object):

    def __init__(self, fNbytes,fSeekKey, fName):
        self.packer = ">ihiIhhii"
        self.fVersion = 4
        self.fNbytes = fNbytes
        self.fObjlen = 0
        self.fDatime = 1573188772
        self.fKeylen = 0
        self.fCycle = 1
        self.fSeekKey = fSeekKey
        self.fSeekPdir = 100
        self.fClassName = b'TFile'
        self.fName = fName
        self.fTitle = b''

    def values(self):
        return self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle