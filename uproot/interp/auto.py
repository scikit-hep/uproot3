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
from functools import reduce

import numpy

import uproot.const
from uproot.interp.numerical import asdtype
from uproot.interp.numerical import asarray
from uproot.interp.numerical import asstlbitset
from uproot.interp.jagged import asjagged
from uproot.interp.jagged import asstlvector
from uproot.interp.jagged import asstlvectorvector
from uproot.interp.jagged import asjaggedobjects
from uproot.interp.strings import asstrings
from uproot.interp.strings import asstlvecstrings

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
        return numpy.dtype(numpy.bool_)
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

        elif len(branch.fLeaves) > 1:
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
            if len(branch.fBranches) > 0 and all(len(x.fLeaves) == 1 and x.fLeaves[0].fLeafCount is branch.fLeaves[0] for x in branch.fBranches):
                return asdtype(">i4")

            if branch.fLeaves[0].__class__.__name__ == "TLeafC":
                return asstrings(skip_bytes=1, skip4_if_255=True)

            elif branch.fLeaves[0].__class__.__name__ == "TLeafElement":
                if isinstance(branch._streamer, uproot.rootio.TStreamerBasicType):
                    try:
                        fromdtype = _ftype2dtype(branch._streamer.fType)
                    except _NotNumerical:
                        pass
                    else:
                        if swapbytes:
                            todtype = fromdtype.newbyteorder("=")
                        else:
                            todtype = fromdtype
                        fromdims, remainder = divmod(branch._streamer.fSize, fromdtype.itemsize)
                        if remainder == 0:
                            todims = dims
                            if reduce(lambda x, y: x * y, todims, 1) != fromdims:
                                todims = (fromdims,)
                            return asdtype(fromdtype, todtype, (fromdims,), todims)

                if isinstance(branch._streamer, uproot.rootio.TStreamerBasicPointer):
                    if uproot.const.kOffsetP < branch._streamer.fType < uproot.const.kOffsetP + 20:
                        try:
                            fromdtype = _ftype2dtype(branch._streamer.fType - uproot.const.kOffsetP)
                        except _NotNumerical:
                            pass
                        else:
                            if swapbytes:
                                todtype = fromdtype.newbyteorder("=")
                            else:
                                todtype = fromdtype
                            if len(branch.fLeaves) == 1 and branch.fLeaves[0].fLeafCount is not None:
                                return asjagged(asdtype(fromdtype, todtype), skip_bytes=1)
                            
                if isinstance(branch._streamer, uproot.rootio.TStreamerString):
                    return asstrings(skip_bytes=1, skip4_if_255=True)

                if isinstance(branch._streamer, uproot.rootio.TStreamerSTLstring):
                    return asstrings(skip_bytes=7, skip4_if_255=True)   # FIXME: not sure about skip4_if_255

                if getattr(branch._streamer, "fType", None) == uproot.const.kCharStar:
                    return asstrings(skip_bytes=4, skip4_if_255=False)

                if getattr(branch._streamer, "fSTLtype", None) == uproot.const.kSTLvector:
                    try:
                        fromdtype = _ftype2dtype(branch._streamer.fCtype)
                        if swapbytes:
                            ascontent = asdtype(fromdtype, fromdtype.newbyteorder("="))
                        else:
                            ascontent = asdtype(fromdtype, fromdtype)
                        return asstlvector(ascontent)

                    except _NotNumerical:
                        if branch._vecstreamer is not None:
                            return asjaggedobjects(branch._vecstreamer.pyclass, branch._context)

                if hasattr(branch._streamer, "fTypeName"):
                    m = re.match(b"bitset<([1-9][0-9]*)>", branch._streamer.fTypeName)
                    if m is not None:
                        return asstlbitset(int(m.group(1)))

                if getattr(branch._streamer, "fTypeName", None) == b"vector<bool>":
                    return asstlvector(asdtype(numpy.bool_))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<char>":
                    return asstlvector(asdtype("i1"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<unsigned char>":
                    return asstlvector(asdtype("u1"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<short>":
                    return asstlvector(asdtype("i2"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<unsigned short>":
                    return asstlvector(asdtype("u2"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<int>":
                    return asstlvector(asdtype("i4"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<unsigned int>":
                    return asstlvector(asdtype("u4"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<long>":
                    return asstlvector(asdtype("i8"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<unsigned long>":
                    return asstlvector(asdtype("u8"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<float>":
                    return asstlvector(asdtype("f4"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<double>":
                    return asstlvector(asdtype("f8"))
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<string>":
                    return asstlvecstrings()

                if getattr(branch._streamer, "fTypeName", None) == b"vector<vector<bool> >":
                    return asstlvectorvector(numpy.bool_)
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<char> >":
                    return asstlvectorvector("i1")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<unsigned char> >":
                    return asstlvectorvector("u1")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<short> >":
                    return asstlvectorvector(">i2")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<unsigned short> >":
                    return asstlvectorvector(">u2")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<int> >":
                    return asstlvectorvector(">i4")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<unsigned int> >":
                    return asstlvectorvector(">u4")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<long> >":
                    return asstlvectorvector(">i8")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<unsigned long> >":
                    return asstlvectorvector(">u8")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<float> >":
                    return asstlvectorvector(">f4")
                elif getattr(branch._streamer, "fTypeName", None) == b"vector<vector<double> >":
                    return asstlvectorvector(">f8")

                m = re.match(b"bitset<([1-9][0-9]*)>", branch.fClassName)
                if m is not None:
                    return asstlbitset(int(m.group(1)))

                if branch.fClassName == b"vector<bool>":
                    return asstlvector(asdtype(numpy.bool_))
                elif branch.fClassName == b"vector<char>":
                    return asstlvector(asdtype("i1"))
                elif branch.fClassName == b"vector<unsigned char>":
                    return asstlvector(asdtype("u1"))
                elif branch.fClassName == b"vector<short>":
                    return asstlvector(asdtype("i2"))
                elif branch.fClassName == b"vector<unsigned short>":
                    return asstlvector(asdtype("u2"))
                elif branch.fClassName == b"vector<int>":
                    return asstlvector(asdtype("i4"))
                elif branch.fClassName == b"vector<unsigned int>":
                    return asstlvector(asdtype("u4"))
                elif branch.fClassName == b"vector<long>":
                    return asstlvector(asdtype("i8"))
                elif branch.fClassName == b"vector<unsigned long>":
                    return asstlvector(asdtype("u8"))
                elif branch.fClassName == b"vector<float>":
                    return asstlvector(asdtype("f4"))
                elif branch.fClassName == b"vector<double>":
                    return asstlvector(asdtype("f8"))
                elif branch.fClassName == b"vector<string>":
                    return asstlvecstrings()

                if branch.fClassName == b"vector<vector<bool> >":
                    return asstlvectorvector(numpy.bool_)
                elif branch.fClassName == b"vector<vector<char> >":
                    return asstlvectorvector("i1")
                elif branch.fClassName == b"vector<vector<unsigned char> >":
                    return asstlvectorvector("u1")
                elif branch.fClassName == b"vector<vector<short> >":
                    return asstlvectorvector(">i2")
                elif branch.fClassName == b"vector<vector<unsigned short> >":
                    return asstlvectorvector(">u2")
                elif branch.fClassName == b"vector<vector<int> >":
                    return asstlvectorvector(">i4")
                elif branch.fClassName == b"vector<vector<unsigned int> >":
                    return asstlvectorvector(">u4")
                elif branch.fClassName == b"vector<vector<long> >":
                    return asstlvectorvector(">i8")
                elif branch.fClassName == b"vector<vector<unsigned long> >":
                    return asstlvectorvector(">u8")
                elif branch.fClassName == b"vector<vector<float> >":
                    return asstlvectorvector(">f4")
                elif branch.fClassName == b"vector<vector<double> >":
                    return asstlvectorvector(">f8")

        return None

interpret._titlehasdims = re.compile(br"^([^\[\]]+)(\[[^\[\]]+\])+")
interpret._itemdimpattern = re.compile(br"\[([1-9][0-9]*)\]")
