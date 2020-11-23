#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

from __future__ import absolute_import

import struct
from copy import copy

import numpy

import uproot3.const
import uproot3.write.compress
import uproot3.write.sink.cursor
from uproot3.rootio import _bytesid

class TH(object):
    def __init__(self, histogram):
        self._fTitle = _bytesid(histogram._fTitle)
        self._fClassName = _bytesid(histogram._classname)

        self._fXaxis = self._emptyaxis("xaxis", 1.0)
        self._fXaxis.update(histogram._fXaxis.__dict__)
        self._fixaxis(self._fXaxis)

        self._fYaxis = self._emptyaxis("yaxis", 0.0)
        if hasattr(histogram, "_fYaxis"):
            self._fYaxis.update(histogram._fYaxis.__dict__)
        self._fixaxis(self._fYaxis)

        self._fZaxis = self._emptyaxis("zaxis", 1.0)
        if hasattr(histogram, "_fZaxis"):
            self._fZaxis.update(histogram._fZaxis.__dict__)
        self._fixaxis(self._fZaxis)

        self._values = histogram.allvalues

        self._fields = self._emptyfields()
        for n in list(self._fields):
            if hasattr(histogram, n):
                self._fields[n] = getattr(histogram, n)

        if self._fClassName == b"TH1C":
            self._valuesarray = numpy.array(self._values, dtype=">i1")
        elif self._fClassName == b"TH1S":
            self._valuesarray = numpy.array(self._values, dtype=">i2")
        elif self._fClassName == b"TH1I":
            self._valuesarray = numpy.array(self._values, dtype=">i4")
        elif self._fClassName == b"TH1F":
            self._valuesarray = numpy.array(self._values, dtype=">f4")
        elif self._fClassName == b"TH1D":
            self._valuesarray = numpy.array(self._values, dtype=">f8")
        elif self._fClassName == b"TProfile":
            self._valuesarray = numpy.array(self._values, dtype=">f8")
        elif self._fClassName == b"TH2C":
            self._valuesarray = numpy.array(self._values, dtype=">i1").transpose()
        elif self._fClassName == b"TH2S":
            self._valuesarray = numpy.array(self._values, dtype=">i2").transpose()
        elif self._fClassName == b"TH2I":
            self._valuesarray = numpy.array(self._values, dtype=">i4").transpose()
        elif self._fClassName == b"TH2F":
            self._valuesarray = numpy.array(self._values, dtype=">f4").transpose()
        elif self._fClassName == b"TH2D":
            self._valuesarray = numpy.array(self._values, dtype=">f8").transpose()
        elif self._fClassName == b"TProfile2D":
            self._valuesarray = numpy.array(self._values, dtype=">f8").transpose()
        elif self._fClassName == b"TH3C":
            self._valuesarray = numpy.array(self._values, dtype=">i1").transpose()
        elif self._fClassName == b"TH3S":
            self._valuesarray = numpy.array(self._values, dtype=">i2").transpose()
        elif self._fClassName == b"TH3I":
            self._valuesarray = numpy.array(self._values, dtype=">i4").transpose()
        elif self._fClassName == b"TH3F":
            self._valuesarray = numpy.array(self._values, dtype=">f4").transpose()
        elif self._fClassName == b"TH3D":
            self._valuesarray = numpy.array(self._values, dtype=">f8").transpose()
        elif self._fClassName == b"TProfile3D":
            self._valuesarray = numpy.array(self._values, dtype=">f8").transpose()
        else:
            raise ValueError("unrecognized histogram class name {0}".format(self._fClassName))

        self._fields["_fNcells"] = self._valuesarray.size
        self._fields["_fContour"] = numpy.array(self._fields["_fContour"], dtype=">f8", copy=False)
        self._fields["_fSumw2"] = numpy.array(self._fields["_fSumw2"], dtype=">f8", copy=False)
        self._fields["_fBinEntries"] = numpy.array(self._fields["_fBinEntries"], dtype=">f8", copy=False)
        self._fields["_fBinSumw2"] = numpy.array(self._fields["_fBinSumw2"], dtype=">f8", copy=False)

    @staticmethod
    def _fixaxis(axis):
        axis["_fName"] = _bytesid(axis["_fName"])
        axis["_fTitle"] = _bytesid(axis["_fTitle"])
        axis["_fXbins"] = numpy.array(axis["_fXbins"], dtype=">f8", copy=False)
        if axis["_fLabels"] is None:
            axis["_fLabels"] = []
        if axis["_fModLabs"] is None:
            axis["_fModLabs"] = []

    @staticmethod
    def _emptyfields():
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
    def _emptyaxis(name, titleoffset):
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
    def _put_tobject(self, cursor):
        return cursor.put_fields(self._format_tobject1, 1, 0, numpy.uint32(0x03000000))

    def _put_tnamed(self, cursor, name, title):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        buff = (self._put_tobject(cursor) +
                cursor.put_string(name) + cursor.put_string(title))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tarray = struct.Struct(">i")
    def _put_tarray(self, cursor, values):
        return cursor.put_fields(self._format_tarray, values.size) + cursor.put_array(values)

    _format_tobjstring = struct.Struct(">IHHII")
    def _put_tobjstring(self, cursor, value, bit=0):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_tobjstring.size)
        vers = 1
        buff = cursor.put_string(value)
        length = len(buff) + self._format_tobjstring.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_tobjstring, cnt, vers, 1, bit, numpy.uint32(0x03000000)) + buff

    _format_tlist1 = struct.Struct(">i")
    _format_tlist2 = struct.Struct(">B")
    def _put_tlist(self, cursor, values):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 5
        buff = b""
        givenbytes = (self._put_tobject(cursor) +
                      cursor.put_string(b"") +
                      cursor.put_fields(self._format_tlist1, len(values)))
        for value in values:
            buff += self.util.put_objany(cursor, (value, "TObjString"), self.keycursor)
            buff += cursor.put_fields(self._format_tlist2, 0)
            buff += b"" # cursor.bytes(source, n)
        givenbytes += buff
        length = len(givenbytes) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + givenbytes

    _format_tattline = struct.Struct(">hhh")
    def _put_tattline(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattline,
                                  self._fields["_fLineColor"],
                                  self._fields["_fLineStyle"],
                                  self._fields["_fLineWidth"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattfill = struct.Struct(">hh")
    def _put_tattfill(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattfill,
                                  self._fields["_fFillColor"],
                                  self._fields["_fFillStyle"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattmarker = struct.Struct(">hhf")
    def _put_tattmarker(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattmarker,
                                  self._fields["_fMarkerColor"],
                                  self._fields["_fMarkerStyle"],
                                  self._fields["_fMarkerSize"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattaxis = struct.Struct(">ihhhfffffhh")
    def _put_tattaxis(self, cursor, axis):
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
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_taxis_1 = struct.Struct(">idd")
    _format_taxis_2 = struct.Struct(">iiH?")
    def _put_taxis(self, cursor, axis):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 10
        buff = (self._put_tnamed(cursor, axis["_fName"], axis["_fTitle"]) +
                self._put_tattaxis(cursor, axis) +
                cursor.put_fields(self._format_taxis_1,
                                  axis["_fNbins"],
                                  axis["_fXmin"],
                                  axis["_fXmax"]) +
                self._put_tarray(cursor, axis["_fXbins"]) +
                cursor.put_fields(self._format_taxis_2,
                                  axis["_fFirst"],
                                  axis["_fLast"],
                                  axis["_fBits2"],
                                  axis["_fTimeDisplay"]) +
                cursor.put_string(axis["_fTimeFormat"]) +
                self.util.put_objany(cursor, (axis["_fLabels"], "THashList"), self.keycursor) +
                self.util.put_objany(cursor, (axis["_fModLabs"], "TList"), self.keycursor))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_th1_1 = struct.Struct(">i")
    _format_th1_2 = struct.Struct(">hhdddddddd")
    _format_th1_3 = struct.Struct(">iBii")
    def _put_th1(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 8
        if len(self._fields["_fBuffer"]) != 0:
            raise NotImplementedError
        buff = (self._put_tnamed(cursor, name, self._fTitle) +
                self._put_tattline(cursor) +
                self._put_tattfill(cursor) +
                self._put_tattmarker(cursor) +
                cursor.put_fields(self._format_th1_1, self._fields["_fNcells"]) +
                self._put_taxis(cursor, self._fXaxis) +
                self._put_taxis(cursor, self._fYaxis) +
                self._put_taxis(cursor, self._fZaxis) +
                cursor.put_fields(self._format_th1_2,
                                  self._fields["_fBarOffset"],
                                  self._fields["_fBarWidth"],
                                  self._fields["_fEntries"],
                                  self._fields["_fTsumw"],
                                  self._fields["_fTsumw2"],
                                  self._fields["_fTsumwx"],
                                  self._fields["_fTsumwx2"],
                                  self._fields["_fMaximum"],
                                  self._fields["_fMinimum"],
                                  self._fields["_fNormFactor"]) +
                self._put_tarray(cursor, self._fields["_fContour"]) +
                self._put_tarray(cursor, self._fields["_fSumw2"]) +
                cursor.put_string(self._fields["_fOption"]) +
                self._put_tlist(cursor, self._fields["_fFunctions"]) +
                cursor.put_fields(self._format_th1_3,
                                  self._fields["_fBufferSize"],
                                  0,  # FIXME: empty fBuffer
                                  self._fields["_fBinStatErrOpt"],
                                  self._fields["_fStatOverflows"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_th2_1 = struct.Struct(">dddd")
    def _put_th2(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 5
        buff = (self._put_th1(cursor, name) +
                cursor.put_fields(self._format_th2_1,
                                  self._fields["_fScalefactor"],
                                  self._fields["_fTsumwy"],
                                  self._fields["_fTsumwy2"],
                                  self._fields["_fTsumwxy"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_th3_1 = struct.Struct(">ddddddd")
    def _put_th3(self, cursor, name):
        vers = 6
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        buff = (self._put_th1(cursor, name) +
                self._put_tatt3d(cursor) + cursor.put_fields(self._format_th3_1,
                                                             self._fields["_fTsumwy"],
                                                             self._fields["_fTsumwy2"],
                                                             self._fields["_fTsumwxy"],
                                                             self._fields["_fTsumwz"],
                                                             self._fields["_fTsumwz2"],
                                                             self._fields["_fTsumwxz"],
                                                             self._fields["_fTsumwyz"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    def _put_tatt3d(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        cnt = numpy.int64(self._format_cntvers.size - 4) | uproot3.const.kByteCountMask
        vers = 1
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers)

    def _put_th1d(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 3
        buff = self._put_th1(cursor, name) + self._put_tarray(cursor, self._valuesarray)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    def _put_th2d(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 4
        buff = self._put_th2(cursor, name) + self._put_tarray(cursor, self._valuesarray)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    def _put_th3d(self, cursor, name):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 4
        buff = self._put_th3(cursor, name) + self._put_tarray(cursor, self._valuesarray)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tprofile = struct.Struct(">idddd")
    def _write(self, context, cursor, name, compression, key, keycursor, util):
        self.util = util
        self.util.set_obj(self)
        copy_cursor = copy(cursor)
        write_cursor = copy(cursor)
        self.keycursor = keycursor
        cursor.skip(self._format_cntvers.size)
        if "TH1" in self._fClassName.decode("utf-8"):
            vers = 3
            buff = self._put_th1(cursor, name) + self._put_tarray(cursor, self._valuesarray)
        elif "TH2" in self._fClassName.decode("utf-8"):
            vers = 4
            buff = self._put_th2(cursor, name) + self._put_tarray(cursor, self._valuesarray)
        elif "TH3" in self._fClassName.decode("utf-8"):
            vers = 4
            buff = self._put_th3(cursor, name) + self._put_tarray(cursor, self._valuesarray)
        elif "TProfile" == self._fClassName.decode("utf-8"):
            vers = 7
            buff = (self._put_th1d(cursor, name) + self._put_tarray(cursor, self._fields["_fBinEntries"]) +
                    cursor.put_fields(self._format_tprofile, self._fields["_fErrorMode"], self._fields["_fYmin"],
                                      self._fields["_fYmax"], self._fields["_fTsumwy"], self._fields["_fTsumwy2"]) +
                    self._put_tarray(cursor, self._fields["_fBinSumw2"]))
        elif "TProfile2D" == self._fClassName.decode("utf-8"):
            vers = 8
            buff = (self._put_th2d(cursor, name)
                    + self._put_tarray(cursor, self._fields["_fBinEntries"]) +
                    cursor.put_fields(self._format_tprofile, self._fields["_fErrorMode"], self._fields["_fZmin"],
                                      self._fields["_fZmax"], self._fields["_fTsumwz"], self._fields["_fTsumwz2"]) +
                    self._put_tarray(cursor, self._fields["_fBinSumw2"]))
        elif "TProfile3D" == self._fClassName.decode("utf-8"):
            vers = 8
            buff = (self._put_th3d(cursor, name)
                    + self._put_tarray(cursor, self._fields["_fBinEntries"]) +
                    cursor.put_fields(self._format_tprofile, self._fields["_fErrorMode"], self._fields["_fTmin"],
                                      self._fields["_fTmax"], self._fields["_fTsumwt"], self._fields["_fTsumwt2"]) +
                    self._put_tarray(cursor, self._fields["_fBinSumw2"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot3.const.kByteCountMask
        givenbytes = copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff
        uproot3.write.compress.write(context, write_cursor, givenbytes, compression, key, keycursor)
