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
        else:
            return int(math.floor(self.fXaxis.fNbins * (data - low) / (high - low))) + 1

    def fill(self, data, weights=None):
        low = self.fXaxis.fXmin
        high = self.fXaxis.fXmax

        if isinstance(data, numbers.Real):
            if weights is None:
                weights = 1

            if data < low:
                self[0] += weight
            elif data >= high:
                self[-1] += weight
            else:
                self[int(math.floor(self.fXaxis.fNbins * (data - low) / (high - low))) + 1] += weights

        else:
            if not isinstance(data, numpy.ndarray):
                data = numpy.array(data)

            if isinstance(weights, numbers.Real):
                weights = numpy.empty_like(data)

            freq, edges = numpy.histogram(data,
                                          bins=numpy.linspace(low, high, self.fXaxis.fNbins + 1),
                                          weights=weights,
                                          density=False)
            for i, x in enumerate(freq):
                self[i + 1] += x

            underflows = (data < low)
            overflows = (data >= high)

            if isinstance(weights, numpy.ndarray):
                self[0] += weights[underflows].sum()
                self[-1] += weights[overflows].sum()
            else:
                self[0] += underflows.sum()
                self[-1] += overflows.sum()

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

        intervals = ["[{0:<.4g}, {1:<.4g})".format(l, h) for l, h in [self.interval(i) for i in range(len(self))]]
        intervals[-1] = intervals[-1][:-1] + "]"   # last interval is closed on top edge
        intervalswidth = max(len(x) for x in intervals)

        values = ["{0:<.4g}".format(float(x)) for x in self]
        valueswidth = max(len(x) for x in values)

        minimumtext = "{0:<.4g}".format(minimum)
        maximumtext = "{0:<.4g}".format(maximum)

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

def hist(numbins, low, high, name=None, title=None):
    out = TH1()
    out.fXaxis = TAxis()
    out.fXaxis.fNbins = int(numbins)
    out.fXaxis.fXmin = float(low)
    out.fXaxis.fXmax = float(high)
    out.fName = name
    out.fTitle = title
    out.extend([0] * (numbins + 2))
    return out

if numba is not None:
    class Regular1dType(numba.types.Type):
        def __init__(self, valuetype):
            super(Regular1dType, self).__init__(name="Regular1dType")
            self.valuetype = valuetype
            self.obj = numba.types.PyObject("obj")
            self.numbins = numba.types.int64
            self.low = numba.types.float64
            self.high = numba.types.float64
            if self.valuetype is int:
                self.data = numba.types.int64[:]
            else:
                self.data = numba.types.float64[:]

    @numba.extending.typeof_impl.register(TH1Methods)
    def th1_typeof(val, c):
        assert isinstance(val, TH1Methods)
        if val.classname == "TH1F" or val.classname == "TH1D":
            return Regular1dType(float)
        else:
            return Regular1dType(int)

    @numba.extending.register_model(Regular1dType)
    class Regular1dModel(numba.datamodel.models.StructModel):
        def __init__(self, dmm, fe_type):
            members = [(x, getattr(fe_type, x)) for x in "obj", "numbins", "low", "high", "data"]
            super(Regular1dModel, self).__init__(dmm, fe_type, members)

    @numba.extending.unbox(Regular1dType)
    def th1_unbox(typ, obj, c):
        struct = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder)

        numbins_obj = c.pyapi.object_getattr_string(obj, "numbins")
        low_obj = c.pyapi.object_getattr_string(obj, "low")
        high_obj = c.pyapi.object_getattr_string(obj, "high")

        array_fcn = c.pyapi.unserialize(c.pyapi.serialize_object(numpy.array))
        valuetype_obj = c.pyapi.unserialize(c.pyapi.serialize_object(typ.valuetype))
        array_obj = c.pyapi.call_function_objargs(array_fcn, (obj, valuetype_obj))

        struct.obj = obj
        struct.numbins = c.pyapi.long_as_longlong(numbins_obj)
        struct.low = c.pyapi.float_as_double(low_obj)
        struct.high = c.pyapi.float_as_double(high_obj)
        struct.data = c.unbox(typ.data, array_obj).value

        c.pyapi.decref(numbins_obj)
        c.pyapi.decref(low_obj)
        c.pyapi.decref(high_obj)
        c.pyapi.decref(array_fcn)
        c.pyapi.decref(valuetype_obj)
        c.pyapi.decref(array_obj)

        is_error = numba.cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
        return numba.extending.NativeValue(struct._getvalue(), is_error=is_error)

    def th1_merge(obj, data):
        for i, x in enumerate(data):
            obj[i] = x

    @numba.extending.box(Regular1dType)
    def th1_box(typ, val, c):
        struct = numba.cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
        obj = struct.obj

        array_obj = c.box(typ.data, struct.data)
        merge_fcn = c.pyapi.unserialize(c.pyapi.serialize_object(th1_merge))

        c.pyapi.call_function_objargs(merge_fcn, (obj, array_obj))

        c.pyapi.decref(array_obj)

        return obj

def doit():
    @numba.njit
    def testy(x):
        return x

    h = hist(10, -3.0, 3.0)
    h[3] = 7
    print h, h.values
    out = testy(h)
    print out
    print out.name, out.low, out.high, out.values
    out2 = testy(out)
    print out2
    print out2.name, out2.low, out2.high, out2.values
    print out
    print out.name, out.low, out.high, out.values
    print h
    print h.name, h.low, h.high, h.values
