#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import collections
import struct
import uuid

import uproot.write.sink.cursor
import uproot.write.TKey
import uproot.write.util

class TDirectory(object):
    def __init__(self, tfile, fName, fNbytesName, fSeekDir=100, fSeekParent=0, fSeekKeys=0, allocationbytes=128, growfactor=8):
        self.tfile = tfile
        self.fName = fName
        self.fNbytesName = fNbytesName
        self.fNbytesKeys = self._format2.size
        self.fSeekDir = fSeekDir
        self.fSeekParent = fSeekParent
        self.fSeekKeys = fSeekKeys
        self.fDatimeC = uproot.write.util.datime()
        self.fUUID = b'\x00\x01' + uuid.uuid1().bytes

        self.allocationbytes = allocationbytes
        self.growfactor = growfactor

        self.headkey = uproot.write.TKey.TKey(fClassName = b"TFile",
                                              fName      = self.fName,
                                              fObjlen    = self._format2.size,
                                              fSeekKey   = self.fSeekKeys)
        self.keys = collections.OrderedDict()
        self.maxcycle = collections.Counter()

    def size(self):
        return uproot.write.sink.cursor.Cursor.length_string(self.fName) + 1 + self._format1.size + len(self.fUUID) + 12

    def update(self):
        fVersion = 5
        fDatimeM = uproot.write.util.datime()
        self.cursor.update_fields(self.sink, self._format1, fVersion, self.fDatimeC, fDatimeM, self.fNbytesKeys, self.fNbytesName, self.fSeekDir, self.fSeekParent, self.fSeekKeys)

    def write(self, cursor, sink):
        cursor.write_string(sink, self.fName)
        cursor.write_data(sink, b"\x00")

        self.cursor = uproot.write.sink.cursor.Cursor(cursor.index)
        self.sink = sink
        self.update()

        cursor.skip(self._format1.size)
        cursor.write_data(self.sink, self.fUUID)
        cursor.write_data(sink, b"\x00" * 12)   # FIXME! what is this?

    _format1 = struct.Struct(">hIIiiiii")
    _format2 = struct.Struct(">i")

    def _nbyteskeys(self):
        return self.headkey.fKeylen + self._format2.size + sum(x.fKeylen for x in self.keys.values())

    def writekeys(self, cursor):
        self.fSeekKeys = cursor.index
        self.fNbytesKeys = self._nbyteskeys()

        self.tfile._expandfile(uproot.write.sink.cursor.Cursor(self.fSeekKeys + self.allocationbytes))

        self.keycursor = uproot.write.sink.cursor.Cursor(self.fSeekKeys)
        self.headkey.write(self.keycursor, self.sink)
        self.nkeycursor = uproot.write.sink.cursor.Cursor(self.keycursor.index)
        self.keycursor.write_fields(self.sink, self._format2, len(self.keys))
        for key in self.keys.values():
            key.write(self.keycursor, self.sink)

        self.update()

    def newcycle(self, name):
        self.maxcycle[name] += 1
        return self.maxcycle[name]

    def setkey(self, newkey):
        newcursor = None
        if (newkey.fName, newkey.fCycle) in self.keys:
            self.headkey.fObjlen -= self.keys[(newkey.fName, newkey.fCycle)].fKeylen
            newcursor = uproot.write.sink.cursor.Cursor(self.fSeekKeys)

        self.headkey.fObjlen += newkey.fKeylen
        self.keys[(newkey.fName, newkey.fCycle)] = newkey

        self.fNbytesKeys = self._nbyteskeys()
        while self.fNbytesKeys > self.allocationbytes:
            self.allocationbytes *= self.growfactor
            newcursor = uproot.write.sink.cursor.Cursor(self.tfile._fSeekFree)

        if newcursor is not None:
            self.writekeys(newcursor)
        else:
            newkey.write(self.keycursor, self.sink)
            self.headkey.update()
            self.nkeycursor.update_fields(self.sink, self._format2, len(self.keys))
            self.update()

    def delkey(self, name, cycle):
        if cycle is None:
            for x in range(self.maxcycle[name]):
                self.delkey(name, x + 1)

        else:
            oldkey = self.keys[(name, cycle)]
            self.headkey.fObjlen -= oldkey.fKeylen
            del self.keys[(name, cycle)]

            self.fNbytesKeys = self._nbyteskeys()
            self.writekeys(uproot.write.sink.cursor.Cursor(self.fSeekKeys))
