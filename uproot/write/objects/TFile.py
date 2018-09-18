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

import uproot.write.sink.file
import uproot.write.sink.cursor
import uproot.write.objects.TKey
import uproot.write.objects.TDirectory
import uproot.write.streamer

class TFileAppend(object):
    def __init__(self, path):
        self._openfile(path)
        raise NotImplementedError

    def _openfile(self, path):
        self._sink = uproot.write.sink.file.FileSink(path)
        self._path = path
        self._filename = os.path.split(path)[1].encode("utf-8")

    def __getitem__(self, where):
        uproot.open(self.path)
        raise NotImplementedError

    def __setitem__(self, where, what):
        raise NotImplementedError

class TFileCreate(TFileAppend):
    def __init__(self, path):
        self._openfile(path)
        self._writeheader()
        self._writerootdir()
        self._writestreamers()
        self._writerootkeys()

    _format1           = struct.Struct(">4sii")
    _format_end        = struct.Struct(">qq")
    _format2           = struct.Struct(">iiiBi")
    _format_seekinfo   = struct.Struct(">q")
    _format_nbytesinfo = struct.Struct(">i")
    _format_nkeys      = struct.Struct(">i")

    def _writeheader(self):
        cursor = uproot.write.sink.cursor.Cursor(0)
        self._fVersion = 1061404
        self._fBEGIN = 100
        cursor.write_fields(self._sink, self._format1, b"root", self._fVersion, self._fBEGIN)

        self._fEND = 0
        self._fSeekFree = 0
        self._endcursor = uproot.write.sink.cursor.Cursor(cursor.index)
        cursor.write_fields(self._sink, self._format_end, self._fEND, self._fSeekFree)

        self._fNbytesName = 2*len(self._filename) + 36
        cursor.write_fields(self._sink, self._format2, 1, 1, self._fNbytesName, 4, 0)  # fNbytesFree, nfree, fNbytesName, fUnits, fCompress (FIXME!)

        self._fSeekInfo = 0
        self._seekcursor = uproot.write.sink.cursor.Cursor(cursor.index)
        cursor.write_fields(self._sink, self._format_seekinfo, self._fSeekInfo)

        self._fNbytesInfo = 0
        self._nbytescursor = uproot.write.sink.cursor.Cursor(cursor.index)
        cursor.write_fields(self._sink, self._format_nbytesinfo, self._fNbytesInfo)

        cursor.write_data(self._sink, b"\x00\x010\xd5\xf5\xea~\x0b\x11\xe8\xa2D~S\x1f\xac\xbe\xef")  # fUUID (FIXME!)

    def _expandfile(self, cursor):
        self._fSeekFree = self._fEND = cursor.index
        self._endcursor.update_fields(self._sink, self._format_end, self._fEND, self._fSeekFree)

    def _writerootdir(self):
        cursor = uproot.write.sink.cursor.Cursor(self._fBEGIN)
        uproot.write.objects.TKey.TKey(cursor, self._sink, b"TFile", self._filename)
        self._rootdir = uproot.write.objects.TDirectory.TDirectory(cursor, self._sink, self._filename, 0, self._fNbytesName)
        self._expandfile(cursor)

    def _writestreamers(self):
        streamerdatabase = uproot.write.streamer.StreamerDatabase()
        # streamerdata = streamerdatabase[".all"]
        streamerdata = streamerdatabase[".empty"]

        self._fSeekInfo = self._fSeekFree
        self._seekcursor.update_fields(self._sink, self._format_seekinfo, self._fSeekInfo)

        cursor = uproot.write.sink.cursor.Cursor(self._fSeekInfo)
        streamerkey = uproot.write.objects.TKey.TKey(cursor, self._sink, b"TList", b"StreamerInfo",
                                                     fTitle    = b"Doubly linked list",
                                                     fObjlen   = len(streamerdata),
                                                     fSeekKey  = self._fSeekInfo,
                                                     fSeekPdir = self._fBEGIN)
        cursor.write_data(self._sink, streamerdata)

        self._fNbytesInfo = streamerkey.fNbytes
        self._nbytescursor.update_fields(self._sink, self._format_nbytesinfo, self._fNbytesInfo)

        self._expandfile(cursor)

    def _writerootkeys(self):
        cursor = uproot.write.sink.cursor.Cursor(self._fSeekFree)

        self._rootdir.fSeekKeys = self._fSeekFree
        self._rootdir.fNbytesKeys = 0     # FIXME!
        self._rootdir.update()

        uproot.write.objects.TKey.TKey(cursor, self._sink, b"TFile", self._filename,
                                       fSeekKey = self._rootdir.fSeekKeys,
                                       fNbytes  = self._rootdir.fNbytesKeys)

        self._nkeys = 0
        cursor.write_fields(self._sink, self._format_nkeys, self._nkeys)

        self._expandfile(cursor)
        self._sink.flush()

    def close(self):
        self._sink.close()

        
