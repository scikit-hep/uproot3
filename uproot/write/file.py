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

import os
import struct

import uproot.write.sink
import uproot.write.cursor

from begin_key import Begin_Key
from directoryinfo import DirectoryInfo
from streamerkey import StreamerKey
from streamer import StreamerDatabase

class Append(object):
    def __init__(self, path):
        self._openfile(path)
        raise NotImplementedError

    def _openfile(self, path):
        self.path = path
        self.filename = os.path.split(self.path)[1].encode("utf-8")
        self.sink = uproot.write.sink.Sink(open(path, "wb+"))

    def __getitem__(self, where):
        uproot.open(self.path)
        raise NotImplementedError

    def __setitem__(self, where, what):
        where.split("/")
        pass
    
class Create(Append):
    
    _format1 = struct.Struct(">4siqqiiiBiqi18s")
    _format2 = struct.Struct(">ihiIhhii")
    
    def _write_header(self, cursor, sink, magic = b"root", fVersion = 61404, fBEGIN = 100, fEND = 1, fSeekFree = 1, fNbytesFree = 1, nfree = 1, fNbtyesName = (36+(2*len(self.filename))), fUnits = 4, fCompress = 0, fSeekInfo = 0, fNbytesInfo = 0):
        cursor.update_fields(sink, _format1, magic, fVersion, fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo)
    
    def __init__(self, filename):
        self._openfile(path)

        self.streamers = []
        
        #Hack - All streamers
        self.streamers.append(".all")
        
        #Setting the header bytes
        head_cursor = uproot.write.cursor.Cursor(0)
        _write_header(head_cursor, self.sink)
        
        #Writing the first key
        cursor = uproot.write.cursor.Cursor(fBEGIN)
        beginkey_cursor = uproot.write.cursor.Cursor(fBEGIN)
        beginkey = Begin_Key(self.filename)
        beginkey.write_key(cursor, self.sink)
        beginkey.fKeylen = cursor.index - beginkey_cursor.index
        beginkey.fObjlen = beginkey.fNbytes - beginkey.fKeylen
        beginkey.update_key(beginkey_cursor, self.sink)
        
        #Why?
        self.sink.write(cursor.get_strings(fName), cursor.index)
        
        #Setting the directory info
        directorycursor = uproot.write.cursor.Cursor(cursor.index)
        self.directory = DirectoryInfo(self.filename)
        self.directory.write_values(cursor, sink)
        
        #header.fSeekInfo points to begin of StreamerKey
        _write_header(fSeekInfo = cursor.index)
        
        #Write streamerkey
        self.streamer_cursor = uproot.write.cursor.Cursor(cursor.index)
        self.streamerkey = StreamerKey(cursor.index)
        self.streamerkey.write_key(cursor, self.sink)
        self.streamerkey.fKeylen = cursor.index - self.streamer_cursor.index
        self.streamerkey.fNbytes = self.streamerkey.fKeylen + self.streamerkey.fObjlen
        self.streamerkey.update_key(cursor, self.sink)
        
        _write_header(fNbytesInfo = self.streamerkey.fNbytes)
        
        #Punt - Put all streamers
        streamerdatabase = StreamerDatabase()
        self.sink.write(streamerdatabase[".all"], cursor.index)
        cursor.index = self.sink.tell()
        
        