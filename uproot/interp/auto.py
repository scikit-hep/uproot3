#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import copy
import re
import ast
from functools import reduce

import uproot.const
import uproot.rootio
from uproot.interp.numerical import asdtype
from uproot.interp.numerical import asarray
from uproot.interp.numerical import asdouble32
from uproot.interp.numerical import asfloat16
from uproot.interp.numerical import asstlbitset
from uproot.interp.jagged import asjagged
from uproot.interp.objects import astable
from uproot.interp.objects import asobj
from uproot.interp.objects import asgenobj
from uproot.interp.objects import asstring
from uproot.interp.objects import SimpleArray
from uproot.interp.objects import STLVector
from uproot.interp.objects import STLMap
from uproot.interp.objects import STLString

class _NotNumerical(Exception): pass

def _normalize_ftype(fType):
    if fType is not None and uproot.const.kOffsetL < fType < uproot.const.kOffsetP:
        return fType - uproot.const.kOffsetL
    else:
        return fType

def _ftype2dtype(fType, awkward):
    fType = _normalize_ftype(fType)
    if fType == uproot.const.kBool:
        return awkward.numpy.dtype(awkward.numpy.bool_)
    elif fType == uproot.const.kChar:
        return awkward.numpy.dtype("i1")
    elif fType == uproot.const.kUChar:
        return awkward.numpy.dtype("u1")
    elif fType == uproot.const.kShort:
        return awkward.numpy.dtype(">i2")
    elif fType == uproot.const.kUShort:
        return awkward.numpy.dtype(">u2")
    elif fType == uproot.const.kInt:
        return awkward.numpy.dtype(">i4")
    elif fType in (uproot.const.kBits, uproot.const.kUInt, uproot.const.kCounter):
        return awkward.numpy.dtype(">u4")
    elif fType == uproot.const.kLong:
        return awkward.numpy.dtype(awkward.numpy.long).newbyteorder(">")
    elif fType == uproot.const.kULong:
        return awkward.numpy.dtype(">u" + repr(awkward.numpy.dtype(awkward.numpy.long).itemsize))
    elif fType == uproot.const.kLong64:
        return awkward.numpy.dtype(">i8")
    elif fType == uproot.const.kULong64:
        return awkward.numpy.dtype(">u8")
    elif fType == uproot.const.kFloat:
        return awkward.numpy.dtype(">f4")
    elif fType == uproot.const.kDouble:
        return awkward.numpy.dtype(">f8")
    else:
        raise _NotNumerical

def _leaf2dtype(leaf, awkward):
    classname = leaf.__class__.__name__
    if classname == "TLeafO":
        return awkward.numpy.dtype(awkward.numpy.bool_)
    elif classname == "TLeafB":
        if leaf._fIsUnsigned:
            return awkward.numpy.dtype(awkward.numpy.uint8)
        else:
            return awkward.numpy.dtype(awkward.numpy.int8)
    elif classname == "TLeafS":
        if leaf._fIsUnsigned:
            return awkward.numpy.dtype(awkward.numpy.uint16)
        else:
            return awkward.numpy.dtype(awkward.numpy.int16)
    elif classname == "TLeafI":
        if leaf._fIsUnsigned:
            return awkward.numpy.dtype(awkward.numpy.uint32)
        else:
            return awkward.numpy.dtype(awkward.numpy.int32)
    elif classname == "TLeafL":
        if leaf._fIsUnsigned:
            return awkward.numpy.dtype(awkward.numpy.uint64)
        else:
            return awkward.numpy.dtype(awkward.numpy.int64)
    elif classname == "TLeafF":
        return awkward.numpy.dtype(awkward.numpy.float32)
    elif classname == "TLeafD":
        return awkward.numpy.dtype(awkward.numpy.float64)
    elif classname == "TLeafElement":
        return _ftype2dtype(leaf._fType, awkward)
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
        if streamerClass._methods is None:
            return astable(asdtype(recarray))
        else:
            if isjagged:
                if streamerClass._methods is None:
                    return asjagged(astable(asdtype(recarray)))
                else:
                    return asjagged(asobj(astable(asdtype(recarray)), streamerClass._methods))
            else:
                if streamerClass._methods is None:
                    return astable(asdtype(recarray))
                else:
                    return asobj(astable(asdtype(recarray)), streamerClass._methods)

