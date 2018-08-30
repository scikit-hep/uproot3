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

import math

import awkward
import awkward.type
import awkward.util

import uproot.interp.interp
import uproot.interp.numerical

class _JaggedArrayPrep(object):
    def __init__(self, counts, content):
        self.counts = counts
        self.content = content

def _destructive_divide(array, divisor):
    if divisor == 1:
        pass
    elif divisor == 2:
        awkward.util.numpy.right_shift(array, 1, out=array)
    elif divisor == 4:
        awkward.util.numpy.right_shift(array, 2, out=array)
    elif divisor == 8:
        awkward.util.numpy.right_shift(array, 3, out=array)
    else:
        awkward.util.numpy.floor_divide(array, divisor, out=array)
    return array

class asjagged(uproot.interp.interp.Interpretation):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.interp.interp.Interpretation.__metaclass__,), {})

    def __init__(self, content, skipbytes=0):
        self.content = content
        self.skipbytes = skipbytes

    def __repr__(self):
        return "asjagged({0})".format(repr(self.content))

    def to(self, todtype=None, todims=None, skipbytes=None):
        if skipbytes is None:
            skipbytes = self.skipbytes
        return asjagged(self.content.to(todtype, todims), skipbytes)

    @property
    def identifier(self):
        return "asjagged({0}{1})".format(repr(self.content), "" if self.skipbytes == 0 else ",{0}".format(self.skipbytes))

    @property
    def type(self):
        return awkward.type.ArrayType(awkward.util.numpy.inf, self.content.type)

    def empty(self):
        return awkward.JaggedArray(awkward.util.numpy.empty(0, dtype=awkward.util.INDEXTYPE), awkward.util.numpy.empty(0, dtype=awkward.util.INDEXTYPE), self.content.empty())

    def compatible(self, other):
        return isinstance(other, asjagged) and self.content.compatible(other.content)

    def numitems(self, numbytes, numentries):
        return self.content.numitems(numbytes - numentries * self.skipbytes, numentries)

    def source_numitems(self, source):
        return self.content.source_numitems(source.content)

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        if local_entrystart == local_entrystop:
            return awkward.JaggedArray.fromoffsets([0], self.content.fromroot(data, None, local_entrystart, local_entrystop))
        else:
            if self.skipbytes == 0:
                offsets = _destructive_divide(byteoffsets, self.content.itemsize)
                starts  = offsets[local_entrystart     : local_entrystop    ]
                stops   = offsets[local_entrystart + 1 : local_entrystop + 1]
                content = self.content.fromroot(data, None, starts[0], stops[-1])
                return awkward.JaggedArray(starts, stops, content)

            else:
                bytestarts = byteoffsets[local_entrystart     : local_entrystop    ] + self.skipbytes
                bytestops  = byteoffsets[local_entrystart + 1 : local_entrystop + 1]

                mask = awkward.util.numpy.zeros(len(data), dtype=awkward.util.numpy.int8)
                mask[bytestarts[bytestarts < len(data)]] = 1
                awkward.util.numpy.add.at(mask, bytestops[bytestops < len(data)], -1)
                awkward.util.numpy.cumsum(mask, out=mask)
                data = data[mask.view(awkward.util.numpy.bool_)]

                content = self.content.fromroot(data, None, 0, bytestops[-1])

                itemsize = 1
                sub = self.content
                while hasattr(sub, "content"):
                    sub = sub.content
                if isinstance(sub, uproot.interp.numerical.asdtype):
                    itemsize = sub.fromdtype.itemsize

                counts = bytestops - bytestarts
                shift = math.log(itemsize, 2)
                if shift == round(shift):
                    awkward.util.numpy.right_shift(counts, int(shift), out=counts)
                else:
                    awkward.util.numpy.floor_divide(counts, itemsize, out=counts)

                offsets = awkward.util.numpy.empty(len(counts) + 1, awkward.util.INDEXTYPE)
                offsets[0] = 0
                awkward.util.numpy.cumsum(counts, out=offsets[1:])

                return awkward.JaggedArray(offsets[:-1], offsets[1:], content)

    def destination(self, numitems, numentries):
        content = self.content.destination(numitems, numentries)
        counts = awkward.util.numpy.empty(numentries, dtype=awkward.util.INDEXTYPE)
        return _JaggedArrayPrep(counts, content)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        self.content.fill(source.content, destination.content, itemstart, itemstop, entrystart, entrystop)
        destination.counts[entrystart:entrystop] = source.counts

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        destination.content = self.content.clip(destination.content, itemstart, itemstop, entrystart, entrystop)
        destination.counts = destination.counts[entrystart:entrystop]
        return destination

    def finalize(self, destination, branch):
        content = self.content.finalize(destination.content, branch)
        leafcount = None
        if len(branch._fLeaves) == 1:
            leafcount = branch._fLeaves[0]._fLeafCount

        out = awkward.Methods.maybemixin(type(content), awkward.JaggedArray).fromcounts(destination.counts, content)
        out.leafcount = leafcount
        return out