# class Create(Append):
#     def __init__(self, path):
#         self._openfile(path)

#         self.streamers = []
        
#         #Hack - Have to refactor into expand.py
#         self.expander = 4000
#         self.expandermultiple = 2
        
#         #Hack - All streamers
#         self.streamers.append(".all")
        
#         #Hack - Put all streamers in only once
#         self.count = 0
        
#         self.nkeypos = 0
        
#         #Setting the header bytes
#         head_cursor = uproot.write.cursor.Cursor(0)
        
#         magic = b"root"
#         fVersion = 61404
#         fBEGIN = 100
#         head_cursor.write_fields(self.sink, ">4sii", magic, fVersion, fBEGIN)
        
#         self.fEND_cursor = uproot.write.cursor.Cursor(head_cursor.index)
#         self.fEND = 1
#         self.fSeekFree = 1
#         self.fEND_packer = ">qq"
#         head_cursor.write_fields(self.sink, self.fEND_packer, self.fEND, self.fSeekFree)
        
#         fNbytesFree = 1
#         nfree = 1
#         self.fNbytesName = 36 + (2 * (len(self.filename)))
#         fUnits = 4
#         fCompress = 0
#         head_cursor.write_fields(self.sink, ">iiiBi", fNbytesFree, nfree, self.fNbytesName, fUnits, fCompress)
        
#         self.fSeekInfo_cursor = uproot.write.cursor.Cursor(head_cursor.index)
#         self.fSeekInfo = 0
#         self.fSeekInfo_packer = ">q"
#         head_cursor.write_fields(self.sink, self.fSeekInfo_packer, self.fSeekInfo)
        
#         self.fNbytesInfo_cursor = uproot.write.cursor.Cursor(head_cursor.index)
#         self.fNbytesInfo = 0
#         self.fNbytesInfo_packer = ">i"
#         head_cursor.write_fields(self.sink, self.fNbytesInfo_packer, self.fNbytesInfo)

#         fUUID = b"\x00\x010\xd5\xf5\xea~\x0b\x11\xe8\xa2D~S\x1f\xac\xbe\xef"
#         head_cursor.write_fields(self.sink, ">18s", fUUID)
        
#         #Writing the first key
#         cursor = uproot.write.cursor.Cursor(100)
#         beginkey_cursor = uproot.write.cursor.Cursor(100)
#         beginkey = Begin_Key(self.filename)
#         beginkey.write_key(cursor, self.sink)
#         beginkey.fKeylen = cursor.index - beginkey_cursor.index
#         beginkey.fObjlen = beginkey.fNbytes - beginkey.fKeylen
#         beginkey.update_key(beginkey_cursor, self.sink)
        
#         #Why?
#         cursor.write_strings(self.sink, self.filename)
        
#         #Setting the directory info
#         self.directorycursor = uproot.write.cursor.Cursor(cursor.index)
#         self.directory = DirectoryInfo(self.fNbytesName)
#         self.directory.write_values(cursor, self.sink)

#         #header.fSeekInfo points to begin of StreamerKey
#         self.fSeekInfo = cursor.index
#         self.fSeekInfo_cursor.update_fields(self.sink, self.fSeekInfo_packer, self.fSeekInfo)
        
#         #Write streamerkey
#         self.streamer_cursor = uproot.write.cursor.Cursor(cursor.index)
#         self.streamerkey = StreamerKey(cursor.index)
#         self.streamerkey.write_key(cursor, self.sink)
#         self.streamerkey.fKeylen = cursor.index - self.streamer_cursor.index
#         self.streamerkey.fNbytes = self.streamerkey.fKeylen + self.streamerkey.fObjlen
#         self.streamerkey.update_key(cursor, self.sink)
        
#         self.fNbytesInfo_cursor.update_fields(self.sink, self.fNbytesInfo_packer, self.streamerkey.fNbytes)
        
#         #Pointer to streamers
#         self.streamer_pointer = uproot.write.cursor.Cursor(cursor.index)
        
#         #Punt - Put empty streamers
#         streamerdatabase = StreamerDatabase()
#         self.sink.write(streamerdatabase[".empty"], cursor.index)
        
#         #Leave space for all streamers if empty needs to be replaced
#         cursor.index += 38048
        
#         #directory.fSeekKeys points to header key
#         self.directory.fSeekKeys = cursor.index
#         self.directory.update_values(self.directorycursor, self.sink)
        
#         #Allocate space for keys
#         self.keystart = cursor.index
#         self.keyend = cursor.index
#         self.keylimit = self.keystart + self.expander
        
#         #Head Key
#         self.headkeycursor = uproot.write.cursor.Cursor(cursor.index)
#         fNbytes = self.directory.fNbytesKeys
#         fSeekKey = self.directory.fSeekKeys
#         fName = self.filename
#         self.head_key = HeadKey(fNbytes, fSeekKey, fName)
#         self.head_key.write_key(cursor, self.sink)
#         self.head_key_end = uproot.write.cursor.Cursor(cursor.index)

