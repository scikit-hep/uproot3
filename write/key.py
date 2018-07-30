class Key(object):
    
    def __init__(self, packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle):
        self.packer = packer
        self.fVersion = fVersion
        self.fNbytes = fNbytes
        self.fObjlen = fObjlen
        self.fDatime = fDatime
        self.fKeylen = fKeylen
        self.fCycle = fCycle
        self.fSeekKey = fSeekKey
        self.fSeekPdir = fSeekPdir
        self.fClassName = fClassName
        self.fName = fName
        self.fTitle = fTitle
        
    def values(self):
        return self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle