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

from uproot.write.objects.TAxis.junkkey import JunkKey as TAxisJunkKey
from uproot.write.objects.TAxis.key import Key as TAxisKey
from uproot.write.objects.TAxis.taxis import TAxis

from uproot.write.objects.TObjString.junkkey import JunkKey as TObjStringJunkKey
from uproot.write.objects.TObjString.key import Key as TObjStringKey
from uproot.write.objects.TObjString.tobjstring import TObjString

class Append(object):

    def _openfile(self, path):
        self.path = path
        self.filename = os.path.split(self.path)[1].encode("utf-8")
        self.sink = uproot.write.sink.Sink(open(path, "wb+"))

    def __getitem__(self, where):
        uproot.open(self.path)
        raise NotImplementedError

    def __setitem__(self, keyname, item):
        if self.count == 0:
            self.sink.write(streamerdatabase[".all"], self.streamer_pointer.index)
            self.count += 1
        
        cursor = uproot.write.cursor.Cursor(self.fEND)
        
        if type(item) is TObjString:
            junkkey = TObjStringJunkKey(keyname.encode("utf-8"))
            key = StringKey(keyname.encode("utf-8"), pointcheck)

        if type(item) is TAxis:
            junkkey = TAxisJunkKey(keyname.encode("utf-8"))
            key = AxisKey(keyname.encode("utf-8"), pointcheck)
        
        junkkeycursor = uproot.write.cursor.Cursor(self.fEND)
        junkkey.write_key(cursor, self.sink)
        junkkey.fKeylen = cursor.index - junkkeycursor.index
        junkkey.fNbytes = junkkey.fKeylen + junkkey.fObjlen
        junkkey.set_key(junkkeycursor, self.sink)

        if type(item.string) is str:
            item.string = item.string.encode("utf-8")
        
        item.write_bytes(cursor, self.sink)

        # Updating Header Bytes
        if cursor.index > self.fEND:
            _write_header(fSeekFree = cursor.index, fEND = cursor.index)

        #Check for Key Re-alocation
        if self.keylimit - self.keyend < 30:
            self.file.seek(self.directory.fSeekKeys)
            temp = self.sink.read(self.expander)
            self.expander = self.expander * self.expandermultiple
            self.file.seek(self.fEND)
            self.file.write(temp)
            self.keyend = self.fEND + self.keyend - self.directory.fSeekKeys
            self.directory.fSeekKeys = self.fEND
            self.keylimit = self.fEND + self.expander
            self.fEND = self.keylimit
            fSeekFree = self.keylimit
            self.directory.update_values(directorycursor, self.sink)
            self.head_key_end = self.directory.fSeekKeys + self.nkeypos

        pointcheck = uproot.write.cursor.Cursor(self.keyend)
        key.write_key(uproot.write.cursor.Cursor(self.keyend), self.sink)
        self.keyend = self.file.tell()
        key.fKeylen = self.keyend - pointcheck
        key.fNbytes = key.fKeylen + key.fObjlen
        key.update_key(pointcheck, key)

        # Updating Header Bytes
        if cursor.index > self.fEND:
            fSeekFree = cursor.index
            self.fEND = cursor.index
        _write_header(fSeekFree = fSeekFree, fEND = self.fEND)
        
        #Update StreamerKey
        self.streamerkey.fNbytes = self.streamerend - self.header.fSeekInfo - 1
        self.streamerkey.fObjlen = self.streamerkey.fNbytes - self.streamerkey.fKeylen
        self.streamerkey.fSeekKey = self.header.fSeekInfo
        self.sink.set_key(self.header.fSeekInfo, self.streamerkey)
        
        #Update TList Streamer
        self.allstreamers.cnt = self.streamerkey.fObjlen
        self.allstreamers.pos = self.header.fSeekInfo + self.streamerkey.fKeylen
        self.allstreamers.write()

        #Update number of keys
        self.nkeypos = self.head_key_end - self.directory.fSeekKeys
        self.nkeys += 1
        packer = ">i"
        uproot.write.cursor.Cursor(self.head_key_end).update_fields(self.sink, packer, self.nkeys)

        #Update DirectoryInfo
        self.directory.fNbytesKeys = self.keyend - self.directory.fSeekKeys
        self.directory.update_values(directorycursor, self.sink)

        #Update Head Key
        self.head_key.fNbytes = self.directory.fNbytesKeys
        self.head_key.fKeylen = self.head_key_end - self.head_key_cursor
        self.head_key.fObjlen = self.head_key.fNbytes - self.head_key.fKeylen
        self.head_key.update_key(self.head_key_cursor, self.sink)

        #Updating Header Bytes
        if cursor.index > self.fEND:
            fSeekFree = cursor.index
            self.fEND = cursor.index

        _write_header(fSeekFree = fSeekFree, fEND = self.fEND)

        self.sink.flush()
        
    def close(self):
        self.sink.close()
    
