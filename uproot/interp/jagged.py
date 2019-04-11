#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import math

import uproot.interp.interp
import uproot.interp.numerical

class _JaggedArrayPrep(object):
    def __init__(self, counts, content):
        self.counts = counts
        self.content = content

def _destructive_divide(array, divisor, awkward):
    if divisor == 1:
        pass
    elif divisor == 2:
        awkward.numpy.right_shift(array, 1, out=array)
    elif divisor == 4:
        awkward.numpy.right_shift(array, 2, out=array)
    elif divisor == 8:
        awkward.numpy.right_shift(array, 3, out=array)
    else:
        awkward.numpy.floor_divide(array, divisor, out=array)
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

    def __repr__(self):
        return "asjagged({0}{1})".format(repr(self.content), "" if self.skipbytes == 0 else ", {0}".format(self.skipbytes))

    @property
    def identifier(self):
        return "asjagged({0}{1})".format(self.content.identifier, "" if self.skipbytes == 0 else ",{0}".format(self.skipbytes))

    @property
    def type(self):
        return self.awkward.type.ArrayType(self.awkward.numpy.inf, self.content.type)

    def empty(self):
        return self.awkward.JaggedArray(self.awkward.numpy.empty(0, dtype=self.awkward.JaggedArray.INDEXTYPE), self.awkward.numpy.empty(0, dtype=self.awkward.JaggedArray.INDEXTYPE), self.content.empty())

    def compatible(self, other):
        return isinstance(other, asjagged) and self.content.compatible(other.content)

    def numitems(self, numbytes, numentries):
        return self.content.numitems(numbytes - numentries * self.skipbytes, numentries)

    def source_numitems(self, source):
        return self.content.source_numitems(source.content)

    def fromroot(self, data, byteoffsets, local_entrystart, local_entrystop):
        if local_entrystart == local_entrystop:
            return self.awkward.JaggedArray.fromoffsets([0], self.content.fromroot(data, None, local_entrystart, local_entrystop))
        else:
            if self.skipbytes == 0:
                offsets = _destructive_divide(byteoffsets, self.content.itemsize, self.awkward)
                starts  = offsets[local_entrystart     : local_entrystop    ]
                stops   = offsets[local_entrystart + 1 : local_entrystop + 1]
                content = self.content.fromroot(data, None, starts[0], stops[-1])
                return self.awkward.JaggedArray(starts, stops, content)

            else:
                bytestarts = byteoffsets[local_entrystart     : local_entrystop    ] + self.skipbytes
                bytestops  = byteoffsets[local_entrystart + 1 : local_entrystop + 1]

                mask = self.awkward.numpy.zeros(len(data), dtype=self.awkward.numpy.int8)
                mask[bytestarts[bytestarts < len(data)]] = 1
                self.awkward.numpy.add.at(mask, bytestops[bytestops < len(data)], -1)
                self.awkward.numpy.cumsum(mask, out=mask)
                data = data[mask.view(self.awkward.numpy.bool_)]

                content = self.content.fromroot(data, None, 0, bytestops[-1])

                itemsize = 1
                sub = self.content
                while hasattr(sub, "content"):
                    sub = sub.content
                if isinstance(sub, uproot.interp.numerical.asdtype):
                    itemsize = sub.fromdtype.itemsize
                if isinstance(sub, uproot.interp.numerical.asstlbitset):
                    itemsize = sub.numbytes + 4

                counts = bytestops - bytestarts
                shift = math.log(itemsize, 2)
                if shift == round(shift):
                    self.awkward.numpy.right_shift(counts, int(shift), out=counts)
                else:
                    self.awkward.numpy.floor_divide(counts, itemsize, out=counts)

                offsets = self.awkward.numpy.empty(len(counts) + 1, self.awkward.JaggedArray.INDEXTYPE)
                offsets[0] = 0
                self.awkward.numpy.cumsum(counts, out=offsets[1:])

                return self.awkward.JaggedArray(offsets[:-1], offsets[1:], content)

    def destination(self, numitems, numentries):
        content = self.content.destination(numitems, numentries)
        counts = self.awkward.numpy.empty(numentries, dtype=self.awkward.JaggedArray.INDEXTYPE)
        return _JaggedArrayPrep(counts, content)

    def fill(self, source, destination, itemstart, itemstop, entrystart, entrystop):
        self.content.fill(source.content, destination.content, itemstart, itemstop, entrystart, entrystop)
        destination.counts[entrystart:entrystop] = source.stops - source.starts

    def clip(self, destination, itemstart, itemstop, entrystart, entrystop):
        destination.content = self.content.clip(destination.content, itemstart, itemstop, entrystart, entrystop)
        destination.counts = destination.counts[entrystart:entrystop]
        return destination

    def finalize(self, destination, branch):
        content = self.content.finalize(destination.content, branch)
        leafcount = None
        if len(branch._fLeaves) == 1:
            leafcount = branch._fLeaves[0]._fLeafCount

        out = self.awkward.Methods.maybemixin(type(content), self.awkward.JaggedArray).fromcounts(destination.counts, content)
        out.leafcount = leafcount
        return out
