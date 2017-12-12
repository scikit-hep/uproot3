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

import sys
import numbers
import math

import numpy
try:
    import numba
    import llvmlite
except ImportError:
    numba = None

import uproot.rootio

class TH1Methods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def __repr__(self):
        if self.fName is None:
            return "<{0} at 0x{1:012x}>".format(self.classname, id(self))
        else:
            return "<{0} {1} 0x{2:012x}>".format(self.classname, repr(self.fName), id(self))

    @property
    def name(self):
        return self.fName

    @property
    def title(self):
        return self.fTitle

    @property
    def numbins(self):
        return self.fXaxis.fNbins

    @property
    def low(self):
        return self.fXaxis.fXmin

    @property
    def high(self):
        return self.fXaxis.fXmax

    @property
    def underflows(self):
        return self[0]

    @property
    def overflows(self):
        return self[-1]

    @property
    def values(self):
        return self[1:-1]

    @property
    def allvalues(self):
        return self[:]

    @property
    def numpy(self):
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        norm = (high - low) / self.fXaxis.fNbins
        freq = numpy.array(self.values, dtype=self._dtype.newbyteorder("="))
        edges = numpy.array([i*norm + low for i in range(self.numbins + 1)])
        return freq, edges

    def interval(self, index):
        if index < 0:
            index += len(self)

        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        if index == 0:
            return (float("-inf"), low)
        elif index == len(self) - 1:
            return (high, float("inf"))
        else:
            norm = (high - low) / self.fXaxis.fNbins
            return (index - 1)*norm + low, index*norm + low

    def index(self, data):
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        if data < low:
            return 0
        elif data >= high:
            return len(self) - 1
        elif not math.isnan(data):
            return int(math.floor(self.fXaxis.fNbins * (data - low) / (high - low))) + 1

    def fill(self, datum):
        numbins = self.fXaxis.fNbins
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        if datum < low:
            self[0] += 1
        elif datum >= high:
            self[-1] += 1
        else:
            self[int(math.floor(numbins * (datum - low) / (high - low))) + 1] += 1

    def fillw(self, datum, weight):
        numbins = self.fXaxis.fNbins
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax
        if datum < low:
            self[0] += weight
        elif datum >= high:
            self[-1] += weight
        else:
            self[int(math.floor(numbins * (datum - low) / (high - low))) + 1] += weight

    def fillall(self, data):
        numbins = self.fXaxis.fNbins
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax

        if not isinstance(data, numpy.ndarray):
            data = numpy.array(data)

        freq, edges = numpy.histogram(data, bins=numbins, range=(low, high), density=False)
        for i, x in enumerate(freq):
            self[i + 1] += x

        self[0] += (data < low).sum()
        self[-1] += (data >= high).sum()

    def fillallw(self, data, weights):
        numbins = self.fXaxis.fNbins
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax

        if not isinstance(data, numpy.ndarray):
            data = numpy.array(data)

        if isinstance(weights, numbers.Real):
            weights = numpy.empty_like(data)

        freq, edges = numpy.histogram(data, bins=numbins, range=(low, high), weights=weights, density=False)
        for i, x in enumerate(freq):
            self[i + 1] += x

        self[0] += weights[data < low].sum()
        self[-1] += weights[data >= high].sum()

    def __add__(self, other):
        if not isinstance(other, TH1Methods) or self.numbins != other.numbins or self.low != other.low or self.high != other.high:
            raise TypeError("TH1 histograms can only be combined with other TH1 histograms")
        return hist(self.numbins, self.low, self.high, name=(self.name if self.name is not None else other.name), title=(self.title if self.title is not None else other.title), values=[x + y for x, y in zip(self.values, other.values)])

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        if not isinstance(other, TH1Methods) or self.numbins != other.numbins or self.low != other.low or self.high != other.high:
            raise TypeError("TH1 histograms can only be combined with other TH1 histograms")
        for i in range(len(self)):
            self[i] = other[i]
        return self

    @property
    def xlabels(self):
        return [str(x) for x in self.fXaxis.fLabels]

    def show(self, width=80, minimum=None, maximum=None, stream=sys.stdout):
        if minimum is None:
            minimum = min(self)
            if minimum < 0:
                minimum *= 1.05
            else:
                minimum = 0

        if maximum is None:
            maximum = max(self) * 1.05

        if maximum <= minimum:
            average = (minimum + maximum) / 2.0
            minimum = average - 0.5
            maximum = average + 0.5

        if self.xlabels is None:
            intervals = ["[{0:<.5g}, {1:<.5g})".format(l, h) for l, h in [self.interval(i) for i in range(len(self))]]
            intervals[-1] = intervals[-1][:-1] + "]"   # last interval is closed on top edge
        else:
            intervals = ["(underflow)"] + [self.xlabels[i] if i < len(self.xlabels) else self.interval(i+1) for i in range(self.numbins)] + ["(overflow)"]

        intervalswidth = max(len(x) for x in intervals)

        values = ["{0:<.5g}".format(float(x)) for x in self]
        valueswidth = max(len(x) for x in values)

        minimumtext = "{0:<.5g}".format(minimum)
        maximumtext = "{0:<.5g}".format(maximum)

        plotwidth = max(len(minimumtext) + len(maximumtext), width - (intervalswidth + 1 + valueswidth + 1 + 2))
        scale = minimumtext + " "*(plotwidth + 2 - len(minimumtext) - len(maximumtext)) + maximumtext

        norm = float(plotwidth) / float(maximum - minimum)
        zero = int(round((0.0 - minimum)*norm))
        line = numpy.empty(plotwidth, dtype=numpy.uint8)

        formatter = "{0:<%s} {1:<%s} |{2}|" % (intervalswidth, valueswidth)
        line[:] = ord("-")
        if minimum != 0 and 0 <= zero < plotwidth:
            line[zero] = ord("+")
        capstone = " " * (intervalswidth + 1 + valueswidth + 1) + "+" + str(line.tostring().decode("ascii")) + "+"

        out = [" "*(intervalswidth + valueswidth + 2) + scale]
        out.append(capstone)
        for interval, value, x in zip(intervals, values, self):
            line[:] = ord(" ")

            pos = int(round((x - minimum)*norm))
            if x < 0:
                line[pos:zero] = ord("*")
            else:
                line[zero:pos] = ord("*")

            if minimum != 0 and 0 <= zero < plotwidth:
                line[zero] = ord("|")

            out.append(formatter.format(interval, value, str(line.tostring().decode("ascii"))))

        out.append(capstone)
        out = "\n".join(out)
        if stream is None:
            return out
        else:
            stream.write(out)
            stream.write("\n")

    @property
    def holoviews(self):
        import uproot._connect.to_holoviews
        return uproot._connect.to_holoviews.TH1Methods_holoviews(self)

    @property
    def bokeh(self):
        import uproot._connect.to_bokeh
        return uproot._connect.to_bokeh.TH1Methods_bokeh(self)

