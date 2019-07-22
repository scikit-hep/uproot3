#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct
from copy import copy

import numpy

import uproot
import uproot.const
import uproot.write.compress
import uproot.write.sink.cursor

class TTree(object):

    def __init__(self, name, title, *branches, **options):
        self.fName = self.fixstring(name)
        self.fTitle = self.fixstring(title)

    @staticmethod
    def fixstring(string):
        if isinstance(string, bytes):
            return string
        else:
            return string.encode("utf-8")

    @staticmethod
    def emptyfields():
        return {"_fUniqueID": 1,
                "_fBits": 0,
                "_fLineColor": 0,
                "_fLineStyle": 0,
                "_fLineWidth": 0,
                "_fEntries": 0.0,
                "_fTotBytes": 0.0,
                "_fZipBytes": 0.0,
                "_fSavedBytes": 0.0,
                "_fFlushedBytes": 0.0,
                "_fWeight": 0.0,
                "_fTimerInterval": 0,
                "_fScanField": 0,
                "_fUpdate": 0,
                "_fDefaultEntryOffsetLen": 0,
                "_fNClusterRange": 0,
                "_fMaxEntries": 0.0,
                "_fMaxEntryLoop": 0.0,
                "_fMaxVirtualSize": 0.0,
                "_fAutoSave": 0.0,
                "_fAutoFlush": 0.0,
                "_fEstimate": 0.0,
                "_fClusterRangeEnd": [], #Pointer value, have to handle differently
                "_fClusterSize": [], #Pointer value, have to handle differently
                "_fIOBits": "",
                "_fLowerBound": 0,
                "_fLast": 0,
                }

    _format_cntvers = struct.Struct(">IH")

    _format_tobject1 = struct.Struct(">HII")
    def put_tobject(self, cursor):
        return cursor.put_fields(self._format_tobject1, 1, 0, numpy.uint32(0x03000000))

    def put_tnamed(self, cursor, name, title):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        buff = (self.put_tobject(cursor) +
                cursor.put_string(name) + cursor.put_string(title))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattline = struct.Struct(">hhh")
    def put_tattline(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattline,
                                  self.fields["_fLineColor"],
                                  self.fields["_fLineStyle"],
                                  self.fields["_fLineWidth"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattfill = struct.Struct(">hh")
    def put_tattfill(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattfill,
                                  self.fields["_fFillColor"],
                                  self.fields["_fFillStyle"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattmarker = struct.Struct(">hhf")
    def put_tattmarker(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattmarker,
                                  self.fields["_fMarkerColor"],
                                  self.fields["_fMarkerStyle"],
                                  self.fields["_fMarkerSize"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_rootiofeatures = struct.Struct(">B")
    def put_rootiofeatures(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        buff = cursor.put_fields(self._format_rootiofeatures, self.fields["_fIOBits"])
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tlist1 = struct.Struct(">i")
    _format_tlist2 = struct.Struct(">B")
    def put_tlist(self, cursor, values):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 5
        buff = b""
        givenbytes = (self.put_tobject(cursor) +
                      cursor.put_string(b"") +
                      cursor.put_fields(self._format_tlist1, len(values)))
        for value in values:
            buff += self.util.put_objany(cursor, (value, "TObjString"), self.keycursor)
            buff += cursor.put_fields(self._format_tlist2, 0)
            buff += b"" # cursor.bytes(source, n)
        givenbytes += buff
        length = len(givenbytes) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + givenbytes

    _format_tleaf1 = struct.Struct('>iii??')
    def put_tleaf(self, cursor, name, title):
        vers = 2
        buff = (self.put_tnamed(cursor, self.fName, self.fTitle) +
                cursor.put_fields(self._format_tleaf1, self.fields["_fLen,"], self.fields["_fLenType"], self.fields["_fOffset"],
                                  self.fields["_fIsRange"], self.fields["_fIsUnsigned"]))

        #cnt =
        pass

    #FIXME
    _format_tobjarray = struct.Struct(">ii")
    def return_tobjarray(self, cursor):
        cnt = numpy.int64(self.length_tobjarray() - 4) | uproot.const.kByteCountMask
        vers = 3
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                self.return_tobject(cursor) +
                cursor.return_string(b"") +
                cursor.return_fields(self._format_tobjarray, self.fields["_fLowerBand"], self.fields["_fLast"]))
                # _readobjany?
    def length_tobjarray(self):
        return self.le

    #FIXME
    _format_ttree = struct.Struct(">qqqqqdiiiiiqqqqqq")
    def return_ttree(self, cursor, name):
        cnt = numpy.int64(self.length_ttree() - 4) | uproot.const.kByteCountMask
        vers = 20
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                self.put_tnamed(cursor, name, self.fTitle) +
                self.put_tattline(cursor)) #Incomplete

    def write(self, context, cursor, name, compression, key, keycursor, util):
        self.keycursor = keycursor
        self.util = util
        self.util.set_obj(self)



class branch(object):

    # Need to think about appropriate defaultBasketSize
    # Need to look at ROOT's default branch compression
    def __init__(self, type, name, title, defaultBasketSize=0, compression=uproot.write.compress.ZLIB(4)): #Fix defaultBasketSize
        self.type = type
        self.name = name
        self.title = title
        self.defaultBasketSize = defaultBasketSize
        self.compression = compression

        self.fields = self.emptyfields()

    def append(self, item):
        self.extend(item)

    def extend(self, items):
        raise NotImplementedError

    def basket(self, items):
        raise NotImplementedError

    @staticmethod
    def emptyfields():
        return {"fCompress" : 0,
                "fBasketSize" : 0,
                "fEntryOffsetLen": 0,
                "fWriteBasket": 0,
                "fEntryNumber": 0.0,
                "fOffSet": 0,
                "fMaxBaskets": 0,
                "fSplitLevel": 0,
                "fEntries": 0.0,
                "fFirstEntry": 0.0,
                "fTotBytes": 0.0,
                "fZipBytes": 0.0,
                "fBasketBytes": [],
                "fBasketEntry": [],
                "fBasketSeek": []}

    _format_cntvers = struct.Struct(">IH")

    branch_format1 = struct.Struct('>iiiiq')

    _format_tobject1 = struct.Struct(">HII")
    def put_tobject(self, cursor):
        return cursor.put_fields(self._format_tobject1, 1, 0, numpy.uint32(0x03000000))

    def put_tnamed(self, cursor, name, title):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        buff = (self.put_tobject(cursor) +
                cursor.put_string(name) + cursor.put_string(title))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    def write(self):
        


