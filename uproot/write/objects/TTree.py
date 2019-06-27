#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct

import numpy

import uproot.const
import uproot.write.compress
import uproot.write.sink.cursor

class TTree(object):

    def __init__(self, *branches, **options):
        self.fTitle = self.fixstring(ttree._fTitle)
        self.fClassName = self.fixstring(ttree._classname)

        self.fields = self.emptyfields()
        for n in list(self.fields):
            if hasattr(ttree, n):
                self.fields[n] = getattr(ttree, n)

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
    def return_tobject(self, cursor):
        return cursor.return_fields(self._format_tobject1, 1, 0, uproot.const.kNotDeleted)
    def length_tobject(self):
        return self._format_tobject1.size

    def return_tnamed(self, cursor, name, title):
        cnt = numpy.int64(self.length_tnamed(name, title) - 4) | uproot.const.kByteCountMask
        vers = 1
        return (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_tobject(cursor) +
                    cursor.return_string(name) + cursor.return_string(title))
    def length_tnamed(self, name, title):
        return self.length_tobject() + uproot.write.sink.cursor.Cursor.length_strings([name, title]) + self._format_cntvers.

    _format_tattline = struct.Struct(">hhh")
    def return_tattline(self, cursor):
        cnt = numpy.int64(self.length_tattline() - 4) | uproot.const.kByteCountMask
        vers = 2
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                cursor.return_fields(self._format_tattline,
                                     self.fields["_fLineColor"],
                                     self.fields["_fLineStyle"],
                                     self.fields["_fLineWidth"]))
    def length_tattline(self):
        return self._format_tattline.size + self._format_cntvers.size

    _format_tattfill = struct.Struct(">hh")
    def return_tattfill(self, cursor):
        cnt = numpy.int64(self.length_tattfill() - 4) | uproot.const.kByteCountMask
        vers = 2
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                cursor.return_fields(self._format_tattfill,
                                     self.fields["_fFillColor"],
                                     self.fields["_fFillStyle"]))
    def length_tattfill(self):
        return self._format_tattfill.size + self._format_cntvers.size

    _format_tattmarker = struct.Struct(">hhf")
    def return_tattmarker(self, cursor):
        cnt = numpy.int64(self.length_tattmarker() - 4) | uproot.const.kByteCountMask
        vers = 2
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                cursor.return_fields(self._format_tattmarker,
                                     self.fields["_fMarkerColor"],
                                     self.fields["_fMarkerStyle"],
                                     self.fields["_fMarkerSize"]))
    def length_tattmarker(self):
        return self._format_tattmarker.size + self._format_cntvers.size

    _format_rootiofeatures = struct.Struct(">B")
    def return_rootiofeatures(self, cursor):
        cnt = numpy.int64(self.length_tattmarker() - 4) | uproot.const.kByteCountMask
        vers = 1
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                cursor.return_fields(self._format_rootiofeatures, self.fields["_fIOBits"]))
    def length_rootiofeatures(self):
        return self._format_rootiofeatures.size + self._format_rootiofeatures.size

    _format_tlist = struct.Struct(">i")
    def return_tlist(self, cursor, values):
        cnt = numpy.int64(self.length_tlist(values) - 4) | uproot.const.kByteCountMask
        vers = 5
        for value in values:
            raise NotImplementedError
        return (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_tobject(cursor) +
            cursor.return_string(b"") + cursor.return_fields(self._format_tlist, len(values))) #FIXME
    def length_tlist(self, values):
        return self.length_tobject() + uproot.write.sink.cursor.Cursor.length_string(b"") + self._format_tlist.size + sum(0 for x in values) + self._format_cntvers.size

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

    _format_ttree = struct.Struct(">qqqqqdiiiiiqqqqqq")
    def return_ttree(self, cursor, name):
        cnt = numpy.int64(self.length_ttree() - 4) | uproot.const.kByteCountMask
        vers = 20
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                self.return_tnamed(cursor, name, self.fTitle) +
                self.return_tattline(cursor) +)

class branch(object):

    # Need to think about appropriate defaultBasketSize
    # Need to look at ROOT's default branch compression
    def __init__(self, type, name, title, defaultBasketSize=?, compression=uproot.ZLIB(4)):
        self.type = type
        self.name = name
        self.title = title
        self.defaultBasketSize = defaultBasketSize
        self.compression = compression

    def append(self, item):
        self.extend(item)

    def extend(self, items):
        raise NotImplementedError

    def basket(self, items):
        raise NotImplementedError
