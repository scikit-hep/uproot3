#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

from __future__ import absolute_import

import struct

import uproot3.write.sink.cursor
import uproot3.write.util

class BasketKey(object):
    def __init__(self, fName, fTitle, fNevBuf, fNevBufSize, fObjlen=0, fSeekKey=100, fSeekPdir=0, fBufferSize=0):
        self.fClassName = b"TBasket"
        self.fName = fName
        self.fTitle = fTitle

        self.fObjlen = fObjlen
        self.fSeekKey = fSeekKey
        self.fSeekPdir = fSeekPdir
        self.fCycle = 0
        self.fDatime = uproot3.write.util.datime()
        self.fNbytes = self.fObjlen + self.fKeylen
        self.fBufferSize = fBufferSize
        self.fNevBuf = fNevBuf
        self.fNevBufSize = fNevBufSize

        self.old_fLast = 0

    @property
    def fKeylen(self):
        return self._format1.size + uproot3.write.sink.cursor.Cursor.length_strings([self.fClassName, self.fName, self.fTitle]) + self._format_basketkey.size + 1

    @property
    def fLast(self):
        return self.fKeylen + self.fObjlen

    def update(self):
        self.cursor.update_fields(self.sink, self._format1, self.fNbytes, self._version, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)

    def write(self, cursor, sink, isjagged=False):
        self.cursor = uproot3.write.sink.cursor.Cursor(cursor.index)
        self.sink = sink

        self.update()

        cursor.skip(self._format1.size)
        cursor.write_string(sink, self.fClassName)
        cursor.write_string(sink, self.fName)
        cursor.write_string(sink, self.fTitle)

        basketversion = 3
        if isjagged:
            if self.old_fLast == 0:
                raise Exception("isjagged flag should be False")
            cursor.write_fields(sink, self._format_basketkey, basketversion, self.fBufferSize, self.fNevBufSize, self.fNevBuf, self.old_fLast)
        else:
            cursor.write_fields(sink, self._format_basketkey, basketversion, self.fBufferSize, self.fNevBufSize, self.fNevBuf, self.fLast)
            self.old_fLast = self.fLast
        cursor.write_data(sink, b"\x00")

    _version = 1004
    _format1 = struct.Struct(">ihiIhhqq")
    _format_basketkey = struct.Struct(">Hiiii")

class TKey(object):
    def __init__(self, fClassName, fName, fTitle=b"", fObjlen=0, fSeekKey=100, fSeekPdir=0, fCycle=1):
        self.fClassName = fClassName
        self.fName = fName
        self.fTitle = fTitle

        self.fObjlen = fObjlen
        self.fSeekKey = fSeekKey
        self.fSeekPdir = fSeekPdir
        self.fCycle = fCycle
        self.fDatime = uproot3.write.util.datime()
        self.fNbytes = self.fObjlen + self.fKeylen

    @property
    def fKeylen(self):
        return self._format1.size + uproot3.write.sink.cursor.Cursor.length_strings([self.fClassName, self.fName, self.fTitle])

    def update(self):
        self.cursor.update_fields(self.sink, self._format1, self.fNbytes, self._version, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)

    def write(self, cursor, sink, isjagged=False):
        if isjagged:
            raise Exception("isjagged flag should be False")
        self.cursor = uproot3.write.sink.cursor.Cursor(cursor.index)
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
