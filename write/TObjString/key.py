from write.key import Key as SuperKey

class Key(SuperKey):

    def __init__(self, keystring, string, stringloc):
        self.fVersion = 4
        self.fObjlen = 17 + len(string)
        self.fDatime = 1573188772
        self.fKeylen = 0
        self.fNbytes = self.fObjlen + self.fKeylen
        self.fCycle = 1
        self.fSeekKey = stringloc
        self.fSeekPdir = 100
        self.packer = ">ihiIhhii"
        self.fClassName = b'TObjString'
        self.fName = keystring
        self.fTitle = b'Collectable string class'
        SuperKey.__init__(self, self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle,
                     self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle)

