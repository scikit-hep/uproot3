#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct

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
            raise NotImplementedError(self.fClassName)
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
                "_fZmax": 0.0}

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
        return self.length_tobject() + uproot.write.sink.cursor.Cursor.length_strings([name, title]) + self._format_cntvers.size

    _format_tarray = struct.Struct(">i")
    def return_tarray(self, cursor, values):
        return cursor.return_fields(self._format_tarray, values.size) + cursor.return_array(values)

    def length_tarray(self, values):
        return self._format_tarray.size + values.nbytes

    _format_tlist = struct.Struct(">i")
    def return_tlist(self, cursor, values):
        cnt = numpy.int64(self.length_tlist(values) - 4) | uproot.const.kByteCountMask
        vers = 5
        for value in values:
            raise NotImplementedError
        return (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_tobject(cursor) +
            cursor.return_string(b"") + cursor.return_fields(self._format_tlist, len(values)))
    def length_tlist(self, values):
        return self.length_tobject() + uproot.write.sink.cursor.Cursor.length_string(b"") + self._format_tlist.size + sum(0 for x in values) + self._format_cntvers.size

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

    _format_tattaxis = struct.Struct(">ihhhfffffhh")
    def return_tattaxis(self, cursor, axis):
        cnt = numpy.int64(self.length_tattaxis() - 4) | uproot.const.kByteCountMask
        vers = 4
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                cursor.return_fields(self._format_tattaxis,
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
    def length_tattaxis(self):
        return self._format_tattaxis.size + self._format_cntvers.size

    _format_taxis_1 = struct.Struct(">idd")
    _format_taxis_2 = struct.Struct(">iiH?")
    def return_taxis(self, cursor, axis):
        cnt = numpy.int64(self.length_taxis(axis) - 4) | uproot.const.kByteCountMask
        vers = 10
        if axis["_fFirst"] != 0 or axis["_fLast"] != 0 or axis["_fBits2"] != 0 or axis["_fTimeDisplay"] or axis["_fTimeFormat"] != b"" or axis["_fLabels"] or axis["_fModLabs"]:
            raise NotImplementedError
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                self.return_tnamed(cursor, axis["_fName"], axis["_fTitle"]) +
                self.return_tattaxis(cursor, axis) +
                cursor.return_fields(self._format_taxis_1,
                            axis["_fNbins"],
                            axis["_fXmin"],
                            axis["_fXmax"]) +
                self.return_tarray(cursor, axis["_fXbins"]) +
                (b"\x00" * 20))
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
    def return_th1(self, cursor, name):
        cnt = numpy.int64(self.length_th1(name) - 4) | uproot.const.kByteCountMask
        vers = 8
        if len(self.fields["_fBuffer"]) != 0:
            raise NotImplementedError
        return (cursor.return_fields(self._format_cntvers, cnt, vers) +
                self.return_tnamed(cursor, name, self.fTitle) +
                self.return_tattline(cursor) +
                self.return_tattfill(cursor) +
                self.return_tattmarker(cursor) +
                cursor.return_fields(self._format_th1_1, self.fields["_fNcells"]) +
                self.return_taxis(cursor, self.fXaxis) +
                self.return_taxis(cursor, self.fYaxis) +
                self.return_taxis(cursor, self.fZaxis) +
                cursor.return_fields(self._format_th1_2,
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
                self.return_tarray(cursor, self.fields["_fContour"]) +
                self.return_tarray(cursor, self.fields["_fSumw2"]) +
                cursor.return_string(self.fields["_fOption"]) +
                self.return_tlist(cursor, self.fields["_fFunctions"]) +
                cursor.return_fields(self._format_th1_3,
                            self.fields["_fBufferSize"],
                            0,     # FIXME: empty fBuffer
                            self.fields["_fBinStatErrOpt"],
                            self.fields["_fStatOverflows"]))

    _format_th2_1 = struct.Struct(">dddd")
    def return_th2(self, cursor, name):
        cnt = numpy.int64(self.length_th2(name) - 4) | uproot.const.kByteCountMask
        vers = 4
        return (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th1(cursor, name) +
                cursor.return_fields(self._format_th2_1,
                                     self.fields["_fScalefactor"],
                                     self.fields["_fTsumwy"],
                                     self.fields["_fTsumwy2"],
                                     self.fields["_fTsumwxy"]))

    _format_th3_1 = struct.Struct(">ddddddd")
    def return_th3(self, cursor, name):
        cnt = numpy.int64(self.length_th3(name) - 4) | uproot.const.kByteCountMask
        vers = 5
        return (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th1(cursor, name) +
                self.return_tatt3d(cursor) + cursor.return_fields(self._format_th3_1,
                                                                  self.fields["_fTsumwy"],
                                                                  self.fields["_fTsumwy2"],
                                                                  self.fields["_fTsumwxy"],
                                                                  self.fields["_fTsumwz"],
                                                                  self.fields["_fTsumwz2"],
                                                                  self.fields["_fTsumwxz"],
                                                                  self.fields["_fTsumwyz"]))

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
                self._format_th1_3.size + self._format_cntvers.size)

    def length_th2(self, name):
        return self.length_th1(name) + self._format_th2_1.size + self._format_cntvers.size

    def length_th3(self, name):
        return self.length_th1(name) + self._format_th3_1.size + self.length_tatt3d() + self._format_cntvers.size

    def return_tatt3d(self, cursor):
        cnt = numpy.int64(self.length_tatt3d() - 4) | uproot.const.kByteCountMask
        vers = 1
        return cursor.return_fields(self._format_cntvers, cnt, vers)

    def length_tatt3d(self):
        return self._format_cntvers.size

    def return_th1d(self, cursor, name):
        cnt = numpy.int64(self.length_th1d(name) - 4) | uproot.const.kByteCountMask
        vers = 2
        return (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th1(cursor, name)
                + self.return_tarray(cursor, self.valuesarray))

    def length_th1d(self, name):
        return self.length_th1(name) + self.length_tarray(self.valuesarray) + self._format_cntvers.size

    def return_th2d(self, cursor, name):
        cnt = numpy.int64(self.length_th2d(name) - 4) | uproot.const.kByteCountMask
        vers = 3
        return (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th2(cursor, name)
                + self.return_tarray(cursor, self.valuesarray))

    def length_th2d(self, name):
        return self.length_th2(name) + self.length_tarray(self.valuesarray) + self._format_cntvers.size

    _format_tprofile = struct.Struct(">idddd")
    def write(self, context, cursor, name, compression, key, keycursor):
        givenbytes = 0
        cnt = numpy.int64(self.length(name) - 4) | uproot.const.kByteCountMask
        if "TH1" in self.fClassName.decode("utf-8"):
            vers = 2
            givenbytes = cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th1(cursor, name)
            givenbytes += self.return_tarray(cursor, self.valuesarray)
        elif "TH2" in self.fClassName.decode("utf-8"):
            vers = 3
            givenbytes = cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th2(cursor, name)
            givenbytes += self.return_tarray(cursor, self.valuesarray)
        elif "TH3" in self.fClassName.decode("utf-8"):
            vers = 3
            givenbytes = cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th3(cursor, name)
            givenbytes += self.return_tarray(cursor, self.valuesarray)
        elif "TProfile" == self.fClassName.decode("utf-8"):
            vers = 6
            givenbytes = (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th1d(cursor, name)
                            + self.return_tarray(cursor, self.fields["_fBinEntries"]) +
                            cursor.return_fields(self._format_tprofile, self.fields["_fErrorMode"], self.fields["_fYmin"],
                            self.fields["_fYmax"], self.fields["_fTsumwy"], self.fields["_fTsumwy2"]) +
                            self.return_tarray(cursor, self.fields["_fBinSumw2"]))
        elif "TProfile2D" == self.fClassName.decode("utf-8"):
            vers = 7
            givenbytes = (cursor.return_fields(self._format_cntvers, cnt, vers) + self.return_th2d(cursor, name)
                            + self.return_tarray(cursor, self.fields["_fBinEntries"]) +
                            cursor.return_fields(self._format_tprofile, self.fields["_fErrorMode"], self.fields["_fZmin"],
                            self.fields["_fZmax"], self.fields["_fTsumwz"], self.fields["_fTsumwz2"]) +
                            self.return_tarray(cursor, self.fields["_fBinSumw2"]))
        uproot.write.compress.write(context, cursor, givenbytes, compression, key, keycursor)

    def length(self, name):
        if "TH1" in self.fClassName.decode("utf-8"):
            return self.length_th1(name) + self.length_tarray(self.valuesarray) + self._format_cntvers.size
        elif "TH2" in self.fClassName.decode("utf-8"):
            return self.length_th2(name) + self.length_tarray(self.valuesarray) + self._format_cntvers.size
        elif "TH3" in self.fClassName.decode("utf-8"):
            return self.length_th3(name) + self.length_tarray(self.valuesarray) + self._format_cntvers.size
        elif "TProfile" == self.fClassName.decode("utf-8"):
            return (self.length_th1d(name) + self.length_tarray(self.fields["_fBinEntries"]) + self._format_tprofile.size
                    + self.length_tarray(self.fields["_fBinSumw2"]) + self._format_cntvers.size)
        elif "TProfile2D" == self.fClassName.decode("utf-8"):
            return (self.length_th2d(name) + self.length_tarray(self.fields["_fBinEntries"]) + self._format_tprofile.size
                    + self.length_tarray(self.fields["_fBinSumw2"]) + self._format_cntvers.size)

