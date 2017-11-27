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

import re

import numpy

import uproot.const
from uproot.interp.numerical import asdtype
from uproot.interp.numerical import asarray
from uproot.interp.jagged import asjagged
from uproot.interp.jagged import asstlvector
from uproot.interp.strings import asstrings

class _NotNumerical(Exception): pass

def _ftype2dtype(fType):
    if fType == uproot.const.kBool:
        return numpy.dtype(numpy.bool_)
    elif fType == uproot.const.kChar:
        return numpy.dtype("i1")
    elif fType == uproot.const.kUChar:
        return numpy.dtype("u1")
    elif fType == uproot.const.kShort:
        return numpy.dtype(">i2")
    elif fType == uproot.const.kUShort:
        return numpy.dtype(">u2")
    elif fType == uproot.const.kInt:
        return numpy.dtype(">i4")
    elif fType in (uproot.const.kBits, uproot.const.kUInt, uproot.const.kCounter):
        return numpy.dtype(">u4")
    elif fType == uproot.const.kLong:
        return numpy.dtype(numpy.long).newbyteorder(">")
    elif fType == uproot.const.kULong:
        return numpy.dtype(">u" + repr(numpy.dtype(numpy.long).itemsize))
    elif fType == uproot.const.kLong64:
        return numpy.dtype(">i8")
    elif fType == uproot.const.kULong64:
        return numpy.dtype(">u8")
    elif fType in (uproot.const.kFloat, uproot.const.kFloat16):
        return numpy.dtype(">f4")
    elif fType in (uproot.const.kDouble, uproot.const.kDouble32):
        return numpy.dtype(">f8")
    else:
        raise _NotNumerical

def _leaf2dtype(leaf):
    classname = leaf.__class__.__name__
    if classname == "TLeafO":
        return numpy.dtype(numpy.bool)
    elif classname == "TLeafB":
        if leaf.fIsUnsigned:
            return numpy.dtype(numpy.uint8)
        else:
            return numpy.dtype(numpy.int8)
    elif classname == "TLeafS":
        if leaf.fIsUnsigned:
            return numpy.dtype(numpy.uint16)
        else:
            return numpy.dtype(numpy.int16)
    elif classname == "TLeafI":
        if leaf.fIsUnsigned:
            return numpy.dtype(numpy.uint32)
        else:
            return numpy.dtype(numpy.int32)
    elif classname == "TLeafL":
        if leaf.fIsUnsigned:
            return numpy.dtype(numpy.uint64)
        else:
            return numpy.dtype(numpy.int64)
    elif classname == "TLeafF":
        return numpy.dtype(numpy.float32)
    elif classname == "TLeafD":
        return numpy.dtype(numpy.float64)
    elif classname == "TLeafElement":
        return _ftype2dtype(leaf.fType)
    else:
        raise _NotNumerical

def interpret(branch, classes=None, swapbytes=True):
    if classes is None:
        classes = branch._context.classes

    dims = ()
    if len(branch.fLeaves) == 1:
        m = interpret._titlehasdims.match(branch.fLeaves[0].fTitle)
        if m is not None:
            dims = tuple(int(x) for x in re.findall(interpret._itemdimpattern, branch.fLeaves[0].fTitle))
    else:
        for leaf in branch.fLeaves:
            if interpret._titlehasdims.match(leaf.fTitle):
                return None

    try:
        if len(branch.fLeaves) == 1:
            fromdtype = _leaf2dtype(branch.fLeaves[0]).newbyteorder(">")

            if swapbytes:
                out = asdtype(fromdtype, fromdtype.newbyteorder("="), dims, dims)
            else:
                out = asdtype(fromdtype, fromdtype, dims, dims)

            if branch.fLeaves[0].fLeafCount is None:
                return out
            else:
                return asjagged(out)

        else:
            fromdtype = numpy.dtype([(leaf.fName.decode("ascii"), _leaf2dtype(leaf).newbyteorder(">")) for leaf in branch.fLeaves])
            if swapbytes:
                todtype = numpy.dtype([(leaf.fName.decode("ascii"), _leaf2dtype(leaf).newbyteorder("=")) for leaf in branch.fLeaves])
            else:
                todtype = fromdtype

            if all(leaf.fLeafCount is None for leaf in branch.fLeaves):
                return asdtype(fromdtype, todtype, dims, dims)
            else:
                return None

    except _NotNumerical:
        if len(branch.fLeaves) == 1:
            if branch.fLeaves[0].__class__.__name__ == "TLeafC":
                return asstrings

            elif branch.fLeaves[0].__class__.__name__ == "TLeafElement":
                if getattr(branch._streamer, "fSTLtype", None) == uproot.const.kSTLvector:
                    try:
                        fromdtype = _ftype2dtype(branch._streamer.fCtype)
                        if swapbytes:
                            ascontents = asdtype(fromdtype, fromdtype.newbyteorder("="))
                        else:
                            ascontents = asdtype(fromdtype, fromdtype)
                        return asstlvector(ascontents)
                    except _NotNumerical:
                        pass

        return None

interpret._titlehasdims = re.compile(br"^([^\[\]]+)(\[[^\[\]]+\])+")
interpret._itemdimpattern = re.compile(br"\[([1-9][0-9]*)\]")
