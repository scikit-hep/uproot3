#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct
from copy import copy

import numpy

import uproot
import uproot.const
import uproot.write.compress
import uproot.write.sink.cursor

class newbranch(object):

    def __init__(self, type, flushsize=30000, title="", compression=None):
        self.name = ""
        self.type = type
        self.flushsize = flushsize
        self.title = title
        self.compression = compression

class newtree(object):

    def __init__(self, branches={}, flushsize=30000, title="", compression=None):
        self.branches = branches
        self.flushsize = flushsize
        self.title = title
        self.compression = compression

class TTree(object):

    def __init__(self, newtree):
        self.name = ""
        self.fClassName = b"TTree"
        self.fName = self.fixstring(self.name)
        self.fTitle = self.fixstring(newtree.title)

        self.branches = []
        for name, branch in newtree.branches.items():
            self.branches.append(TBranch(branch.type, name, branch.title, defaultBasketSize=32000, compression=branch.compression))

        self.fields = {"_fLineColor": 602,
                       "_fLineStyle": 1,
                       "_fLineWidth": 1,
                       "_fFillColor": 0,
                       "_fFillStyle": 1001,
                       "_fMarkerColor": 1,
                       "_fMarkerStyle": 1,
                       "_fMarkerSize": 1.0,
                       "_fEntries": 0,
                       "_fTotBytes": 0,
                       "_fZipBytes": 0,
                       "_fSavedBytes": 0,
                       "_fFlushedBytes": 0,
                       "_fWeight": 1.0,
                       "_fTimerInterval": 0,
                       "_fScanField": 25,
                       "_fUpdate": 0,
                       "_fDefaultEntryOffsetLen": 1000, #TODO: WHAT IS THIS?
                       "_fNClusterRange": 0,
                       "_fMaxEntries": 1000000000000, #TODO: HOW DOES THIS WORK?
                       "_fMaxEntryLoop": 1000000000000, #Same as fMaxEntries?
                       "_fMaxVirtualSize": 0,
                       "_fAutoSave": -300000000,
                       "_fAutoFlush": -30000000,
                       "_fEstimate": 1000000,
                       "_fClusterRangeEnd": [],
                       "_fClusterSize": [],
                       "_fBranches": [],
                       "_fFriends": None,
                       "_fTreeIndex": None,
                       "_fIndex": [],
                       "_fIndexValues": [],
                       "_fAliases": None,
                       "_fLeaves": [],
                       "_fUserInfo": None,
                       "_fBranchRef": None}

    @staticmethod
    def fixstring(string):
        if isinstance(string, bytes):
            return string
        else:
            return string.encode("utf-8")

    _format_cntvers = struct.Struct(">IH")

    _format_tobject1 = struct.Struct(">HII")
    def put_tobject(self, cursor, hexbytes):
        return cursor.put_fields(self._format_tobject1, 1, 0, hexbytes)

    def put_tnamed(self, cursor, name, title, hexbytes=numpy.uint32(0x03000000)):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        buff = (self.put_tobject(cursor, hexbytes) +
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
        vers = 0
        fIOBits = 0
        cursor.skip(4)
        buff = b"\x1a\xa1/\x10" + cursor.put_fields(self._format_rootiofeatures, fIOBits)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tobjarray1 = struct.Struct(">ii")
    def put_tobjarray(self, cursor, values, classname, fBits=50331648):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        buff = self._skiptobj(cursor, fBits)
        vers = 3
        try:
            size = len(values)
        except TypeError:
            size = 1
            values = [values]
        low = 0
        buff += cursor.put_string(b"") + cursor.put_fields(self._format_tobjarray1, size, low)
        for value in values:
            buff += self.util.put_objany(cursor, (value, classname), self.keycursor)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_skiptobj1 = struct.Struct(">h")
    _format_skiptobj2 = struct.Struct(">II")
    def _skiptobj(self, cursor, fBits):
        version = 1
        buff = cursor.put_fields(self._format_skiptobj1, version)
        fUniqueID = 0
        buff += cursor.put_fields(self._format_skiptobj2, fUniqueID, fBits)
        return buff

    _format_tarray = struct.Struct(">i")
    def put_tarray(self, cursor, values):
        return cursor.put_fields(self._format_tarray, values.size) + cursor.put_array(values)

    _format_ttree = struct.Struct(">qqqqqdiiiiIqqqqqq")
    def _write(self, context, cursor, name, compression, key, keycursor, util):
        self.util = util
        self.util.set_obj(self)
        copy_cursor = copy(cursor)
        write_cursor = copy(cursor)
        self.keycursor = keycursor
        cursor.skip(self._format_cntvers.size)
        vers = 20

        self.fields["_fClusterRangeEnd"] = numpy.array(self.fields["_fClusterRangeEnd"], dtype="int64", copy=False)
        self.fields["_fClusterSize"] = numpy.array(self.fields["_fClusterSize"], dtype="int64", copy=False)
        self.fields["_fIndexValues"] = numpy.array(self.fields["_fIndexValues"], dtype=">f8", copy=False)
        self.fields["_fIndex"] = numpy.array(self.fields["_fIndex"], dtype=">i8", copy=False)

        for branch in self.branches:
            self.fields["_fEntries"] += branch.fields["_fEntries"]
            self.fields["_fTotBytes"] += branch.fields["_fTotBytes"]
            self.fields["_fZipBytes"] += branch.fields["_fZipBytes"]
            self.fields["_fLeaves"].append(branch.fields["_fLeaves"])
            #TODO: HAVE TO WRITE BRANCH!
            branch.util = self.util
            branch.keycursor = self.keycursor
            self.fields["_fBranches"].append(branch)

        buff = (self.put_tnamed(cursor, name, self.fTitle, hexbytes=numpy.uint32(0x03000008)) +
                self.put_tattline(cursor) +
                self.put_tattfill(cursor) +
                self.put_tattmarker(cursor) +
                cursor.put_fields(self._format_ttree, self.fields["_fEntries"],
                                  self.fields["_fTotBytes"],
                                  self.fields["_fZipBytes"],
                                  self.fields["_fSavedBytes"],
                                  self.fields["_fFlushedBytes"],
                                  self.fields["_fWeight"],
                                  self.fields["_fTimerInterval"],
                                  self.fields["_fScanField"],
                                  self.fields["_fUpdate"],
                                  self.fields["_fDefaultEntryOffsetLen"],
                                  self.fields["_fNClusterRange"],
                                  self.fields["_fMaxEntries"],
                                  self.fields["_fMaxEntryLoop"],
                                  self.fields["_fMaxVirtualSize"],
                                  self.fields["_fAutoSave"],
                                  self.fields["_fAutoFlush"],
                                  self.fields["_fEstimate"]) +
                cursor.put_array(self.fields["_fClusterRangeEnd"]) +
                b"\x00")
        cursor.skip(len(b"\x00"))
        buff += (cursor.put_array(self.fields["_fClusterSize"]) +
                b"\x00")
        cursor.skip(len(b"\x00"))
        buff += (self.put_rootiofeatures(cursor) +
                self.put_tobjarray(cursor, self.fields["_fBranches"], "TBranch", fBits=50348032))
        if self.fields["_fBranches"] == []:
            buff += self.put_tobjarray(cursor, self.fields["_fLeaves"], "TLeaf")
        else:
            buff += self.put_tobjarray(cursor, self.fields["_fLeaves"][0][0], classname=self.fields["_fLeaves"][0][1])
        buff += (self.util.put_objany(cursor, (self.fields["_fAliases"], "TList"), self.keycursor) +
                 self.put_tarray(cursor, self.fields["_fIndexValues"]) +
                 self.put_tarray(cursor, self.fields["_fIndex"]) +
                 self.util.put_objany(cursor, (self.fields["_fTreeIndex"], "TVirtualIndex"), self.keycursor) +
                 self.util.put_objany(cursor, (self.fields["_fFriends"], "TList"), self.keycursor) +
                 self.util.put_objany(cursor, (self.fields["_fUserInfo"], "TList"), self.keycursor) +
                 self.util.put_objany(cursor, (self.fields["_fBranchRef"], "TBranchRef"), self.keycursor))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        givenbytes = copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff
        uproot.write.compress.write(context, write_cursor, givenbytes, compression, key, keycursor)

class TBranch(object):

    # Need to think about appropriate defaultBasketSize
    # Need to look at ROOT's default branch compression
    def __init__(self, type, name, title, defaultBasketSize=32000, compression=None):

        self.type = numpy.dtype(type).newbyteorder(">")
        self.name = self.fixstring(name)
        if title == "":
            self.title = self.fixstring(name)
            self.nametitle = self.title + b"/I"
        else:
            self.title = self.fixstring(title)
            self.nametitle = self.title
        self.defaultBasketSize = defaultBasketSize
        self.compression = compression
        self.util = None
        self.keycursor = None

        self.fields = {"_fCompress" : 100,
                       "_fBasketSize" : self.defaultBasketSize,
                       "_fEntryOffsetLen": 0,
                       "_fWriteBasket": 0, #Number of baskets
                       "_fOffset": 0,
                       "_fMaxBaskets": 10, #TODO: WHAT DOES THIS MEAN?!!! (IMPORTANT!!!)
                       "_fSplitLevel": 0,
                       "_fEntries": 0, #Number of values in the branch = fEntryNumber in our case
                       "_fFirstEntry": 0, #First value in the branch
                       "_fTotBytes": 0, #Number of bytes of the branch?
                       "_fZipBytes": 0, #Same as fTotBytes when no compression
                       "_fBasketBytes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       "_fBasketEntry": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], #TODO: WHAT DOES THIS MEAN?!!! (IMPORTANT!!!)
                       "_fBasketSeek": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], #Number of entries = fMaxBaskets. Empty baskets = 0.
                       "_fFileName": b"",
                       "_fBranches": [],
                       "_fLeaves": [],
                       "_fFillColor": 0,
                       "_fFillStyle": 1001,
                       "_fEntryNumber": 0}

        if self.type == "int8":
            self.fields["_fLeaves"] = [self, "TLeafB"]
        elif self.type == ">U":
            self.fields["_fLeaves"] = [self, "TLeafC"]
        elif self.type == ">f8":
            self.fields["_fLeaves"] = [self, "TLeafD"]
        elif self.type == ">f4":
            self.fields["_fLeaves"] = [self, "TLeafF"]
        elif self.type == ">i4":
            self.fields["_fLeaves"] = [self, "TLeafI"]
        elif self.type == ">i8":
            self.fields["_fLeaves"] = [self, "TleafL"]
        elif self.type == ">?":
            self.fields["_fLeaves"] = [self, "TLeafO"]
        elif self.type == ">i2":
            self.fields["_fLeaves"] = [self, "TLeafS"]
        else:
            raise NotImplementedError

        self.fields["_fBasketBytes"] = numpy.array(self.fields["_fBasketBytes"], dtype=">i4", copy=False)
        self.fields["_fBasketEntry"] = numpy.array(self.fields["_fBasketEntry"], dtype=">i8", copy=False)
        self.fields["_fBasketSeek"] = numpy.array(self.fields["_fBasketSeek"], dtype=">i8", copy=False)

    def append(self, item):
        self.extend(item)

    def extend(self, items):
        raise NotImplementedError

    def basket(self, items):
        raise NotImplementedError

    @staticmethod
    def fixstring(string):
        if isinstance(string, bytes):
            return string
        else:
            return string.encode("utf-8")

    _format_cntvers = struct.Struct(">IH")

    _format_tobject1 = struct.Struct(">HII")
    def put_tobject(self, cursor, hexbytes):
        return cursor.put_fields(self._format_tobject1, 1, 0, hexbytes)

    def put_tnamed(self, cursor, name, title, hexbytes=numpy.uint32(0x03000000)):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        buff = (self.put_tobject(cursor, hexbytes) +
                cursor.put_string(name) + cursor.put_string(title))
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

    _format_rootiofeatures = struct.Struct(">B")
    def put_rootiofeatures(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 0
        fIOBits = 0
        cursor.skip(4)
        buff = b"\x1a\xa1/\x10"
        buff += cursor.put_fields(self._format_rootiofeatures, fIOBits)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleaf1 = struct.Struct('>iii??')
    def put_tleaf(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        fLen = 1
        fLenType = 4
        fOffset = 0
        fIsRange = False
        fIsUnsigned = False
        fLeafCount = None
        buff = (self.put_tnamed(cursor, self.name, self.title) +
                cursor.put_fields(self._format_tleaf1, fLen, fLenType, fOffset, fIsRange, fIsUnsigned) +
                self.util.put_objany(cursor, (fLeafCount, "TLeaf"), self.keycursor))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafI1 = struct.Struct('>ii')
    def put_tleafI(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafI1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafB1 = struct.Struct('>bb')
    def put_tleafB(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafB1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafD1 = struct.Struct('>dd')
    def put_tleafD(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafD1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafF1 = struct.Struct('>ff')
    def put_tleafF(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafF1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafL1 = struct.Struct('>qq')
    def put_tleafL(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafL1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafO1 = struct.Struct('>??')
    def put_tleafO(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafO1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafS1 = struct.Struct('>hh')
    def put_tleafS(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafS1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tobjarray1 = struct.Struct(">ii")
    def put_tobjarray(self, cursor, values, classname, fBits=50331648):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        buff = self._skiptobj(cursor, fBits)
        vers = 3
        try:
            size = len(values)
        except TypeError:
            size = 1
            values = [values]
        low = 0
        buff += cursor.put_string(b"") + cursor.put_fields(self._format_tobjarray1, size, low)
        for value in values:
            buff += self.util.put_objany(cursor, (value, classname), self.keycursor)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_skiptobj1 = struct.Struct(">h")
    _format_skiptobj2 = struct.Struct(">II")
    def _skiptobj(self, cursor, fBits):
        version = 1
        buff = cursor.put_fields(self._format_skiptobj1, version)
        fUniqueID = 0
        buff += cursor.put_fields(self._format_skiptobj2, fUniqueID, fBits)
        return buff

    _format_tbranch1 = struct.Struct('>iiiiq')
    _format_tbranch2 = struct.Struct('>iIiqqqq')
    def write(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 13
        buff = (self.put_tnamed(cursor, self.name, self.nametitle, hexbytes=numpy.uint32(0x03400000)) +
                self.put_tattfill(cursor) +
                cursor.put_fields(self._format_tbranch1,
                                  self.fields["_fCompress"],
                                  self.fields["_fBasketSize"],
                                  self.fields["_fEntryOffsetLen"],
                                  self.fields["_fWriteBasket"],
                                  self.fields["_fEntryNumber"]) +
                self.put_rootiofeatures(cursor) +
                cursor.put_fields(self._format_tbranch2,
                                  self.fields["_fOffset"],
                                  self.fields["_fMaxBaskets"],
                                  self.fields["_fSplitLevel"],
                                  self.fields["_fEntries"],
                                  self.fields["_fFirstEntry"],
                                  self.fields["_fTotBytes"],
                                  self.fields["_fZipBytes"]) +
                self.put_tobjarray(cursor, self.fields["_fBranches"], classname="TBranch") +
                self.put_tobjarray(cursor, self.fields["_fLeaves"][0], classname=self.fields["_fLeaves"][1]) +
                #self.put_tobjarray(cursor, self.fields["fBaskets"]) +
                b"@\x00\x00\x15\x00\x03\x00\x01\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        cursor.skip(len(b"@\x00\x00\x15\x00\x03\x00\x01\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        buff += (b"\x01")
        cursor.skip(len(b"\x01"))
        buff += (cursor.put_array(self.fields["_fBasketBytes"]) +
                b"\x01")
        cursor.skip(len(b"\x01"))
        buff += (cursor.put_array(self.fields["_fBasketEntry"]) + b"\x01")
        cursor.skip(len(b"\x01"))
        buff += (cursor.put_array(self.fields["_fBasketSeek"]) +
                cursor.put_string(self.fields["_fFileName"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff
