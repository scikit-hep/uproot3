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

import numbers
import math

import numpy

import uproot.rootio

class TH1Methods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def __repr__(self):
        if hasattr(self, "fName"):
            return "<{0} {1} 0x{2:012x}>".format(self.classname, repr(self.fName), id(self))
        else:
            return "<{0} at 0x{1:012x}>".format(self.classname, id(self))

    @property
    def name(self):
        return getattr(self, "fName", None)

    @property
    def title(self):
        return getattr(self, "fTitle", None)

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
                weights = 1.0

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

    @property
    def hv(self):
        import uproot._connect.to_holoviews
        return uproot._connect.to_holoviews.TH1Methods_hv(self)

uproot.rootio.methods["TH1"] = TH1Methods