#         #Number of Keys
#         self.nkeys = 0
#         packer = ">i"
#         cursor.write_fields(self.sink, packer, self.nkeys)

#         self.keyend = uproot.write.cursor.Cursor(cursor.index)
        
#         self.fSeekFree = cursor.index
#         self.fEND = self.fSeekFree + self.expander
        
#         self.fEND_cursor.update_fields(self.sink, self.fEND_packer, self.fEND, self.fSeekFree)

#     def __getitem__(self, where):
#         uproot.open(self.path)
#         raise NotImplementedError

#     def __setitem__(self, keyname, item):
#         if self.count == 0:
#             streamerdatabase = StreamerDatabase()
#             self.sink.write(streamerdatabase[".all"], self.streamer_pointer.index)
#             self.count += 1
        
#         cursor = uproot.write.cursor.Cursor(self.fEND)
#         pointcheck = cursor.index
        
#         if type(item) is TObjString:
#             junkkey = TObjStringJunkKey(keyname.encode("utf-8"))
#             key = TObjStringKey(keyname.encode("utf-8"), pointcheck)

#         if type(item) is TAxis:
#             junkkey = TAxisJunkKey(keyname.encode("utf-8"))
#             key = TAxisKey(keyname.encode("utf-8"), pointcheck)
        
#         junkkeycursor = uproot.write.cursor.Cursor(self.fEND)
#         junkkey.write_key(cursor, self.sink)
#         junkkey.fKeylen = cursor.index - junkkeycursor.index
#         junkkey.fNbytes = junkkey.fKeylen + junkkey.fObjlen
#         junkkey.update_key(junkkeycursor, self.sink)

#         if type(item.string) is str:
#             item.string = item.string.encode("utf-8")
        
#         item.write_bytes(cursor, self.sink)

#         # Updating Header Bytes
#         if cursor.index > self.fEND:
#             self.fEND_cursor.update_fields(self.sink, self.fEND_packer, self.fEND, self.fSeekFree)

#         #Check for Key Re-alocation
#         if self.keylimit - self.keyend < 30:
#             temp = self.sink.read(self.directory.fSeekKeys, self.expander)
#             self.expander = self.expander * self.expandermultiple
#             self.sink.write(temp, self.fEND)
#             self.keyend = self.fEND + self.keyend - self.directory.fSeekKeys
#             self.directory.fSeekKeys = self.fEND
#             self.keylimit = self.fEND + self.expander
#             self.fEND = self.keylimit
#             self.fSeekFree = self.keylimit
#             self.directory.update_values(self.directorycursor, self.sink)
#             self.head_key_end = self.directory.fSeekKeys + self.nkeypos

#         pointcheck = uproot.write.cursor.Cursor(self.keyend)
#         key.write_key(self.keyend, self.sink)
#         key.fKeylen = self.keyend.index - pointcheck
#         key.fNbytes = key.fKeylen + key.fObjlen
#         key.update_key(pointcheck, key)

#         # Updating Header Bytes
#         if cursor.index > self.fEND:
#             self.fSeekFree = cursor.index
#             self.fEND = cursor.index
#         self.fEND_cursor.update_fields(self.sink, self.fEND_packer, self.fEND, self.fSeekFree)
        
#         #Update StreamerKey
#         self.streamerkey.fNbytes = self.streamer_pointer.index - self.fSeekInfo - 1
#         self.streamerkey.fObjlen = self.streamerkey.fNbytes - self.streamerkey.fKeylen
#         self.streamerkey.fSeekKey = self.fSeekInfo
#         self.streamerkey.write_key(uproot.write.cursor.Cursor(self.fSeekInfo), self.sink)

#         #Update number of keys
#         self.nkeypos = self.head_key_end - self.directory.fSeekKeys
#         self.nkeys += 1
#         packer = ">i"
#         uproot.write.cursor.Cursor(self.head_key_end).update_fields(self.sink, packer, self.nkeys)

#         #Update DirectoryInfo
#         self.directory.fNbytesKeys = self.keyend - self.directory.fSeekKeys
#         self.directory.update_values(self.directorycursor, self.sink)

#         #Update Head Key
#         self.head_key.fNbytes = self.directory.fNbytesKeys
#         self.head_key.fKeylen = self.head_key_end - self.headkeycursor
#         self.head_key.fObjlen = self.head_key.fNbytes - self.head_key.fKeylen
#         self.head_key.update_key(self.headkeycursor, self.sink)

#         #Updating Header Bytes
#         if cursor.index > self.fEND:
#             self.fSeekFree = cursor.index
#             self.fEND = cursor.index
        
#         self.fEND_cursor.update_fields(self.sink, self.fEND_packer, self.fEND, self.fSeekFree)

#         self.sink.flush()
        
#     def close(self):
#         self.sink.close()
    