uproot.rootio.methods["TH1"] = TH1Methods

class TH1(TH1Methods, list):
    def _type(self):
        if all(isinstance(x, numbers.Integral) for x in self):
            return int
        elif all(isinstance(x, numbers.Real) for x in self):
            return float
        else:
            raise TypeError("histogram bin values must be integers or floats")

    @property
    def classname(self):
        if self._type() is int:
            return "TH1I"
        else:
            return "TH1D"

    @property
    def _dtype(self):
        if self._type() is int:
            return numpy.dtype(">i4")
        else:
            return numpy.dtype(">f8")

class TAxis(object):
    classname = "TAxis"

def hist(numbins, low, high, name=None, title=None, values=None, allvalues=None, filldata=None):
    out = TH1()
    out.fXaxis = TAxis()
    out.fXaxis.fNbins = int(numbins)
    out.fXaxis.fXmin = float(low)
    out.fXaxis.fXmax = float(high)
    out.fName = name
    out.fTitle = title

    if values is None and allvalues is None:
        out.extend([0] * (numbins + 2))

    if values is not None:
        try:
            assert len(values) == numbins and all(isinstance(x, numbers.Real) for x in values)
        except (TypeError, AssertionError):
            raise ValueError("values must be an iterable of numbers with length numbins")
        out.extend([0] + values + [0])

    # allvalues takes precedence
    if allvalues is not None:
        try:
            assert len(allvalues) == numbins + 2 and all(isinstance(x, numbers.Real) for x in allvalues)
        except (TypeError, AssertionError):
            raise ValueError("allvalues must be an iterable of numbers with length numbins")
        out.extend(allvalues)

    # and filldata is accumulated on top of any values/allvalues
    if filldata is not None:
        out.fillall(filldata)

    return out

