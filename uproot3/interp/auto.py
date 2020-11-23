#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

from __future__ import absolute_import

import copy
import re
import ast
from functools import reduce

import uproot3.const
import uproot3.rootio
from uproot3.interp.numerical import asdtype
from uproot3.interp.numerical import asarray
from uproot3.interp.numerical import asdouble32
from uproot3.interp.numerical import asfloat16
from uproot3.interp.numerical import asstlbitset
from uproot3.interp.jagged import asjagged
from uproot3.interp.objects import astable
from uproot3.interp.objects import asobj
from uproot3.interp.objects import asgenobj
from uproot3.interp.objects import asstring
from uproot3.interp.objects import SimpleArray
from uproot3.interp.objects import STLVector
from uproot3.interp.objects import STLMap
from uproot3.interp.objects import STLString
from uproot3.interp.objects import Pointer

class _NotNumerical(Exception): pass

def _normalize_ftype(fType):
    if fType is not None and uproot3.const.kOffsetL < fType < uproot3.const.kOffsetP:
        return fType - uproot3.const.kOffsetL
    else:
        return fType

def _ftype2dtype(fType, awkward0):
    fType = _normalize_ftype(fType)
    if fType == uproot3.const.kBool:
        return awkward0.numpy.dtype(awkward0.numpy.bool_)
    elif fType == uproot3.const.kChar:
        return awkward0.numpy.dtype("i1")
    elif fType == uproot3.const.kUChar:
        return awkward0.numpy.dtype("u1")
    elif fType == uproot3.const.kShort:
        return awkward0.numpy.dtype(">i2")
    elif fType == uproot3.const.kUShort:
        return awkward0.numpy.dtype(">u2")
    elif fType == uproot3.const.kInt:
        return awkward0.numpy.dtype(">i4")
    elif fType in (uproot3.const.kBits, uproot3.const.kUInt, uproot3.const.kCounter):
        return awkward0.numpy.dtype(">u4")
    elif fType == uproot3.const.kLong:
        return awkward0.numpy.dtype(">i8")
    elif fType == uproot3.const.kULong:
        return awkward0.numpy.dtype(">u8")
    elif fType == uproot3.const.kLong64:
        return awkward0.numpy.dtype(">i8")
    elif fType == uproot3.const.kULong64:
        return awkward0.numpy.dtype(">u8")
    elif fType == uproot3.const.kFloat:
        return awkward0.numpy.dtype(">f4")
    elif fType == uproot3.const.kDouble:
        return awkward0.numpy.dtype(">f8")
    else:
        raise _NotNumerical

def _leaf2dtype(leaf, awkward0):
    classname = leaf.__class__.__name__
    if classname == "TLeafO":
        return awkward0.numpy.dtype(awkward0.numpy.bool_)
    elif classname == "TLeafB":
        if leaf._fIsUnsigned:
            return awkward0.numpy.dtype(awkward0.numpy.uint8)
        else:
            return awkward0.numpy.dtype(awkward0.numpy.int8)
    elif classname == "TLeafS":
        if leaf._fIsUnsigned:
            return awkward0.numpy.dtype(awkward0.numpy.uint16)
        else:
            return awkward0.numpy.dtype(awkward0.numpy.int16)
    elif classname == "TLeafI":
        if leaf._fIsUnsigned:
            return awkward0.numpy.dtype(awkward0.numpy.uint32)
        else:
            return awkward0.numpy.dtype(awkward0.numpy.int32)
    elif classname == "TLeafL":
        if leaf._fIsUnsigned:
            return awkward0.numpy.dtype(awkward0.numpy.uint64)
        else:
            return awkward0.numpy.dtype(awkward0.numpy.int64)
    elif classname == "TLeafF":
        return awkward0.numpy.dtype(awkward0.numpy.float32)
    elif classname == "TLeafD":
        return awkward0.numpy.dtype(awkward0.numpy.float64)
    elif classname == "TLeafElement":
        return _ftype2dtype(leaf._fType, awkward0)
    else:
        raise _NotNumerical

def _obj_or_genobj(streamerClass, branch, isjagged, cntvers=False, tobject=True, speedbump=True):
    if len(branch._fBranches) != 0:
        return None

    try:
        recarray = streamerClass._recarray_dtype(cntvers=cntvers, tobject=tobject)

    except (AttributeError, ValueError):
        if not speedbump:
            context = copy.copy(branch._context)
            context.speedbump = False
        else:
            context = branch._context

        if isjagged:
            return asgenobj(SimpleArray(streamerClass), context, 0)
        else:
            return asgenobj(streamerClass, context, 0)

    else:
        if isjagged:
            if streamerClass._methods is None:
                return asjagged(astable(asdtype(recarray)))
            else:
                return asjagged(asobj(astable(asdtype(recarray)), streamerClass._methods))
        else:
            if streamerClass._methods is None:
                return asdtype(recarray)
            else:
                return asobj(astable(asdtype(recarray)), streamerClass._methods)