class Create(Append):
    
    _format1 = struct.Struct(">4siqqiiiBiqi18s")
    _format2 = struct.Struct(">ihiIhhii")
    
    def _write_header(self, cursor, sink, magic = b"root", fVersion = 61404, fBEGIN = 100, fEND = 1, fSeekFree = 1, fNbytesFree = 1, nfree = 1, fNbtyesName = (36+(2*len(self.filename))), fUnits = 4, fCompress = 0, fSeekInfo = 0, fNbytesInfo = 0):
        cursor.update_fields(sink, _format1, magic, fVersion, fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo)
    
    def __init__(self, path):
        
        self._openfile(path)

        self.streamers = []
        
        #Hack - Have to refactor into expand.py
        self.expander = 4000
        self.expandermultiple = 2
        
        #Hack - All streamers
        self.streamers.append(".all")
        
        #Hack - Put all streamers in only once
        self.count = 0
        
        self.nkeypos = 0
        
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
        
        #Pointer to streamers
        self.streamer_pointer = uproot.write.cursor.Cursor(cursor.index)
        
        #Punt - Put empty streamers
        streamerdatabase = StreamerDatabase()
        self.sink.write(streamerdatabase[".empty"], cursor.index)
        
        #Leave space for all streamers if empty needs to be replaced
        cursor.index += 38048
        
        #directory.fSeekKeys points to header key
        self.directory.fSeekKeys = cursor.index
        self.directory.update_values(directorycursor, self.sink)
        
        #Allocate space for keys
        self.keystart = cursor.index
        self.keyend = cursor.index
        self.keylimit = self.keystart + self.expander
        
        #Head Key
        self.headkeycursor = uproot.write.cursor.Cursor(cursor.index)
        fNbytes = self.directory.fNbytesKeys
        fSeekKey = self.directory.fSeekKeys
        fName = self.bytename
        self.head_key = HeadKey(fNbytes, fSeekKey, fName)
        self.head_key.write_key(cursor, self.sink)
        self.head_key_end = uproot.write.cursor.Cursor(cursor.index)

        #Number of Keys
        self.nkeys = 0
        packer = ">i"
        cursor.write_fields(self.sink, packer, self.nkeys)

        self.keyend = uproot.write.cursor.Cursor(cursor.index)
        
        fSeekFree = cursor.index
        self.fEND = header.fSeekFree + self.expander
        _write_header(fSeekFree = fSeekFree, fEND = self.fEND)
        
    def _openfile(self, path):
        self.path = path
        self.filename = os.path.split(self.path)[1].encode("utf-8")
        self.sink = uproot.write.sink.Sink(open(path, "wb+"))

    def __getitem__(self, where):
        uproot.open(self.path)
        raise NotImplementedError

    def __setitem__(self, keyname, item):
        if self.count == 0:
            self.sink.write(streamerdatabase[".all"], self.streamer_pointer.index)
            self.count += 1
        
        cursor = uproot.write.cursor.Cursor(self.fEND)
        
        if type(item) is TObjString:
            junkkey = TObjStringJunkKey(keyname.encode("utf-8"))
            key = StringKey(keyname.encode("utf-8"), pointcheck)

        if type(item) is TAxis:
            junkkey = TAxisJunkKey(keyname.encode("utf-8"))
            key = AxisKey(keyname.encode("utf-8"), pointcheck)
        
        junkkeycursor = uproot.write.cursor.Cursor(self.fEND)
        junkkey.write_key(cursor, self.sink)
        junkkey.fKeylen = cursor.index - junkkeycursor.index
        junkkey.fNbytes = junkkey.fKeylen + junkkey.fObjlen
        junkkey.set_key(junkkeycursor, self.sink)

        if type(item.string) is str:
            item.string = item.string.encode("utf-8")
        
        item.write_bytes(cursor, self.sink)

        # Updating Header Bytes
        if cursor.index > self.fEND:
            _write_header(fSeekFree = cursor.index, fEND = cursor.index)

        #Check for Key Re-alocation
        if self.keylimit - self.keyend < 30:
            self.file.seek(self.directory.fSeekKeys)
            temp = self.sink.read(self.expander)
            self.expander = self.expander * self.expandermultiple
            self.file.seek(self.fEND)
            self.file.write(temp)
            self.keyend = self.fEND + self.keyend - self.directory.fSeekKeys
            self.directory.fSeekKeys = self.fEND
            self.keylimit = self.fEND + self.expander
            self.fEND = self.keylimit
            fSeekFree = self.keylimit
            self.directory.update_values(directorycursor, self.sink)
            self.head_key_end = self.directory.fSeekKeys + self.nkeypos

        pointcheck = uproot.write.cursor.Cursor(self.keyend)
        key.write_key(uproot.write.cursor.Cursor(self.keyend), self.sink)
        self.keyend = self.file.tell()
        key.fKeylen = self.keyend - pointcheck
        key.fNbytes = key.fKeylen + key.fObjlen
        key.update_key(pointcheck, key)

        # Updating Header Bytes
        if cursor.index > self.fEND:
            fSeekFree = cursor.index
            self.fEND = cursor.index
        _write_header(fSeekFree = fSeekFree, fEND = self.fEND)
        
        #Update StreamerKey
        self.streamerkey.fNbytes = self.streamerend - self.header.fSeekInfo - 1
        self.streamerkey.fObjlen = self.streamerkey.fNbytes - self.streamerkey.fKeylen
        self.streamerkey.fSeekKey = self.header.fSeekInfo
        self.sink.set_key(self.header.fSeekInfo, self.streamerkey)
        
        #Update TList Streamer
        self.allstreamers.cnt = self.streamerkey.fObjlen
        self.allstreamers.pos = self.header.fSeekInfo + self.streamerkey.fKeylen
        self.allstreamers.write()

        #Update number of keys
        self.nkeypos = self.head_key_end - self.directory.fSeekKeys
        self.nkeys += 1
        packer = ">i"
        uproot.write.cursor.Cursor(self.head_key_end).update_fields(self.sink, packer, self.nkeys)

        #Update DirectoryInfo
        self.directory.fNbytesKeys = self.keyend - self.directory.fSeekKeys
        self.directory.update_values(directorycursor, self.sink)

        #Update Head Key
        self.head_key.fNbytes = self.directory.fNbytesKeys
        self.head_key.fKeylen = self.head_key_end - self.head_key_cursor
        self.head_key.fObjlen = self.head_key.fNbytes - self.head_key.fKeylen
        self.head_key.update_key(self.head_key_cursor, self.sink)

        #Updating Header Bytes
        if cursor.index > self.fEND:
            fSeekFree = cursor.index
            self.fEND = cursor.index

        _write_header(fSeekFree = fSeekFree, fEND = self.fEND)

        self.sink.flush()
        
    def close(self):
        self.sink.close()
    