if numba is not None:
    class Regular1dType(numba.types.Type):
        def __init__(self):
            self.obj = numba.types.PyObject("obj")
            self.numbins = numba.types.int64
            self.low = numba.types.float64
            self.high = numba.types.float64

    class IntRegular1dType(Regular1dType):
        pythontype = int
        numbametatype = numba.types.Integer
        def __init__(self):
            Regular1dType.__init__(self)
            numba.types.Type.__init__(self, name="IntRegular1dType")
            self.allvalues = numba.types.int64[:]

    class FloatRegular1dType(Regular1dType):
        pythontype = float
        numbametatype = (numba.types.Integer, numba.types.Float)
        def __init__(self):
            Regular1dType.__init__(self)
            numba.types.Type.__init__(self, name="FloatRegular1dType")
            self.allvalues = numba.types.float64[:]

    intRegular1dType = IntRegular1dType()
    floatRegular1dType = FloatRegular1dType()

    @numba.extending.typeof_impl.register(TH1Methods)
    def th1_typeof(val, c):
        assert isinstance(val, TH1Methods)
        if val.classname == "TH1F" or val.classname == "TH1D":
            return floatRegular1dType
        else:
            return intRegular1dType

    @numba.extending.register_model(IntRegular1dType)
    class IntRegular1dModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [(x, getattr(fe_type, x)) for x in ("obj", "numbins", "low", "high", "allvalues")]
            numba.datamodel.models.StructModel.__init__(self, dmm, fe_type, members)

    @numba.extending.register_model(FloatRegular1dType)
    class FloatRegular1dModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [(x, getattr(fe_type, x)) for x in ("obj", "numbins", "low", "high", "allvalues")]
            numba.datamodel.models.StructModel.__init__(self, dmm, fe_type, members)

    numba.extending.make_attribute_wrapper(Regular1dType, "numbins", "numbins")
    numba.extending.make_attribute_wrapper(Regular1dType, "low", "low")
    numba.extending.make_attribute_wrapper(Regular1dType, "high", "high")
    numba.extending.make_attribute_wrapper(Regular1dType, "allvalues", "allvalues")

    @numba.extending.unbox(Regular1dType)
    def th1_unbox(typ, obj, c):
        struct = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)

        numbins_obj = c.pyapi.object_getattr_string(obj, "numbins")
        low_obj = c.pyapi.object_getattr_string(obj, "low")
        high_obj = c.pyapi.object_getattr_string(obj, "high")

        array_fcn = c.pyapi.unserialize(c.pyapi.serialize_object(numpy.array))
        pythontype_obj = c.pyapi.unserialize(c.pyapi.serialize_object(typ.pythontype))
        array_obj = c.pyapi.call_function_objargs(array_fcn, (obj, pythontype_obj))

        c.pyapi.incref(obj)
        struct.obj = obj
        struct.numbins = c.pyapi.long_as_longlong(numbins_obj)
        struct.low = c.pyapi.float_as_double(low_obj)
        struct.high = c.pyapi.float_as_double(high_obj)
        struct.allvalues = c.unbox(typ.allvalues, array_obj).value

        c.pyapi.decref(numbins_obj)
        c.pyapi.decref(low_obj)
        c.pyapi.decref(high_obj)
        c.pyapi.decref(array_fcn)
        c.pyapi.decref(pythontype_obj)
        c.pyapi.decref(array_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(struct._getvalue(), is_error=is_error)

    def th1_merge(obj, allvalues):
        obj[:] = allvalues

    @numba.extending.box(Regular1dType)
    def th1_box(typ, val, c):
        struct = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        obj = struct.obj

        array_obj = c.box(typ.allvalues, struct.allvalues)
        merge_fcn = c.pyapi.unserialize(c.pyapi.serialize_object(th1_merge))

        c.pyapi.call_function_objargs(merge_fcn, (obj, array_obj))

        c.pyapi.decref(array_obj)
        return obj

    def th1_fill(th1, datum):
        if datum < th1.low:
            th1.allvalues[0] += 1
        elif datum >= th1.high:
            th1.allvalues[-1] += 1
        elif not math.isnan(datum):
            th1.allvalues[int(math.floor(th1.numbins * (datum - th1.low) / (th1.high - th1.low))) + 1] += 1

    def th1_fillw(th1, datum, weight):
        if datum < th1.low:
            th1.allvalues[0] += weight
        elif datum >= th1.high:
            th1.allvalues[-1] += weight
        elif not math.isnan(datum):
            th1.allvalues[int(math.floor(th1.numbins * (datum - th1.low) / (th1.high - th1.low))) + 1] += weight

    def th1_fillall(th1, data):
        for datum in data:
            if datum < th1.low:
                th1.allvalues[0] += 1
            elif datum >= th1.high:
                th1.allvalues[-1] += 1
            elif not math.isnan(datum):
                th1.allvalues[int(math.floor(th1.numbins * (datum - th1.low) / (th1.high - th1.low))) + 1] += 1

    def th1_fillallw(th1, data, weight):
        for datum in data:
            if datum < th1.low:
                th1.allvalues[0] += weight
            elif datum >= th1.high:
                th1.allvalues[-1] += weight
            elif not math.isnan(datum):
                th1.allvalues[int(math.floor(th1.numbins * (datum - th1.low) / (th1.high - th1.low))) + 1] += weight

    for metatype in IntRegular1dType, FloatRegular1dType:
        @numba.extending.overload_method(metatype, "fill")
        def highlevel_fill(typ, datum):
            if isinstance(datum, numba.types.Number):
                return th1_fill

        @numba.extending.overload_method(metatype, "fillw")
        def highlevel_fillw(typ, datum, weight):
            if isinstance(datum, numba.types.Number) and isinstance(weight, typ.numbametatype):
                return th1_fillw

        @numba.extending.overload_method(metatype, "fillall")
        def highlevel_fillall(typ, data):
            if isinstance(data, numba.types.Array):
                return th1_fillall

        @numba.extending.overload_method(metatype, "fillallw")
        def highlevel_fillallw(typ, data, weights):
            if isinstance(data, numba.types.Array) and isinstance(weights, numba.types.Array) and isinstance(weights.dtype, typ.numbametatype):
                return th1_fillallw
