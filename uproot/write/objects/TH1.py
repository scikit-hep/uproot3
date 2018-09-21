#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import struct

import numpy

import uproot.const
import uproot.write.sink.cursor

class TH1(object):
    def __init__(self, histogram):
        import uproot_methods.classes.TH1

        self.fields = self.emptyfields()

        if isinstance(histogram, tuple) and len(histogram) >= 2:
            content, edges = histogram[:2]

            self.fXaxis = self.emptyaxis("xaxis", 1.0)
            self.fYaxis = self.emptyaxis("yaxis", 0.0)
            self.fZaxis = self.emptyaxis("zaxis", 1.0)
            self.fXaxis["_fNbins"] = len(edges) - 1
            self.fXaxis["_fXmin"] = edges[0]
            self.fXaxis["_fXmax"] = edges[-1]
            if not numpy.array_equal(edges, numpy.linspace(edges[0], edges[-1], len(edges), dtype=edges.dtype)):
                self.fXaxis["_fXbins"] = edges.astype(">f8")
            self.fixaxis(self.fXaxis)
            self.fixaxis(self.fYaxis)
            self.fixaxis(self.fZaxis)

            centers = (edges[:-1] + edges[1:]) / 2.0
            self.fields["_fEntries"] = self.fields["_fTsumw"] = self.fields["_fTsumw2"] = content.sum()
            self.fields["_fTsumwx"] = (content * centers).sum()
            self.fields["_fTsumwx2"] = (content * centers**2).sum()

            if len(histogram) >= 3:
                self.fTitle = self.fixstring(histogram[2])
            else:
                self.fTitle = b""

            if issubclass(content.dtype.type, (numpy.bool_, numpy.bool)):
                self.fClassName = b"TH1C"
                content = content.astype(">i1")
            elif issubclass(content.dtype.type, numpy.int8):
                self.fClassName = b"TH1C"
                content = content.astype(">i1")
            elif issubclass(content.dtype.type, numpy.uint8) and content.max() <= numpy.iinfo(numpy.int8).max:
                self.fClassName = b"TH1C"
                content = content.astype(">i1")
            elif issubclass(content.dtype.type, numpy.uint8):
                self.fClassName = b"TH1S"
                content = content.astype(">i2")
            elif issubclass(content.dtype.type, numpy.int16):
                self.fClassName = b"TH1S"
                content = content.astype(">i2")
            elif issubclass(content.dtype.type, numpy.uint16) and content.max() <= numpy.iinfo(numpy.int16).max:
                self.fClassName = b"TH1S"
                content = content.astype(">i2")
            elif issubclass(content.dtype.type, numpy.uint16):
                self.fClassName = b"TH1I"
                content = content.astype(">i4")
            elif issubclass(content.dtype.type, numpy.int32):
                self.fClassName = b"TH1I"
                content = content.astype(">i4")
            elif issubclass(content.dtype.type, numpy.uint32) and content.max() <= numpy.iinfo(numpy.int32).max:
                self.fClassName = b"TH1I"
                content = content.astype(">i4")
            elif issubclass(content.dtype.type, numpy.integer) and numpy.iinfo(numpy.int32).min <= content.min() and content.max() <= numpy.iinfo(numpy.int32).max:
                self.fClassName = b"TH1I"
                content = content.astype(">i4")
            elif issubclass(content.dtype.type, numpy.float32):
                self.fClassName = b"TH1F"
                content = content.astype(">f4")
            else:
                self.fClassName = b"TH1D"
                content = content.astype(">f8")

            self.valuesarray = numpy.empty(len(content) + 2, dtype=content.dtype)
            self.valuesarray[1:-1] = content
            self.valuesarray[0] = 0
            self.valuesarray[-1] = 0

        elif isinstance(histogram, uproot_methods.classes.TH1.Methods):
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
                self.fYaxis.update(histogram._fZaxis.__dict__)
            self.fixaxis(self.fZaxis)

            self.values = histogram.allvalues

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
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH2C":
                self.valuesarray = numpy.array(self.values, dtype=">i1")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH2S":
                self.valuesarray = numpy.array(self.values, dtype=">i2")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH2I":
                self.valuesarray = numpy.array(self.values, dtype=">i4")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH2F":
                self.valuesarray = numpy.array(self.values, dtype=">f4")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH2D":
                self.valuesarray = numpy.array(self.values, dtype=">f8")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TProfile2D":
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH3C":
                self.valuesarray = numpy.array(self.values, dtype=">i1")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH3S":
                self.valuesarray = numpy.array(self.values, dtype=">i2")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH3I":
                self.valuesarray = numpy.array(self.values, dtype=">i4")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH3F":
                self.valuesarray = numpy.array(self.values, dtype=">f4")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TH3D":
                self.valuesarray = numpy.array(self.values, dtype=">f8")
                raise NotImplementedError(self.fClassName)
            elif self.fClassName == b"TProfile3D":
                raise NotImplementedError(self.fClassName)
            else:
                raise ValueError("unrecognized histogram class name {0}".format(self.fClassName))
            
        else:
            raise TypeError("type {0} from module {1} is not recognizable as a TH1".format(histogram.__class__.__name__, histogram.__class__.__module__))

        self.fields["_fNcells"] = len(self.valuesarray)
        self.fields["_fContour"] = numpy.array(self.fields["_fContour"], dtype=">f8", copy=False)
        self.fields["_fSumw2"] = numpy.array(self.fields["_fSumw2"], dtype=">f8", copy=False)

    @staticmethod
    def fixstring(string):
        if isinstance(string, bytes):
            return string
        else:
            return string.encode("utf-8")

    @staticmethod
    def fixaxis(axis):
        axis["_fName"] = TH1.fixstring(axis["_fName"])
        axis["_fTitle"] = TH1.fixstring(axis["_fTitle"])
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
                "_fStatOverflows": 2}

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
    def write_tobject(self, cursor, sink):
        cursor.write_fields(sink, self._format_tobject1, 1, 0, uproot.const.kNotDeleted)
    def length_tobject(self):
        return self._format_tobject1.size

    def write_tnamed(self, cursor, sink, name, title):
        cnt = numpy.int64(self.length_tnamed(name, title) - 4) | uproot.const.kByteCountMask
        vers = 1
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_tobject(cursor, sink)
        cursor.write_string(sink, name)
        cursor.write_string(sink, title)
    def length_tnamed(self, name, title):
        return self.length_tobject() + uproot.write.sink.cursor.Cursor.length_strings([name, title]) + 6

    _format_tarray = struct.Struct(">i")
    def write_tarray(self, cursor, sink, values):
        cursor.write_fields(sink, self._format_tarray, len(values))
        cursor.write_array(sink, values)
    def length_tarray(self, values):
        return self._format_tarray.size + values.nbytes

    _format_tlist = struct.Struct(">i")
    def write_tlist(self, cursor, sink, values):
        cnt = numpy.int64(self.length_tlist(values) - 4) | uproot.const.kByteCountMask
        vers = 5
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_tobject(cursor, sink)
        cursor.write_string(sink, b"")
        cursor.write_fields(sink, self._format_tlist, len(values))
        for value in values:
            raise NotImplementedError
    def length_tlist(self, values):
        return self.length_tobject() + uproot.write.sink.cursor.Cursor.length_string(b"") + self._format_tlist.size + sum(0 for x in values) + 6

    _format_tattline = struct.Struct(">hhh")
    def write_tattline(self, cursor, sink):
        cnt = numpy.int64(self.length_tattline() - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        cursor.write_fields(sink, self._format_tattline,
                            self.fields["_fLineColor"],
                            self.fields["_fLineStyle"],
                            self.fields["_fLineWidth"])
    def length_tattline(self):
        return self._format_tattline.size + 6

    _format_tattfill = struct.Struct(">hh")
    def write_tattfill(self, cursor, sink):
        cnt = numpy.int64(self.length_tattfill() - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        cursor.write_fields(sink, self._format_tattfill,
                            self.fields["_fFillColor"],
                            self.fields["_fFillStyle"])
    def length_tattfill(self):
        return self._format_tattfill.size + 6

    _format_tattmarker = struct.Struct(">hhf")
    def write_tattmarker(self, cursor, sink):
        cnt = numpy.int64(self.length_tattmarker() - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        cursor.write_fields(sink, self._format_tattmarker,
                            self.fields["_fMarkerColor"],
                            self.fields["_fMarkerStyle"],
                            self.fields["_fMarkerSize"])
    def length_tattmarker(self):
        return self._format_tattmarker.size + 6

    _format_tattaxis = struct.Struct(">ihhhfffffhh")
    def write_tattaxis(self, cursor, sink, axis):
        cnt = numpy.int64(self.length_tattaxis() - 4) | uproot.const.kByteCountMask
        vers = 4
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        cursor.write_fields(sink, self._format_tattaxis,
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
                            axis["_fTitleFont"])
    def length_tattaxis(self):
        return self._format_tattaxis.size + 6
                            
    _format_taxis_1 = struct.Struct(">idd")
    _format_taxis_2 = struct.Struct(">iiH?")
    def write_taxis(self, cursor, sink, axis):
        cnt = numpy.int64(self.length_taxis(axis) - 4) | uproot.const.kByteCountMask
        vers = 10
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_tnamed(cursor, sink, axis["_fName"], axis["_fTitle"])
        self.write_tattaxis(cursor, sink, axis)
        cursor.write_fields(sink, self._format_taxis_1,
                            axis["_fNbins"],
                            axis["_fXmin"],
                            axis["_fXmax"])
        self.write_tarray(cursor, sink, axis["_fXbins"])
        if axis["_fFirst"] != 0 or axis["_fLast"] != 0 or axis["_fBits2"] != 0 or axis["_fTimeDisplay"] or axis["_fTimeFormat"] != b"" or axis["_fLabels"] or axis["_fModLabs"]:
            raise NotImplementedError
        cursor.write_data(sink, b"\x00" * 20)
        # cursor.write_fields(sink, self._format_taxis_2,
        #                     axis["_fFirst"],
        #                     axis["_fLast"],
        #                     axis["_fBits2"],
        #                     axis["_fTimeDisplay"])
        # cursor.write_string(sink, axis["_fTimeFormat"])
        # self.write_tlist(cursor, sink, axis["_fLabels"])
        # self.write_tlist(cursor, sink, axis["_fModLabs"])
    def length_taxis(self, axis):
        return (self.length_tnamed(axis["_fName"], axis["_fTitle"]) +
                self.length_tattaxis() +
                self._format_taxis_1.size +
                self.length_tarray(axis["_fXbins"]) +
                20 + 6)
                # self._format_taxis_2.size +
                # uproot.write.sink.cursor.Cursor.length_string(axis["_fTimeFormat"]) +
                # self.length_tlist(axis["_fLabels"]) +
                # self.length_tlist(axis["_fModLabs"]))

    _format_th1_1 = struct.Struct(">i")
    _format_th1_2 = struct.Struct(">hhdddddddd")
    _format_th1_3 = struct.Struct(">iBii")
    def write_th1(self, cursor, sink, name):
        cnt = numpy.int64(self.length_th1(name) - 4) | uproot.const.kByteCountMask
        vers = 8
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_tnamed(cursor, sink, name, self.fTitle)
        self.write_tattline(cursor, sink)
        self.write_tattfill(cursor, sink)
        self.write_tattmarker(cursor, sink)
        cursor.write_fields(sink, self._format_th1_1, self.fields["_fNcells"])
        self.write_taxis(cursor, sink, self.fXaxis)
        self.write_taxis(cursor, sink, self.fYaxis)
        self.write_taxis(cursor, sink, self.fZaxis)
        cursor.write_fields(sink, self._format_th1_2,
                            self.fields["_fBarOffset"],
                            self.fields["_fBarWidth"],
                            self.fields["_fEntries"],
                            self.fields["_fTsumw"],
                            self.fields["_fTsumw2"],
                            self.fields["_fTsumwx"],
                            self.fields["_fTsumwx2"],
                            self.fields["_fMaximum"],
                            self.fields["_fMinimum"],
                            self.fields["_fNormFactor"])
        self.write_tarray(cursor, sink, self.fields["_fContour"])
        self.write_tarray(cursor, sink, self.fields["_fSumw2"])
        cursor.write_string(sink, self.fields["_fOption"])
        self.write_tlist(cursor, sink, self.fields["_fFunctions"])
        if len(self.fields["_fBuffer"]) != 0:
            raise NotImplementedError
        cursor.write_fields(sink, self._format_th1_3,
                            self.fields["_fBufferSize"],
                            0,     # FIXME: empty fBuffer
                            self.fields["_fBinStatErrOpt"],
                            self.fields["_fStatOverflows"])
    def length_th1(self, name):
        return (self.length_tnamed(name, self.fTitle) +
                self.length_tattline() +
                self.length_tattfill() +
                self.length_tattmarker() +
                self._format_th1_1.size +
                self.length_taxis(self.fXaxis) +
                self.length_taxis(self.fYaxis) +
                self.length_taxis(self.fZaxis) +
                self._format_th1_2.size +
                self.length_tarray(self.fields["_fContour"]) +
                self.length_tarray(self.fields["_fSumw2"]) +
                uproot.write.sink.cursor.Cursor.length_string(self.fields["_fOption"]) +
                self.length_tlist(self.fields["_fFunctions"]) +
                self._format_th1_3.size +
                6)

    def write(self, cursor, sink, name):
        cnt = numpy.int64(self.length(name) - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_th1(cursor, sink, name)
        self.write_tarray(cursor, sink, self.valuesarray)

    def length(self, name):
        return self.length_th1(name) + self.length_tarray(self.valuesarray) + 6
