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
    def __init__(self, histogram):       # histogram is an uproot_methods.classes.TH1.Methods
        if isinstance(histogram._fTitle, bytes):
            self.fTitle = histogram._fTitle
        else:
            self.fTitle = histogram._fTitle.encode("utf-8")

        if isinstance(histogram._classname, bytes):
            self.fClassName = histogram._classname
        else:
            self.fClassName = histogram._classname.encode("utf-8")

        self.fXaxis = self.emptyaxis("xaxis", 1.0)
        self.fXaxis.update(histogram._fXaxis.__dict__)

        self.fYaxis = self.emptyaxis("yaxis", 0.0)
        if hasattr(histogram, "_fYaxis"):
            self.fYaxis.update(histogram._fYaxis.__dict__)

        self.fZaxis = self.emptyaxis("zaxis", 1.0)
        if hasattr(histogram, "_fZaxis"):
            self.fYaxis.update(histogram._fZaxis.__dict__)

        self.fields = {
            "_fLineColor": 602,
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

        for n in list(self.fields):
            if hasattr(histogram, n):
                self.fields[n] = getattr(histogram, n)

        self.values = histogram.allvalues()

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

    def write_tnamed(self, cursor, sink, name):
        cnt = numpy.int64(uproot.write.sink.cursor.Cursor.length_strings([name, self.fTitle]) - 4) | uproot.const.kByteCountMask
        vers = 1
        self.write_tobject(cursor, sink)
        cursor.write_string(sink, name)
        cursor.write_string(sink, self.fTitle)

    _format_tarray = struct.Struct(">i")
    def write_tarray(self, cursor, sink, values):
        cursor.write_fields(sink, self._format_tarray, len(values))
        cursor.write_array(values)

    _format_tlist = struct.Struct(">i")
    def write_tlist(self, cursor, sink, values):
        cnt = numpy.int64(self.length_tlist(values) - 4) | uproot.const.kByteCountMask
        vers = 5
        self.write_tobject(cursor, sink)
        cursor.write_string(sink, b"")
        cursor.write_fields(sink, self._format_tlist, len(values))
        for value in values:
            raise NotImplementedError

    _format_tattline = struct.Struct(">hhh")
    def write_tattline(self, cursor, sink):
        cnt = numpy.int64(self.length_tattline() - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        cursor.write_fields(sink, self._format_tattline,
                            self.fields["_fLineColor"],
                            self.fields["_fLineStyle"],
                            self.fields["_fLineWidth"])

    _format_tattfill = struct.Struct(">hh")
    def write_tattfill(self, cursor, sink):
        cnt = numpy.int64(self.length_tattfill() - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        cursor.write_fields(sink, self._format_tattfill,
                            self.fields["_fFillColor"],
                            self.fields["_fFillStyle"])

    _format_tattmarker = struct.Struct(">hhf")
    def write_tattmarker(self, cursor, sink):
        cnt = numpy.int64(self.length_tattmarker() - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        cursor.write_fields(sink, self._format_tattmarker,
                            self.fields["_fMarkerColor"],
                            self.fields["_fMarkerStyle"],
                            self.fields["_fMarkerSize"])

    _format_tattaxis = struct.Struct(">ihhhfffffhh")
    def write_tattaxis(self, cursor, sink, axis):
        cnt = numpy.int64(self.length_tattmarker() - 4) | uproot.const.kByteCountMask
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
                            
    _format_taxis_1 = struct.Struct(">idd")
    _format_taxis_2 = struct.Struct(">iiH?")
    def write_taxis(self, cursor, sink, axis):
        cnt = numpy.int64(self.length_taxis(axis) - 4) | uproot.const.kByteCountMask
        vers = 10
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_tnamed(cursor, sink, axis["_fName"])
        self.write_tattaxis(cursor, sink, axis)
        cursor.write_fields(sink, self._format_taxis_1,
                            axis["_fNbins"],
                            axis["_fXmin"],
                            axis["_fXmax"])
        self.write_tarray(cursor, sink, numpy.array(axis["_fXbins"], dtype=">f8"))
        cursor.write_fields(sink, self._format_taxis_2,
                            axis["_fFirst"],
                            axis["_fLast"],
                            axis["_fBits2"],
                            axis["_fTimeDisplay"])
        cursor.write_string(sink, axis["_fTimeFormat"])
        self.write_tlist(cursor, sink, axis["_fLabels"])
        self.write_tlist(cursor, sink, axis["_fModLabs"])

    _format_th1_1 = struct.Struct(">i")
    _format_th1_2 = struct.Struct(">hhdddddddd")
    _format_th1_3 = struct.Struct(">iBii")
    def write_th1(self, cursor, sink, name):
        cnt = numpy.int64(self.length_th1(name) - 4) | uproot.const.kByteCountMask
        vers = 8
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_tnamed(cursor, sink, name)
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
        self.write_tarray(cursor, sink, numpy.array(self.fields["_fContour"], dtype=">f8"))
        self.write_tarray(cursor, sink, numpy.array(self.fields["_fSumw2"], dtype=">f8"))
        cursor.write_string(sink, self.fields["_fOption"])
        self.write_tlist(cursor, sink, self.fields["_fFunctions"])
        cursor.write_fields(sink, self._format_th1_3,
                            self.fields["_fBufferSize"],
                            0,     # FIXME: empty fBuffer
                            self.fields["fBinStatErrOpt"],
                            self.fields["fStatOverflows"])
        
    def write_th1d(self, cursor, sink, name):
        cnt = numpy.int64(self.length_th1d(name) - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_th1(cursor, sink, name)
        self.write_tarray(cursor, sink, numpy.array(self.values, dtype=">f8"))

    def write_th1f(self, cursor, sink, name):
        cnt = numpy.int64(self.length_th1f(name) - 4) | uproot.const.kByteCountMask
        vers = 2
        cursor.write_fields(sink, self._format_cntvers, cnt, vers)
        self.write_th1(cursor, sink, name)
        self.write_tarray(cursor, sink, numpy.array(self.values, dtype=">f4"))
        
    # def length_axis(self):
    #     pass

    # def write_axis(self, cursor, sink):
    #     cursor.write_string(sink, )

    # def length(self, name):
    #     pass

    # def write(self, cursor, sink, name):
    #     pass
