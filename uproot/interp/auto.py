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
import ast
from functools import reduce

import numpy

import uproot.const
from uproot.interp.numerical import asdtype
from uproot.interp.numerical import asdouble32
from uproot.interp.numerical import asarray
from uproot.interp.numerical import asstlbitset
from uproot.interp.jagged import asjagged
from uproot.interp.jagged import asstlvector
from uproot.interp.jagged import asstlvectorvector
from uproot.interp.jagged import asobjs
from uproot.interp.jagged import asobj
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
    elif fType == uproot.const.kFloat:
        return numpy.dtype(">f4")
    elif fType == uproot.const.kDouble:
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

def interpret(branch, swapbytes=True):
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
            if isinstance(branch._streamer, uproot.rootio.TStreamerObjectPointer):
                obj = branch._streamer.fTypeName.decode("utf-8")
                if obj.endswith("*"):
                    obj = obj[:-1]
                if obj in branch._context.classes:
                    return asobj(branch._context.classes.get(obj), branch._context)

            if branch.fLeaves[0].__class__.__name__ == "TLeafElement" and branch.fLeaves[0].fType == uproot.const.kDouble32:
                def transform(node, tofloat=True):
                    if isinstance(node, ast.AST):
                        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == "pi":
                            out = ast.Num(3.141592653589793)  # TMath::Pi()
                        elif isinstance(node, ast.Num):
                            out = ast.Num(float(node.n))
                        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                            out = ast.BinOp(transform(node.left), node.op, transform(node.right))
                        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                            out = ast.UnaryOp(node.op, transform(node.operand))
                        elif isinstance(node, ast.List) and isinstance(node.ctx, ast.Load) and len(node.elts) == 2:
                            out = ast.List([transform(node.elts[0]), transform(node.elts[1])], node.ctx)
                        elif isinstance(node, ast.List) and isinstance(node.ctx, ast.Load) and len(node.elts) == 3 and isinstance(node.elts[2], ast.Num):
                            out = ast.List([transform(node.elts[0]), transform(node.elts[1]), node.elts[2]], node.ctx)
                        else:
                            raise Exception(ast.dump(node))
                        out.lineno, out.col_offset = node.lineno, node.col_offset
                        return out
                    else:
                        raise Exception(ast.dump(node))

                try:
                    left, right = branch._streamer.fTitle.index(b"["), branch._streamer.fTitle.index(b"]")
                except (ValueError, AttributeError):
                    out = asdtype(">f4", "f8", dims, dims)
                else:
                    try:
                        spec = eval(compile(ast.Expression(transform(ast.parse(branch._streamer.fTitle[left : right + 1]).body[0].value)), repr(branch._streamer.fTitle), "eval"))
                        if len(spec) == 2:
                            low, high = spec
                            numbits = 32
                        else:
                            low, high, numbits = spec
                        out = asdouble32(low, high, numbits, dims, dims)
                    except:
                        return None
                    
            else:
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
            fromdtype = numpy.dtype([(str(leaf.fName.decode("ascii")), _leaf2dtype(leaf).newbyteorder(">")) for leaf in branch.fLeaves])
            if swapbytes:
                todtype = numpy.dtype([(str(leaf.fName.decode("ascii")), _leaf2dtype(leaf).newbyteorder("=")) for leaf in branch.fLeaves])
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

            if isinstance(branch._streamer, uproot.rootio.TStreamerObject):
                obj = branch._streamer.fTypeName.decode("utf-8")
                if obj in branch._context.classes:
                    return asobj(branch._context.classes.get(obj), branch._context)
                
            if isinstance(branch._streamer, uproot.rootio.TStreamerInfo):
                obj = branch._streamer.fName.decode("utf-8")
                if obj in branch._context.classes:
                    return asobj(branch._context.classes.get(obj), branch._context)

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
                            try:
                                streamerClass = branch._vecstreamer.pyclass
                            except AttributeError:
                                obj = branch._vecstreamer.fName.decode("utf-8")
                                if obj in branch._context.classes:
                                    streamerClass = branch._context.classes.get(obj)
                            return asobjs(streamerClass, branch._context)

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

                if branch.fClassName == b"string":
                    return asstrings()

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
