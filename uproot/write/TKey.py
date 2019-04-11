#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct

import uproot.write.sink.cursor
import uproot.write.util

class TKey(object):
    def __init__(self, fClassName, fName, fTitle=b"", fObjlen=0, fSeekKey=100, fSeekPdir=0, fCycle=1):
        self.fClassName = fClassName
        self.fName = fName
        self.fTitle = fTitle

        self.fObjlen = fObjlen
        self.fSeekKey = fSeekKey
        self.fSeekPdir = fSeekPdir
        self.fCycle = fCycle
        self.fDatime = uproot.write.util.datime()

    @property
    def fKeylen(self):
        return self._format1.size + uproot.write.sink.cursor.Cursor.length_strings([self.fClassName, self.fName, self.fTitle])

    @property
    def fNbytes(self):
        return self.fObjlen + self.fKeylen

    def update(self):
        self.cursor.update_fields(self.sink, self._format1, self.fNbytes, self._version, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)

    def write(self, cursor, sink):
        self.cursor = uproot.write.sink.cursor.Cursor(cursor.index)
        self.sink = sink

        self.update()

        cursor.skip(self._format1.size)
        cursor.write_string(sink, self.fClassName)
        cursor.write_string(sink, self.fName)
        cursor.write_string(sink, self.fTitle)

    _version = 1004
    _format1 = struct.Struct(">ihiIhhqq")

class TKey32(TKey):
    _version = 4
    _format1 = struct.Struct(">ihiIhhii")
