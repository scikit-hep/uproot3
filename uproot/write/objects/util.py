import struct
from copy import copy

import numpy

import uproot

class Util(object):

    def __init__(self):
        self._written = {}
        self.tobjstring_count = 0

    _format_cntvers = struct.Struct(">IH")

    def _putclass(self, cursor, obj, keycursor, beg):
        start = cursor.index - keycursor.index
        beg = beg - keycursor.index
        buf = b""
        objct, clsname = obj
        if id(objct) in self._written and clsname in self._written:
            buf += cursor.put_fields(self._format_putobjany1, numpy.uint32(self._written[id(objct)]))
            return buf
        if clsname in self._written:
            buf += cursor.put_fields(self._format_putobjany1, self._written[clsname] | uproot.const.kClassMask)
            if clsname != "TBranch":
                self._written[id(objct)] = beg + uproot.const.kMapOffset
        else:
            buf += cursor.put_fields(self._format_putobjany1, uproot.const.kNewClassTag)
            buf += cursor.put_cstring(clsname)
            self._written[clsname] = numpy.uint32(start + uproot.const.kMapOffset) | uproot.const.kClassMask
            self._written[id(objct)] = beg + uproot.const.kMapOffset
        if clsname == "THashList" or clsname == "TList":
            buf += self.parent_obj._put_tlist(cursor, objct)
        elif clsname == "TObjString":
            self.tobjstring_count += 1
            buf += self.parent_obj._put_tobjstring(cursor, objct, self.tobjstring_count)
        elif clsname == "TBranch":
            buf += objct.write(cursor)
        elif clsname == "TLeafI":
            buf += objct.put_tleafI(cursor)
        elif clsname == "TLeafB":
            buf += objct.put_tleafB(cursor)
        elif clsname == "TLeafD":
            buf += objct.put_tleafD(cursor)
        elif clsname == "TLeafF":
            buf += objct.put_tleafF(cursor)
        elif clsname == "TLeafL":
            buf += objct.put_tleafL(cursor)
        elif clsname == "TLeafO":
            buf += objct.put_tleafO(cursor)
        elif clsname == "TLeafS":
            buf += objct.put_tleafS(cursor)
        return buf

    _format_putobjany1 = struct.Struct(">I")
    def put_objany(self, cursor, obj, keycursor):
        class_buf = b""
        objct, clsname = obj
        if id(objct) in self._written and clsname in self._written:
            class_buf = self._putclass(cursor, obj, keycursor, cursor.index)
            buff = b""
        elif objct != [] and objct != None:
            copy_cursor = copy(cursor)
            beg = cursor.index
            cursor.skip(self._format_putobjany1.size)
            class_buf = self._putclass(cursor, obj, keycursor, beg)
            buff = copy_cursor.put_fields(self._format_putobjany1, numpy.uint32(len(class_buf)) | uproot.const.kByteCountMask)
        else:
            copy_cursor = copy(cursor)
            cursor.skip(self._format_putobjany1.size)
            buff = copy_cursor.put_fields(self._format_putobjany1, len(class_buf))
        buff += class_buf
        return buff

    def set_obj(self, parent_obj):
        self.parent_obj = parent_obj
