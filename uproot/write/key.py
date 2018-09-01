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
        
    def write_key(self, cursor, sink):
        cursor.write_fields(sink, self.packer, self.fVersion, self.fNbytes, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)
        cursor.write_strings(sink, self.fClassName)
        cursor.write_strings(sink, self.fName)
        cursor.write_strings(sink, self.fTitle)
        
    def update_key(self, cursor, sink)
        cursor.update_fields(sink, self.packer, self.fVersion, self.fNbytes, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)
        cursor.update_strings(sink, self.fClassName)
        cursor.update_strings(sink, self.fName)
        cursor.update_strings(sink, self.fTitle)