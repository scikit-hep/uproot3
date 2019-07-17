import struct
from copy import copy

import uproot
from uproot.write.objects.TH import TH

class Util(object):

    _written = {}

    _format_cntvers = struct.Struct(">IH")

    def _putclass(self, cursor, obj, keycursor):
        start = cursor.index - keycursor.index
        buf = b""
        objct, clsname = obj
        if clsname in self._written:
            buf += cursor.put_fields(self._format_putobjany1, (self._written[clsname]) | uproot.const.kClassMask)
            if clsname == "THashList" or clsname == "TList":
                buf += self.obj.put_tlist(cursor, objct)
            elif clsname == "TObjString":
                self.tobjstring_count += 1
                buf += self.obj.put_tobjstring(cursor, objct, self.tobjstring_count)
        else:
            buf += cursor.put_fields(self._format_putobjany1, uproot.const.kNewClassTag)
            buf += cursor.put_cstring(clsname)
            self._written[clsname] = (start + uproot.const.kMapOffset) | uproot.const.kClassMask
            if clsname == "THashList" or clsname == "TList":
                buf += self.obj.put_tlist(cursor, objct)
            elif clsname == "TObjString":
                self.tobjstring_count = 1
                buf += self.obj.put_tobjstring(cursor, objct, self.tobjstring_count)
        return buf

    _format_putobjany1 = struct.Struct(">I")
    def put_objany(self, cursor, obj, keycursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_putobjany1.size)
        class_buf = b""
        objct, _ = obj
        if objct != []:
            class_buf = self._putclass(cursor, obj, keycursor)
            buff = copy_cursor.put_fields(self._format_putobjany1, len(class_buf) | uproot.const.kByteCountMask)
        else:
            buff = copy_cursor.put_fields(self._format_putobjany1, len(class_buf))
        buff += class_buf
        return buff

    def set_obj(self, obj):
        self.obj = obj
