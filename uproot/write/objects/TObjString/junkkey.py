from write.key import Key

class JunkKey(Key):
    
    def __init__(self, string):
        self.string = string
        self.fVersion = 4
        self.fObjlen = 17 + len(self.string)
        self.fDatime = 1573188772
        self.fKeylen = 0
        self.fNbytes = self.fObjlen + self.fKeylen
        self.fCycle = 1
        self.fSeekKey = 0
        self.fSeekPdir = 100
        self.packer = ">ihiIhhii"
        self.fClassName = b'TObjString'
        self.fName = self.string
        self.fTitle = b'Collectable string class'
        Key.__init__(self, self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle,
                     self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle)

