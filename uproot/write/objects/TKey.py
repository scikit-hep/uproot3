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

import struct

import uproot.write.sink.cursor

class TKey(object):
    def __init__(self, cursor, sink, fClassName, fName, fTitle=b"", fObjlen=0, fCycle=1, fSeekKey=100, fSeekPdir=0, fNbytes=None):
        self.fObjlen = fObjlen
        self.fCycle = fCycle
        self.fSeekKey = fSeekKey
        self.fSeekPdir = fSeekPdir
        self._fNbytes = fNbytes

        self.fKeylen = self._format1.size + cursor.length_string(fClassName) + cursor.length_string(fName) + cursor.length_string(fTitle)

        print("at", sink._sink.tell())

        self.cursor = uproot.write.sink.cursor.Cursor(cursor.index)
        self.sink = sink
        self.update()

        cursor.skip(self._format1.size)
        cursor.write_string(sink, fClassName)
        cursor.write_string(sink, fName)
        cursor.write_string(sink, fTitle)

        print("          ", fClassName, fName, fTitle)

    @property
    def fNbytes(self):
        if self._fNbytes is None:
            return self.fObjlen + self.fKeylen
        else:
            return self._fNbytes

    def update(self):
        fVersion = 1004
        fDatime = 1573188772                  # FIXME!

        print("write TKey", self.fNbytes, fVersion, self.fObjlen, fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)

        self.cursor.update_fields(self.sink, self._format1, self.fNbytes, fVersion, self.fObjlen, fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)

    _format1 = struct.Struct(">ihiIhhqq")