def interpret(branch, awkwardlib=None, swapbytes=True, cntvers=False, tobject=True, speedbump=True):
    import uproot3.tree
    awkward0 = uproot3.tree._normalize_awkwardlib(awkwardlib)

    dims, isjagged = (), False
    if len(branch._fLeaves) == 1:
        m = interpret._titlehasdims.match(branch._fLeaves[0]._fTitle)
        if m is not None:
            dims = tuple(int(x) for x in re.findall(interpret._itemdimpattern, branch._fLeaves[0]._fTitle))
            if dims == ():
                dims = (branch._fLeaves[0]._fLen, ) if branch._fLeaves[0]._fLen > 1 else ()
            if any(interpret._itemdimpattern.match(x) is None for x in re.findall(interpret._itemanypattern, branch._fLeaves[0]._fTitle)):
                isjagged = True
    else:
        for leaf in branch._fLeaves:
            if interpret._titlehasdims.match(leaf._fTitle):
                return None

    try:
        if len(branch._fLeaves) == 1:
            if isinstance(branch._streamer, uproot3.rootio.TStreamerObjectPointer):
                obj = branch._streamer._fTypeName
                if obj.endswith(b"*"):
                    obj = obj[:-1]
                obj = uproot3.rootio._safename(obj)
                if obj in branch._context.classes:
                    return _obj_or_genobj(branch._context.classes.get(obj), branch, isjagged, cntvers=cntvers, tobject=tobject, speedbump=speedbump)

            # Process Double32_t and Float16_t types possibly packed in TLeafElement
            leaftype = uproot3.const.kBase
            if branch._fLeaves[0].__class__.__name__ == "TLeafElement":
                leaftype = _normalize_ftype(branch._fLeaves[0]._fType)

            iskDouble32 = leaftype == uproot3.const.kDouble32
            iskFloat16  = leaftype == uproot3.const.kFloat16

            if iskDouble32 or iskFloat16:
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
                    left, right = branch._streamer._fTitle.index(b"["), branch._streamer._fTitle.index(b"]")
                except (ValueError, AttributeError):
                    low, high, numbits = 0, 0, 0
                else:
                    try:
                        spec = eval(compile(ast.Expression(transform(ast.parse(branch._streamer._fTitle[left : right + 1]).body[0].value)), repr(branch._streamer._fTitle), "eval"))
                        if len(spec) == 2:
                            low, high = spec
                            numbits = None
                        else:
                            low, high, numbits = spec
                    except Exception:
                        return None

                if iskDouble32 and numbits == 0:
                    out = asdtype(awkward0.numpy.dtype((">f4", dims)), awkward0.numpy.dtype(("f8", dims)))
                elif iskDouble32 and numbits is None:
                    out = asdouble32(low, high, 32, dims)
                elif iskDouble32:
                    out = asdouble32(low, high, numbits, dims)
                elif iskFloat16 and numbits == 0:
                    out = asfloat16(low, high, 12, dims)
                elif iskFloat16 and numbits is None:
                    out = asfloat16(low, high, 32, dims)
                elif iskFloat16:
                    out = asfloat16(low, high, numbits, dims)
                else:
                    return None

            else:
                fromdtype = _leaf2dtype(branch._fLeaves[0], awkward0).newbyteorder(">")

                if swapbytes:
                    out = asdtype(awkward0.numpy.dtype((fromdtype, dims)), awkward0.numpy.dtype((fromdtype.newbyteorder("="), dims)))
                else:
                    out = asdtype(awkward0.numpy.dtype((fromdtype, dims)), awkward0.numpy.dtype((fromdtype, dims)))

            if branch._fLeaves[0]._fLeafCount is None:
                return out
            else:
                return asjagged(out)

        elif len(branch._fLeaves) > 1:
            fromdtype = awkward0.numpy.dtype([(str(leaf._fName.decode("ascii")), _leaf2dtype(leaf, awkward0).newbyteorder(">")) for leaf in branch._fLeaves])
            if swapbytes:
                todtype = awkward0.numpy.dtype([(str(leaf._fName.decode("ascii")), _leaf2dtype(leaf, awkward0).newbyteorder("=")) for leaf in branch._fLeaves])
            else:
                todtype = fromdtype

            if all(leaf._fLeafCount is None for leaf in branch._fLeaves):
                return asdtype(awkward0.numpy.dtype((fromdtype, dims)), awkward0.numpy.dtype((todtype, dims)))
            else:
                return None

    except _NotNumerical:
        if len(branch._fLeaves) == 1:
            if len(branch._fBranches) > 0 and all(len(x._fLeaves) == 1 and x._fLeaves[0]._fLeafCount is branch._fLeaves[0] for x in branch._fBranches):
                return asdtype(">i4")

            if isinstance(branch._streamer, uproot3.rootio.TStreamerObject):
                obj = uproot3.rootio._safename(branch._streamer._fTypeName)
                if obj == "string":
                    return asgenobj(STLString(awkward0), branch._context, 0)
                elif obj in branch._context.classes:
                    return _obj_or_genobj(branch._context.classes.get(obj), branch, isjagged, cntvers=cntvers, tobject=tobject, speedbump=speedbump)

            if isinstance(branch._streamer, uproot3.rootio.TStreamerInfo):
                obj = uproot3.rootio._safename(branch._streamer._fName)
                if obj == "string":
                    return asgenobj(STLString(awkward0), branch._context, 0)
                elif obj in branch._context.classes:
                    return _obj_or_genobj(branch._context.classes.get(obj), branch, isjagged, cntvers=cntvers, tobject=tobject, speedbump=speedbump)

            if branch._fLeaves[0].__class__.__name__ == "TLeafC":
                return asstring(skipbytes=1)

            elif branch._fLeaves[0].__class__.__name__ == "TLeafElement":
                if isinstance(branch._streamer, uproot3.rootio.TStreamerBasicType):
                    try:
                        fromdtype = _ftype2dtype(branch._streamer._fType, awkward0)
                    except _NotNumerical:
                        pass
                    else:
                        if swapbytes:
                            todtype = fromdtype.newbyteorder("=")
                        else:
                            todtype = fromdtype
                        fromdims, remainder = divmod(branch._streamer._fSize, fromdtype.itemsize)
                        if remainder == 0:
                            todims = dims
                            if reduce(lambda x, y: x * y, todims, 1) != fromdims:
                                todims = (fromdims,)
                            return asdtype(awkward0.numpy.dtype((fromdtype, (fromdims,))), awkward0.numpy.dtype((todtype, todims)))

                if isinstance(branch._streamer, uproot3.rootio.TStreamerBasicPointer):
                    if uproot3.const.kOffsetP < branch._streamer._fType < uproot3.const.kOffsetP + 20:
                        try:
                            fromdtype = _ftype2dtype(branch._streamer._fType - uproot3.const.kOffsetP, awkward0)
                        except _NotNumerical:
                            pass
                        else:
                            if swapbytes:
                                todtype = fromdtype.newbyteorder("=")
                            else:
                                todtype = fromdtype
                            if len(branch._fLeaves) == 1 and branch._fLeaves[0]._fLeafCount is not None:
                                return asjagged(asdtype(fromdtype, todtype), skipbytes=1)

                if isinstance(branch._streamer, uproot3.rootio.TStreamerObjectAny):
                    if getattr(branch._streamer, "_fTypeName", None) in (b"TArrayC", b"TArrayS", b"TArrayI", b"TArrayL", b"TArrayL64", b"TArrayF", b"TArrayD"):
                        return asjagged(asdtype(getattr(uproot3.rootio, branch._streamer._fTypeName.decode("ascii"))._dtype), skipbytes=4)

                if isinstance(branch._streamer, uproot3.rootio.TStreamerString):
                    return asstring(skipbytes=1)

                if isinstance(branch._streamer, uproot3.rootio.TStreamerSTLstring):
                    if branch._isTClonesArray:
                        return asgenobj(STLVector(STLString()), branch._context, 6)
                    else:
                        return asstring(skipbytes=7)

                if getattr(branch._streamer, "_fType", None) == uproot3.const.kCharStar:
                    return asstring(skipbytes=4)

                if getattr(branch._streamer, "_fSTLtype", None) == uproot3.const.kSTLvector:
                    try:
                        fromdtype = _ftype2dtype(branch._streamer._fCtype, awkward0)
                        if swapbytes:
                            ascontent = asdtype(fromdtype, fromdtype.newbyteorder("="))
                        else:
                            ascontent = asdtype(fromdtype, fromdtype)
                        if branch._isTClonesArray:
                            return asgenobj(SimpleArray(STLVector(asdtype(fromdtype, fromdtype))), branch._context, 6)
                        else:
                            return asjagged(ascontent, skipbytes=10)

                    except _NotNumerical:
                        if branch._vecstreamer is not None:
                            try:
                                streamerClass = branch._vecstreamer.pyclass
                            except AttributeError:
                                obj = uproot3.rootio._safename(branch._vecstreamer._fName)
                                if obj in branch._context.classes:
                                    streamerClass = branch._context.classes.get(obj)
                            if getattr(streamerClass, "_hasreadobjany", False):
                                return None

                            if streamerClass.__name__ == "string":
                                return asgenobj(STLVector(STLString(awkward0)), branch._context, 6)

                            if len(branch._fBranches) != 0:
                                return None

                            try:
                                recarray = streamerClass._recarray_dtype(cntvers=cntvers, tobject=tobject)
                            except (AttributeError, ValueError):
                                return asgenobj(STLVector(streamerClass), branch._context, 6)
                            else:
                                if streamerClass._methods is None:
                                    return asjagged(astable(asdtype(recarray)), skipbytes=10)
                                else:
                                    return asjagged(asobj(astable(asdtype(recarray)), streamerClass._methods), skipbytes=10)

                if hasattr(branch._streamer, "_fTypeName"):
                    m = re.match(b"bitset<([1-9][0-9]*)>", branch._streamer._fTypeName)
                    if m is not None:
                        return asjagged(asstlbitset(int(m.group(1))), skipbytes=6)

                if getattr(branch._streamer, "_fTypeName", None) == b"vector<bool>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Bool_t>":
                    return asjagged(asdtype(awkward0.numpy.bool_), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<char>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Char_t>":
                    return asjagged(asdtype("i1"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned char>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<UChar_t>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Byte_t>":
                    return asjagged(asdtype("u1"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<short>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Short_t>":
                    return asjagged(asdtype("i2"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned short>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<UShort_t>":
                    return asjagged(asdtype("u2"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<int>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Int_t>":
                    return asjagged(asdtype("i4"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned int>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<UInt_t>":
                    return asjagged(asdtype("u4"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<long>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Long_t>":
                    return asjagged(asdtype("i8"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned long>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<ULong_t>":
                    return asjagged(asdtype("u8"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<long long>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Long64_t>":
                    return asjagged(asdtype("i8"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned long long>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<ULong64_t>":
                    return asjagged(asdtype("u8"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<float>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Float_t>":
                    return asjagged(asdtype("f4"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<double>" or getattr(branch._streamer, "_fTypeName", None) == b"vector<Double_t>":
                    return asjagged(asdtype("f8"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<string>":
                    return asgenobj(STLVector(STLString(awkward0)), branch._context, 6)
                else:
                    m = interpret._vectorpointer.match(getattr(branch._streamer, "_fTypeName", b""))
                    if m is not None and m.group(1) in branch._context.streamerinfosmap:
                        streamer = branch._context.streamerinfosmap[m.group(1)]
                        return asgenobj(STLVector(Pointer(streamer.pyclass)), branch._context, skipbytes=6)

                if getattr(branch._streamer, "_fTypeName", None) == b"map<string,bool>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Bool_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype(awkward0.numpy.bool_)), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,char>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Char_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i1")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned char>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,UChar_t>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Byte_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u1")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,short>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Short_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i2")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned short>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,UShort_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u2")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,int>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Int_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i4")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned int>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,UInt_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u4")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,long>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Long_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i8")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned long>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,ULong_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u8")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,long long>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Long64_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i8")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned long long>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,ULong64_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u8")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,float>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Float_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("f4")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,double>" or getattr(branch._streamer, "_fTypeName", None) == b"map<string,Double_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("f8")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,string>":
                    return asgenobj(STLMap(STLString(awkward0), STLString(awkward0)), branch._context, 6)

                if getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<bool> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Bool_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(awkward0.numpy.bool_))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<char> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Char_t> >":
                    return asgenobj(STLVector(STLVector(asdtype("i1"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned char> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<UChar_t> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Byte_t> >":
                    return asgenobj(STLVector(STLVector(asdtype("u1"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<short> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Short_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i2"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned short> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<UShort_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u2"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<int> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Int_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i4"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned int> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<UInt_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u4"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<long> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Long_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i8"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned long> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<ULong_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u8"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<long long> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Long64_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i8"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned long long> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<ULong64_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u8"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<float> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Float_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">f4"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<double> >" or getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<Double_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">f8"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<string> >":
                    return asgenobj(STLVector(STLVector(STLString(awkward0))), branch._context, 6)

                m = re.match(b"bitset<([1-9][0-9]*)>", branch._fClassName)
                if m is not None:
                    return asstlbitset(int(m.group(1)))

                if branch._fClassName == b"string":
                    return asstring(skipbytes=1)

                if branch._fClassName == b"vector<bool>" or branch._fClassName == b"vector<Bool_t>":
                    return asjagged(asdtype(awkward0.numpy.bool_), skipbytes=10)
                elif branch._fClassName == b"vector<char>" or branch._fClassName == b"vector<Char_t>":
                    return asjagged(asdtype("i1"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned char>" or branch._fClassName == b"vector<UChar_t>" or branch._fClassName == b"vector<Byte_t>":
                    return asjagged(asdtype("u1"), skipbytes=10)
                elif branch._fClassName == b"vector<short>" or branch._fClassName == b"vector<Short_t>":
                    return asjagged(asdtype("i2"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned short>" or branch._fClassName == b"vector<UShort_t>":
                    return asjagged(asdtype("u2"), skipbytes=10)
                elif branch._fClassName == b"vector<int>" or branch._fClassName == b"vector<Int_t>":
                    return asjagged(asdtype("i4"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned int>" or branch._fClassName == b"vector<UInt_t>":
                    return asjagged(asdtype("u4"), skipbytes=10)
                elif branch._fClassName == b"vector<long>" or branch._fClassName == b"vector<Long_t>":
                    return asjagged(asdtype("i8"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned long>" or branch._fClassName == b"vector<ULong_t>":
                    return asjagged(asdtype("u8"), skipbytes=10)
                elif branch._fClassName == b"vector<long long>" or branch._fClassName == b"vector<Long64_t>":
                    return asjagged(asdtype("i8"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned long long>" or branch._fClassName == b"vector<ULong64_t>":
                    return asjagged(asdtype("u8"), skipbytes=10)
                elif branch._fClassName == b"vector<float>" or branch._fClassName == b"vector<Float_t>":
                    return asjagged(asdtype("f4"), skipbytes=10)
                elif branch._fClassName == b"vector<double>" or branch._fClassName == b"vector<Double_t>":
                    return asjagged(asdtype("f8"), skipbytes=10)
                elif branch._fClassName == b"vector<string>":
                    return asgenobj(STLVector(STLString(awkward0)), branch._context, 6)

                if branch._fClassName == b"vector<vector<bool> >" or branch._fClassName == b"vector<vector<Bool_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(awkward0.numpy.bool_))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<char> >" or branch._fClassName == b"vector<vector<Char_t> >":
                    return asgenobj(STLVector(STLVector(asdtype("i1"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned char> >" or branch._fClassName == b"vector<vector<UChar_t> >" or branch._fClassName == b"vector<vector<Byte_t> >":
                    return asgenobj(STLVector(STLVector(asdtype("u1"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<short> >" or branch._fClassName == b"vector<vector<Short_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i2"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned short> >" or branch._fClassName == b"vector<vector<UShort_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u2"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<int> >" or branch._fClassName == b"vector<vector<Int_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i4"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned int> >" or branch._fClassName == b"vector<vector<UInt_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u4"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<long> >" or branch._fClassName == b"vector<vector<Long_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i8"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned long> >" or branch._fClassName == b"vector<vector<ULong_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u8"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<long long> >" or branch._fClassName == b"vector<vector<Long64_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i8"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned long long> >" or branch._fClassName == b"vector<vector<ULong64_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u8"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<float> >" or branch._fClassName == b"vector<vector<Float_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">f4"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<double> >" or branch._fClassName == b"vector<vector<Double_t> >":
                    return asgenobj(STLVector(STLVector(asdtype(">f8"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<string> >":
                    return asgenobj(STLVector(STLVector(STLString(awkward0))), branch._context, 6)

                if branch._fClassName == b"map<string,bool>" or branch._fClassName == b"map<string,Bool_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype(awkward0.numpy.bool_)), branch._context, 6)
                elif branch._fClassName == b"map<string,char>" or branch._fClassName == b"map<string,Char_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i1")), branch._context, 6)
                elif branch._fClassName == b"map<string,unsigned char>" or branch._fClassName == b"map<string,UChar_t>" or branch._fClassName == b"map<string,Byte_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u1")), branch._context, 6)
                elif branch._fClassName == b"map<string,short>" or branch._fClassName == b"map<string,Short_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i2")), branch._context, 6)
                elif branch._fClassName == b"map<string,unsigned short>" or branch._fClassName == b"map<string,UShort_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u2")), branch._context, 6)
                elif branch._fClassName == b"map<string,int>" or branch._fClassName == b"map<string,Int_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i4")), branch._context, 6)
                elif branch._fClassName == b"map<string,unsigned int>" or branch._fClassName == b"map<string,UInt_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u4")), branch._context, 6)
                elif branch._fClassName == b"map<string,long>" or branch._fClassName == b"map<string,Long_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i8")), branch._context, 6)
                elif branch._fClassName == b"map<string,unsigned long>" or branch._fClassName == b"map<string,ULong_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u8")), branch._context, 6)
                elif branch._fClassName == b"map<string,long long>" or branch._fClassName == b"map<string,Long64_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("i8")), branch._context, 6)
                elif branch._fClassName == b"map<string,unsigned long long>" or branch._fClassName == b"map<string,ULong64_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("u8")), branch._context, 6)
                elif branch._fClassName == b"map<string,float>" or branch._fClassName == b"map<string,Float_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("f4")), branch._context, 6)
                elif branch._fClassName == b"map<string,double>" or branch._fClassName == b"map<string,Double_t>":
                    return asgenobj(STLMap(STLString(awkward0), asdtype("f8")), branch._context, 6)
                elif branch._fClassName == b"map<string,string>":
                    return asgenobj(STLMap(STLString(awkward0), STLString(awkward0)), branch._context, 6)

                if branch.name.endswith(b".first") and branch._fClassName.startswith(b"pair<string,"):
                    return asgenobj(SimpleArray(STLString(awkward0)), branch._context, 6)

                if branch.name.endswith(b".second"):
                    m = interpret._pairsecond.match(branch._fClassName)
                    if m is not None:
                        t, = m.groups()
                        if t == b"vector<bool>" or t == b"vector<Bool_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype(awkward0.numpy.bool_))), branch._context, 6)
                        elif t == b"vector<char>" or t == b"vector<Char_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("i1"))), branch._context, 6)
                        elif t == b"vector<unsigned char>" or t == b"vector<UChar_t>" or t == b"vector<Byte_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("u1"))), branch._context, 6)
                        elif t == b"vector<short>" or t == b"vector<Short_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("i2"))), branch._context, 6)
                        elif t == b"vector<unsigned short>" or t == b"vector<UShort_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("u2"))), branch._context, 6)
                        elif t == b"vector<int>" or t == b"vector<Int_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("i4"))), branch._context, 6)
                        elif t == b"vector<unsigned int>" or t == b"vector<UInt_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("u4"))), branch._context, 6)
                        elif t == b"vector<long>" or t == b"vector<Long_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("i8"))), branch._context, 6)
                        elif t == b"vector<unsigned long>" or t == b"vector<ULong_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("u8"))), branch._context, 6)
                        elif t == b"vector<long long>" or t == b"vector<Long64_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("i8"))), branch._context, 6)
                        elif t == b"vector<unsigned long long>" or t == b"vector<ULong64_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("u8"))), branch._context, 6)
                        elif t == b"vector<float>" or t == b"vector<Float_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("f4"))), branch._context, 6)
                        elif t == b"vector<double>" or t == b"vector<Double_t>":
                            return asgenobj(SimpleArray(STLVector(asdtype("f8"))), branch._context, 6)
                        elif t == b"vector<string>":
                            return asgenobj(SimpleArray(STLVector(STLString(awkward0))), branch._context, 6)

        return None

interpret._titlehasdims = re.compile(br"^([^\[\]]+)(\[[^\[\]]+\])+")
interpret._itemdimpattern = re.compile(br"\[([1-9][0-9]*)\]")
interpret._itemanypattern = re.compile(br"\[(.*)\]")
interpret._vectorpointer = re.compile(br"vector\<([^<>]*)\*\>")
interpret._pairsecond = re.compile(br"pair\<[^<>]*,(.*) \>")

streamer_aliases = [
    (re.compile(b'(ROOT::Math::(?:PositionVector3D|DisplacementVector3D)<ROOT::Math::Cartesian3D<(?:[^>,]+)>)\\s+(>)'),
        b'\\1,ROOT::Math::DefaultCoordinateSystemTag\\2'),
]
