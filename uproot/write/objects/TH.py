#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from __future__ import absolute_import

import struct
from copy import copy

import numpy

import uproot.const
import uproot.write.compress
import uproot.write.sink.cursor

class TH(object):
    def __init__(self, histogram):
        self.fTitle = self.fixstring(histogram._fTitle)
        self.fClassName = self.fixstring(histogram._classname)

        self.fXaxis = self.emptyaxis("xaxis", 1.0)
        self.fXaxis.update(histogram._fXaxis.__dict__)
        self.fixaxis(self.fXaxis)

        self.fYaxis = self.emptyaxis("yaxis", 0.0)
        if hasattr(histogram, "_fYaxis"):
            self.fYaxis.update(histogram._fYaxis.__dict__)
        self.fixaxis(self.fYaxis)

        self.fZaxis = self.emptyaxis("zaxis", 1.0)
        if hasattr(histogram, "_fZaxis"):
            self.fZaxis.update(histogram._fZaxis.__dict__)
        self.fixaxis(self.fZaxis)

        self.values = histogram.allvalues

        self.fields = self.emptyfields()
        for n in list(self.fields):
            if hasattr(histogram, n):
                self.fields[n] = getattr(histogram, n)

        if self.fClassName == b"TH1C":
            self.valuesarray = numpy.array(self.values, dtype=">i1")
        elif self.fClassName == b"TH1S":
            self.valuesarray = numpy.array(self.values, dtype=">i2")
        elif self.fClassName == b"TH1I":
            self.valuesarray = numpy.array(self.values, dtype=">i4")
        elif self.fClassName == b"TH1F":
            self.valuesarray = numpy.array(self.values, dtype=">f4")
        elif self.fClassName == b"TH1D":
            self.valuesarray = numpy.array(self.values, dtype=">f8")
        elif self.fClassName == b"TProfile":
            self.valuesarray = numpy.array(self.values, dtype=">f8")
        elif self.fClassName == b"TH2C":
            self.valuesarray = numpy.array(self.values, dtype=">i1").transpose()
        elif self.fClassName == b"TH2S":
            self.valuesarray = numpy.array(self.values, dtype=">i2").transpose()
        elif self.fClassName == b"TH2I":
            self.valuesarray = numpy.array(self.values, dtype=">i4").transpose()
        elif self.fClassName == b"TH2F":
            self.valuesarray = numpy.array(self.values, dtype=">f4").transpose()
        elif self.fClassName == b"TH2D":
            self.valuesarray = numpy.array(self.values, dtype=">f8").transpose()
        elif self.fClassName == b"TProfile2D":
            self.valuesarray = numpy.array(self.values, dtype=">f8").transpose()
        elif self.fClassName == b"TH3C":
            self.valuesarray = numpy.array(self.values, dtype=">i1").transpose()
        elif self.fClassName == b"TH3S":
            self.valuesarray = numpy.array(self.values, dtype=">i2").transpose()
        elif self.fClassName == b"TH3I":
            self.valuesarray = numpy.array(self.values, dtype=">i4").transpose()
        elif self.fClassName == b"TH3F":
            self.valuesarray = numpy.array(self.values, dtype=">f4").transpose()
        elif self.fClassName == b"TH3D":
            self.valuesarray = numpy.array(self.values, dtype=">f8").transpose()
        elif self.fClassName == b"TProfile3D":
            self.valuesarray = numpy.array(self.values, dtype=">f8").transpose()
        else:
            raise ValueError("unrecognized histogram class name {0}".format(self.fClassName))

        self.fields["_fNcells"] = self.valuesarray.size
        self.fields["_fContour"] = numpy.array(self.fields["_fContour"], dtype=">f8", copy=False)
        self.fields["_fSumw2"] = numpy.array(self.fields["_fSumw2"], dtype=">f8", copy=False)
        self.fields["_fBinEntries"] = numpy.array(self.fields["_fBinEntries"], dtype=">f8", copy=False)
        self.fields["_fBinSumw2"] = numpy.array(self.fields["_fBinSumw2"], dtype=">f8", copy=False)

    @staticmethod
    def fixstring(string):
        if isinstance(string, bytes):
            return string
        else:
            return string.encode("utf-8")

    @staticmethod
    def fixaxis(axis):
        axis["_fName"] = TH.fixstring(axis["_fName"])
        axis["_fTitle"] = TH.fixstring(axis["_fTitle"])
        axis["_fXbins"] = numpy.array(axis["_fXbins"], dtype=">f8", copy=False)
        if axis["_fLabels"] is None:
            axis["_fLabels"] = []
        if axis["_fModLabs"] is None:
            axis["_fModLabs"] = []

    @staticmethod
    def emptyfields():
        return {"_fLineColor": 602,
                "_fLineStyle": 1,
                "_fLineWidth": 1,
                "_fFillColor": 0,
                "_fFillStyle": 1001,
                "_fMarkerColor": 1,
                "_fMarkerStyle": 1,
                "_fMarkerSize": 1.0,
                "_fNcells": 12,
                "_fBarOffset": 0,
                "_fBarWidth": 1000,
                "_fEntries": 0.0,
                "_fTsumw": 0.0,
                "_fTsumw2": 0.0,
                "_fTsumwx": 0.0,
                "_fTsumwx2": 0.0,
                "_fMaximum": -1111.0,
                "_fMinimum": -1111.0,
                "_fNormFactor": 0.0,
                "_fContour": [],
                "_fSumw2": [],
                "_fOption": b"",
                "_fFunctions": [],
                "_fBufferSize": 0,
                "_fBuffer": [],
                "_fBinStatErrOpt": 0,
                "_fStatOverflows": 2,
                "_fTsumwy": 0.0,
                "_fTsumwy2": 0.0,
                "_fTsumwxy": 0.0,
                "_fTsumwz": 0.0,
                "_fTsumwz2": 0.0,
                "_fTsumwxz": 0.0,
                "_fTsumwyz": 0.0,
                "_fScalefactor": 0.0,
                "_fBinEntries": [],
                "_fYmin": 0.0,
                "_fYmax": 0.0,
                "_fBinSumw2": [],
                "_fErrorMode": 0,
                "_fZmin": 0.0,
                "_fZmax": 0.0,
                "_fTmin": 0.0,
                "_fTmax": 0.0,
                "_fTsumwt": 0.0,
                "_fTsumwt2": 0.0}

    @staticmethod
    def emptyaxis(name, titleoffset):
        return {"_fName": name,
                "_fTitle": b"",
                "_fNdivisions": 510,
                "_fAxisColor": 1,
                "_fLabelColor": 1,
                "_fLabelFont": 42,
                "_fLabelOffset": 0.004999999888241291,
                "_fLabelSize": 0.03500000014901161,
                "_fTickLength": 0.029999999329447746,
                "_fTitleOffset": titleoffset,
                "_fTitleSize": 0.03500000014901161,
                "_fTitleColor": 1,
                "_fTitleFont": 42,
                "_fNbins": 1,
                "_fXmin": 0.0,
                "_fXmax": 1.0,
                "_fXbins": [],
                "_fFirst": 0,
                "_fLast": 0,
                "_fBits2": 0,
                "_fTimeDisplay": False,
                "_fTimeFormat": b"",
                "_fLabels": None,
                "_fModLabs": None}

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

    _format_tarray = struct.Struct(">i")
    def put_tarray(self, cursor, values):
        return cursor.put_fields(self._format_tarray, values.size) + cursor.put_array(values)

    _format_tobjstring = struct.Struct(">IHHII")
    def put_tobjstring(self, cursor, value, bit=0):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_tobjstring.size)
        vers = 1
        buff = cursor.put_string(value)
        length = len(buff) + self._format_tobjstring.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_tobjstring, cnt, vers, 1, bit, numpy.uint32(0x03000000)) + buff

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

    _format_tattaxis = struct.Struct(">ihhhfffffhh")
    def put_tattaxis(self, cursor, axis):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 4
        buff = (cursor.put_fields(self._format_tattaxis,
                                  axis["_fNdivisions"],
                                  axis["_fAxisColor"],
                                  axis["_fLabelColor"],
                                  axis["_fLabelFont"],
                                  axis["_fLabelOffset"],
                                  axis["_fLabelSize"],
                                  axis["_fTickLength"],
                                  axis["_fTitleOffset"],
                                  axis["_fTitleSize"],
                                  axis["_fTitleColor"],
                                  axis["_fTitleFont"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_taxis_1 = struct.Struct(">idd")
    _format_taxis_2 = struct.Struct(">iiH?")
    def put_taxis(self, cursor, axis):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 10
        buff = (self.put_tnamed(cursor, axis["_fName"], axis["_fTitle"]) +
                self.put_tattaxis(cursor, axis) +
                cursor.put_fields(self._format_taxis_1,
                                  axis["_fNbins"],
                                  axis["_fXmin"],
                                  axis["_fXmax"]) +
                self.put_tarray(cursor, axis["_fXbins"]) +
                cursor.put_fields(self._format_taxis_2,
                                  axis["_fFirst"],
                                  axis["_fLast"],
                                  axis["_fBits2"],
                                  axis["_fTimeDisplay"]) +
                cursor.put_string(axis["_fTimeFormat"]) +
                self.util.put_objany(cursor, (axis["_fLabels"], "THashList"), self.keycursor) +
                self.util.put_objany(cursor, (axis["_fModLabs"], "TList"), self.keycursor))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_th1_1 = struct.Struct(">i")
    _format_th1_2 = struct.Struct(">hhdddddddd")
    _format_th1_3 = struct.Struct(">iBii")
    def put_th1(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 8
        if len(self.fields["_fBuffer"]) != 0:
            raise NotImplementedError
        buff = (self.put_tnamed(cursor, name, self.fTitle) +
                self.put_tattline(cursor) +
                self.put_tattfill(cursor) +
                self.put_tattmarker(cursor) +
                cursor.put_fields(self._format_th1_1, self.fields["_fNcells"]) +
                self.put_taxis(cursor, self.fXaxis) +
                self.put_taxis(cursor, self.fYaxis) +
                self.put_taxis(cursor, self.fZaxis) +
                cursor.put_fields(self._format_th1_2,
                                  self.fields["_fBarOffset"],
                                  self.fields["_fBarWidth"],
                                  self.fields["_fEntries"],
                                  self.fields["_fTsumw"],
                                  self.fields["_fTsumw2"],
                                  self.fields["_fTsumwx"],
                                  self.fields["_fTsumwx2"],
                                  self.fields["_fMaximum"],
                                  self.fields["_fMinimum"],
                                  self.fields["_fNormFactor"]) +
                self.put_tarray(cursor, self.fields["_fContour"]) +
                self.put_tarray(cursor, self.fields["_fSumw2"]) +
                cursor.put_string(self.fields["_fOption"]) +
                self.put_tlist(cursor, self.fields["_fFunctions"]) +
                cursor.put_fields(self._format_th1_3,
                                  self.fields["_fBufferSize"],
                                  0,  # FIXME: empty fBuffer
                                  self.fields["_fBinStatErrOpt"],
                                  self.fields["_fStatOverflows"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_th2_1 = struct.Struct(">dddd")
    def put_th2(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 5
        buff = (self.put_th1(cursor, name) +
                cursor.put_fields(self._format_th2_1,
                                  self.fields["_fScalefactor"],
                                  self.fields["_fTsumwy"],
                                  self.fields["_fTsumwy2"],
                                  self.fields["_fTsumwxy"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_th3_1 = struct.Struct(">ddddddd")
    def put_th3(self, cursor, name):
        vers = 6
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        buff = (self.put_th1(cursor, name) +
                self.put_tatt3d(cursor) + cursor.put_fields(self._format_th3_1,
                                                            self.fields["_fTsumwy"],
                                                            self.fields["_fTsumwy2"],
                                                            self.fields["_fTsumwxy"],
                                                            self.fields["_fTsumwz"],
                                                            self.fields["_fTsumwz2"],
                                                            self.fields["_fTsumwxz"],
                                                            self.fields["_fTsumwyz"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    def put_tatt3d(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        cnt = numpy.int64(self._format_cntvers.size - 4) | uproot.const.kByteCountMask
        vers = 1
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers)

    def put_th1d(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 3
        buff = self.put_th1(cursor, name) + self.put_tarray(cursor, self.valuesarray)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    def put_th2d(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 4
        buff = self.put_th2(cursor, name) + self.put_tarray(cursor, self.valuesarray)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    def put_th3d(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 4
        buff = self.put_th3(cursor, name) + self.put_tarray(cursor, self.valuesarray)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tprofile = struct.Struct(">idddd")
    def write(self, context, cursor, name, compression, key, keycursor, util):
        self.util = util
        self.util.set_obj(self)
        copy_cursor = copy(cursor)
        write_cursor = copy(cursor)
        self.keycursor = keycursor
        cursor.skip(self._format_cntvers.size)
        if "TH1" in self.fClassName.decode("utf-8"):
            vers = 3
            buff = self.put_th1(cursor, name) + self.put_tarray(cursor, self.valuesarray)
        elif "TH2" in self.fClassName.decode("utf-8"):
            vers = 4
            buff = self.put_th2(cursor, name) + self.put_tarray(cursor, self.valuesarray)
        elif "TH3" in self.fClassName.decode("utf-8"):
            vers = 4
            buff = self.put_th3(cursor, name) + self.put_tarray(cursor, self.valuesarray)
        elif "TProfile" == self.fClassName.decode("utf-8"):
            vers = 7
            buff = (self.put_th1d(cursor, name) + self.put_tarray(cursor, self.fields["_fBinEntries"]) +
                    cursor.put_fields(self._format_tprofile, self.fields["_fErrorMode"], self.fields["_fYmin"],
                                              self.fields["_fYmax"], self.fields["_fTsumwy"], self.fields["_fTsumwy2"]) +
                    self.put_tarray(cursor, self.fields["_fBinSumw2"]))
        elif "TProfile2D" == self.fClassName.decode("utf-8"):
            vers = 8
            buff = (self.put_th2d(cursor, name)
                    + self.put_tarray(cursor, self.fields["_fBinEntries"]) +
                    cursor.put_fields(self._format_tprofile, self.fields["_fErrorMode"], self.fields["_fZmin"],
                                              self.fields["_fZmax"], self.fields["_fTsumwz"], self.fields["_fTsumwz2"]) +
                    self.put_tarray(cursor, self.fields["_fBinSumw2"]))
        elif "TProfile3D" == self.fClassName.decode("utf-8"):
            vers = 8
            buff = (self.put_th3d(cursor, name)
                    + self.put_tarray(cursor, self.fields["_fBinEntries"]) +
                    cursor.put_fields(self._format_tprofile, self.fields["_fErrorMode"], self.fields["_fTmin"],
                                              self.fields["_fTmax"], self.fields["_fTsumwt"], self.fields["_fTsumwt2"]) +
                    self.put_tarray(cursor, self.fields["_fBinSumw2"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        givenbytes = copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff
        uproot.write.compress.write(context, write_cursor, givenbytes, compression, key, keycursor)
