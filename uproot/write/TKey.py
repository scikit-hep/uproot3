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
import uproot.write.util

class TKey(object):
    def __init__(self, fClassName, fName, fTitle=b"", fObjlen=0, fSeekKey=100, fSeekPdir=0, fCycle=1):
        self.fClassName = fClassName
        self.fName = fName
        self.fTitle = fTitle

        self.fObjlen = fObjlen
        self.fSeekKey = fSeekKey
        self.fSeekPdir = fSeekPdir
        self.fCycle = fCycle
        self.fDatime = uproot.write.util.datime()

    @property
    def fKeylen(self):
        return self._format1.size + uproot.write.sink.cursor.Cursor.length_strings([self.fClassName, self.fName, self.fTitle])

    @property
    def fNbytes(self):
        return self.fObjlen + self.fKeylen

    def update(self):
        self.cursor.update_fields(self.sink, self._format1, self.fNbytes, self._version, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)

    def write(self, cursor, sink):
        self.cursor = uproot.write.sink.cursor.Cursor(cursor.index)
        self.sink = sink

        self.update()

        cursor.skip(self._format1.size)
        cursor.write_string(sink, self.fClassName)
        cursor.write_string(sink, self.fName)
        cursor.write_string(sink, self.fTitle)

    _version = 1004
    _format1 = struct.Struct(">ihiIhhqq")

class TKey32(TKey):
    _version = 4
    _format1 = struct.Struct(">ihiIhhii")
