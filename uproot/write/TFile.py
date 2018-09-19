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
import sys
import struct

import uproot.write.sink.file
import uproot.write.sink.cursor
import uproot.write.TKey
import uproot.write.TDirectory
import uproot.write.streamers
import uproot.write.registry

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
        if (sys.version_info[0] <= 2 and isinstance(where, unicode)) or (sys.version_info[0] > 2 and isinstance(where, str)):
            where = where.encode("utf-8")
        if not isinstance(where, bytes):
            raise TypeError("ROOT file key must be a string")

        if b"/" in where:
            raise NotImplementedError("subdirectories not supported yet")
        
        what = uproot.write.registry.writeable(what)

        location = self._fSeekFree
        cursor = uproot.write.sink.cursor.Cursor(location)
        newkey = uproot.write.TKey.TKey(fClassName = what.fClassName,
                                        fName      = where,
                                        fTitle     = what.fTitle,
                                        fObjlen    = what.length(),
                                        fSeekKey   = location)

        self._fSeekFree += newkey.fKeylen + what.length()
        
        newkey.write(cursor, self._sink)
        what.write(cursor, self._sink)

        self._rootdir.setkey(newkey)
        self._sink.flush()

class TFileCreate(TFileAppend):
    def __init__(self, path):
        self._openfile(path)
        self._writeheader()
        self._writerootdir()
        self._writestreamers()
        self._writerootkeys()
        self._sink.flush()

    _format1           = struct.Struct(">4sii")
    _format_end        = struct.Struct(">qq")
    _format2           = struct.Struct(">iiiBi")
    _format_seekinfo   = struct.Struct(">q")
    _format_nbytesinfo = struct.Struct(">i")

    def _writeheader(self):
        cursor = uproot.write.sink.cursor.Cursor(0)
        self._fVersion = 1061404
        self._fBEGIN = 100
        cursor.write_fields(self._sink, self._format1, b"root", self._fVersion, self._fBEGIN)

        self._fEND = 0
        self._fSeekFree = 0
        self._endcursor = uproot.write.sink.cursor.Cursor(cursor.index)
        cursor.write_fields(self._sink, self._format_end, self._fEND, self._fSeekFree)

        self._fNbytesName = 2*len(self._filename) + 36 + 8                             # two fields in TKey are 'q' rather than 'i', so +8
        cursor.write_fields(self._sink, self._format2, 1, 1, self._fNbytesName, 8, 0)  # fNbytesFree, nfree, fNbytesName, fUnits, fCompress (FIXME!)

        self._fSeekInfo = 0
        self._seekcursor = uproot.write.sink.cursor.Cursor(cursor.index)
        cursor.write_fields(self._sink, self._format_seekinfo, self._fSeekInfo)

        self._fNbytesInfo = 0
        self._nbytescursor = uproot.write.sink.cursor.Cursor(cursor.index)
        cursor.write_fields(self._sink, self._format_nbytesinfo, self._fNbytesInfo)

        cursor.write_data(self._sink, b"\x00\x010\xd5\xf5\xea~\x0b\x11\xe8\xa2D~S\x1f\xac\xbe\xef")  # fUUID (FIXME!)

    def _expandfile(self, cursor):
        if cursor.index > self._fEND:
            fillcursor = uproot.write.sink.cursor.Cursor(cursor.index - 1)
            fillcursor.update_data(self._sink, b"\x00")
        
        self._fSeekFree = self._fEND = cursor.index
        self._endcursor.update_fields(self._sink, self._format_end, self._fEND, self._fSeekFree)

    def _writerootdir(self):
        cursor = uproot.write.sink.cursor.Cursor(self._fBEGIN)
        key = uproot.write.TKey.TKey(b"TFile", self._filename)
        key.write(cursor, self._sink)
        self._rootdir = uproot.write.TDirectory.TDirectory(self, self._filename, self._fNbytesName)
        self._rootdir.write(cursor, self._sink)
        self._expandfile(cursor)

    def _writestreamers(self):
        self._fSeekInfo = self._fSeekFree
        self._seekcursor.update_fields(self._sink, self._format_seekinfo, self._fSeekInfo)

        cursor = uproot.write.sink.cursor.Cursor(self._fSeekInfo)
        streamerkey = uproot.write.TKey.TKey32(fClassName = b"TList",
                                               fName      = b"StreamerInfo",
                                               fTitle     = b"Doubly linked list",
                                               fObjlen    = len(uproot.write.streamers.streamers),
                                               fSeekKey   = self._fSeekInfo,
                                               fSeekPdir  = self._fBEGIN)
        streamerkey.write(cursor, self._sink)
        cursor.write_data(self._sink, uproot.write.streamers.streamers)

        self._fNbytesInfo = streamerkey.fNbytes
        self._nbytescursor.update_fields(self._sink, self._format_nbytesinfo, self._fNbytesInfo)

        self._expandfile(cursor)

    def _writerootkeys(self):
        self._rootdir.writekeys(uproot.write.sink.cursor.Cursor(self._fSeekFree))

    def close(self):
        self._sink.close()

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
    