def interpret(branch, awkwardlib=None, swapbytes=True, cntvers=False, tobject=True, speedbump=True):
    import uproot.tree
    awkward = uproot.tree._normalize_awkwardlib(awkwardlib)

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
            if isinstance(branch._streamer, uproot.rootio.TStreamerObjectPointer):
                obj = branch._streamer._fTypeName
                if obj.endswith(b"*"):
                    obj = obj[:-1]
                obj = uproot.rootio._safename(obj)
                if obj in branch._context.classes:
                    return _obj_or_genobj(branch._context.classes.get(obj), branch, isjagged, cntvers=cntvers, tobject=tobject, speedbump=speedbump)

            # Process Double32_t and Float16_t types possibly packed in TLeafElement
            leaftype = uproot.const.kBase
            if branch._fLeaves[0].__class__.__name__ == "TLeafElement":
                leaftype = _normalize_ftype(branch._fLeaves[0]._fType)

            iskDouble32 = leaftype == uproot.const.kDouble32
            iskFloat16  = leaftype == uproot.const.kFloat16

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
                    except:
                        return None

                if iskDouble32 and numbits == 0:
                    out = asdtype(awkward.numpy.dtype((">f4", dims)), awkward.numpy.dtype(("f8", dims)))
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
                fromdtype = _leaf2dtype(branch._fLeaves[0], awkward).newbyteorder(">")

                if swapbytes:
                    out = asdtype(awkward.numpy.dtype((fromdtype, dims)), awkward.numpy.dtype((fromdtype.newbyteorder("="), dims)))
                else:
                    out = asdtype(awkward.numpy.dtype((fromdtype, dims)), awkward.numpy.dtype((fromdtype, dims)))

            if branch._fLeaves[0]._fLeafCount is None:
                return out
            else:
                return asjagged(out)

        elif len(branch._fLeaves) > 1:
            fromdtype = awkward.numpy.dtype([(str(leaf._fName.decode("ascii")), _leaf2dtype(leaf, awkward).newbyteorder(">")) for leaf in branch._fLeaves])
            if swapbytes:
                todtype = awkward.numpy.dtype([(str(leaf._fName.decode("ascii")), _leaf2dtype(leaf, awkward).newbyteorder("=")) for leaf in branch._fLeaves])
            else:
                todtype = fromdtype

            if all(leaf._fLeafCount is None for leaf in branch._fLeaves):
                return astable(asdtype(awkward.numpy.dtype((fromdtype, dims)), awkward.numpy.dtype((todtype, dims))))
            else:
                return None

    except _NotNumerical:
        if len(branch._fLeaves) == 1:
            if len(branch._fBranches) > 0 and all(len(x._fLeaves) == 1 and x._fLeaves[0]._fLeafCount is branch._fLeaves[0] for x in branch._fBranches):
                return asdtype(">i4")

            if isinstance(branch._streamer, uproot.rootio.TStreamerObject):
                obj = uproot.rootio._safename(branch._streamer._fTypeName)
                if obj == "string":
                    return asgenobj(STLString(awkward), branch._context, 0)
                elif obj in branch._context.classes:
                    return _obj_or_genobj(branch._context.classes.get(obj), branch, isjagged, cntvers=cntvers, tobject=tobject, speedbump=speedbump)

            if isinstance(branch._streamer, uproot.rootio.TStreamerInfo):
                obj = uproot.rootio._safename(branch._streamer._fName)
                if obj == "string":
                    return asgenobj(STLString(awkward), branch._context, 0)
                elif obj in branch._context.classes:
                    return _obj_or_genobj(branch._context.classes.get(obj), branch, isjagged, cntvers=cntvers, tobject=tobject, speedbump=speedbump)

            if branch._fLeaves[0].__class__.__name__ == "TLeafC":
                return asstring(skipbytes=1)

            elif branch._fLeaves[0].__class__.__name__ == "TLeafElement":
                if isinstance(branch._streamer, uproot.rootio.TStreamerBasicType):
                    try:
                        fromdtype = _ftype2dtype(branch._streamer._fType, awkward)
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
                            return asdtype(awkward.numpy.dtype((fromdtype, (fromdims,))), awkward.numpy.dtype((todtype, todims)))

                if isinstance(branch._streamer, uproot.rootio.TStreamerBasicPointer):
                    if uproot.const.kOffsetP < branch._streamer._fType < uproot.const.kOffsetP + 20:
                        try:
                            fromdtype = _ftype2dtype(branch._streamer._fType - uproot.const.kOffsetP, awkward)
                        except _NotNumerical:
                            pass
                        else:
                            if swapbytes:
                                todtype = fromdtype.newbyteorder("=")
                            else:
                                todtype = fromdtype
                            if len(branch._fLeaves) == 1 and branch._fLeaves[0]._fLeafCount is not None:
                                return asjagged(asdtype(fromdtype, todtype), skipbytes=1)

                if isinstance(branch._streamer, uproot.rootio.TStreamerObjectAny):
                    if getattr(branch._streamer, "_fTypeName", None) in (b"TArrayC", b"TArrayS", b"TArrayI", b"TArrayL", b"TArrayL64", b"TArrayF", b"TArrayD"):
                        return asjagged(asdtype(getattr(uproot.rootio, branch._streamer._fTypeName.decode("ascii"))._dtype), skipbytes=4)

                if isinstance(branch._streamer, uproot.rootio.TStreamerString):
                    return asstring(skipbytes=1)

                if isinstance(branch._streamer, uproot.rootio.TStreamerSTLstring):
                    return asstring(skipbytes=7)

                if getattr(branch._streamer, "_fType", None) == uproot.const.kCharStar:
                    return asstring(skipbytes=4)

                if getattr(branch._streamer, "_fSTLtype", None) == uproot.const.kSTLvector:
                    try:
                        fromdtype = _ftype2dtype(branch._streamer._fCtype, awkward)
                        if swapbytes:
                            ascontent = asdtype(fromdtype, fromdtype.newbyteorder("="))
                        else:
                            ascontent = asdtype(fromdtype, fromdtype)
                        if branch._isTClonesArray:
                            return asgenobj(SimpleArray(STLVector(asdtype(">i2"))), branch._context, 6)
                        else:
                            return asjagged(ascontent, skipbytes=10)

                    except _NotNumerical:
                        if branch._vecstreamer is not None:
                            try:
                                streamerClass = branch._vecstreamer.pyclass
                            except AttributeError:
                                obj = uproot.rootio._safename(branch._vecstreamer._fName)
                                if obj in branch._context.classes:
                                    streamerClass = branch._context.classes.get(obj)

                            if streamerClass.__name__ == "string":
                                return asgenobj(STLVector(STLString(awkward)), branch._context, 6)

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

                if getattr(branch._streamer, "_fTypeName", None) == b"vector<bool>":
                    return asjagged(asdtype(awkward.numpy.bool_), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<char>":
                    return asjagged(asdtype("i1"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned char>":
                    return asjagged(asdtype("u1"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<short>":
                    return asjagged(asdtype("i2"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned short>":
                    return asjagged(asdtype("u2"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<int>":
                    return asjagged(asdtype("i4"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned int>":
                    return asjagged(asdtype("u4"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<long>":
                    return asjagged(asdtype("i8"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<unsigned long>":
                    return asjagged(asdtype("u8"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<float>":
                    return asjagged(asdtype("f4"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<double>":
                    return asjagged(asdtype("f8"), skipbytes=10)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<string>":
                    return asgenobj(STLVector(STLString(awkward)), branch._context, 6)

                if getattr(branch._streamer, "_fTypeName", None) == b"map<string,bool>":
                    return asgenobj(STLMap(STLString(awkward), asdtype(awkward.numpy.bool_)), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,char>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("i1")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned char>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("u1")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,short>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("i2")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned short>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("u2")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,int>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("i4")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned int>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("u4")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,long>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("i8")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,unsigned long>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("u8")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,float>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("f4")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,double>":
                    return asgenobj(STLMap(STLString(awkward), asdtype("f8")), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"map<string,string>":
                    return asgenobj(STLMap(STLString(awkward), STLString(awkward)), branch._context, 6)

                if getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<bool> >":
                    return asgenobj(STLVector(STLVector(asdtype(awkward.numpy.bool_))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<char> >":
                    return asgenobj(STLVector(STLVector(asdtype("i1"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned char> >":
                    return asgenobj(STLVector(STLVector(asdtype("u1"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<short> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i2"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned short> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u2"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<int> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i4"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned int> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u4"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<long> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i8"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<unsigned long> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u8"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<float> >":
                    return asgenobj(STLVector(STLVector(asdtype(">f4"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<double> >":
                    return asgenobj(STLVector(STLVector(asdtype(">f8"))), branch._context, 6)
                elif getattr(branch._streamer, "_fTypeName", None) == b"vector<vector<string> >":
                    return asgenobj(STLVector(STLVector(STLString(awkward))), branch._context, 6)

                m = re.match(b"bitset<([1-9][0-9]*)>", branch._fClassName)
                if m is not None:
                    return asstlbitset(int(m.group(1)))

                if branch._fClassName == b"string":
                    return asstring(skipbytes=1)

                if branch._fClassName == b"vector<bool>":
                    return asjagged(asdtype(awkward.numpy.bool_), skipbytes=10)
                elif branch._fClassName == b"vector<char>":
                    return asjagged(asdtype("i1"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned char>":
                    return asjagged(asdtype("u1"), skipbytes=10)
                elif branch._fClassName == b"vector<short>":
                    return asjagged(asdtype("i2"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned short>":
                    return asjagged(asdtype("u2"), skipbytes=10)
                elif branch._fClassName == b"vector<int>":
                    return asjagged(asdtype("i4"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned int>":
                    return asjagged(asdtype("u4"), skipbytes=10)
                elif branch._fClassName == b"vector<long>":
                    return asjagged(asdtype("i8"), skipbytes=10)
                elif branch._fClassName == b"vector<unsigned long>":
                    return asjagged(asdtype("u8"), skipbytes=10)
                elif branch._fClassName == b"vector<float>":
                    return asjagged(asdtype("f4"), skipbytes=10)
                elif branch._fClassName == b"vector<double>":
                    return asjagged(asdtype("f8"), skipbytes=10)
                elif branch._fClassName == b"vector<string>":
                    return asgenobj(STLVector(STLString(awkward)), branch._context, 6)

                if branch._fClassName == b"vector<vector<bool> >":
                    return asgenobj(STLVector(STLVector(asdtype(awkward.numpy.bool_))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<char> >":
                    return asgenobj(STLVector(STLVector(asdtype("i1"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned char> >":
                    return asgenobj(STLVector(STLVector(asdtype("u1"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<short> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i2"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned short> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u2"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<int> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i4"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned int> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u4"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<long> >":
                    return asgenobj(STLVector(STLVector(asdtype(">i8"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<unsigned long> >":
                    return asgenobj(STLVector(STLVector(asdtype(">u8"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<float> >":
                    return asgenobj(STLVector(STLVector(asdtype(">f4"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<double> >":
                    return asgenobj(STLVector(STLVector(asdtype(">f8"))), branch._context, 6)
                elif branch._fClassName == b"vector<vector<string> >":
                    return asgenobj(STLVector(STLVector(STLString(awkward))), branch._context, 6)

        return None

interpret._titlehasdims = re.compile(br"^([^\[\]]+)(\[[^\[\]]+\])+")
interpret._itemdimpattern = re.compile(br"\[([1-9][0-9]*)\]")
interpret._itemanypattern = re.compile(br"\[(.*)\]")
