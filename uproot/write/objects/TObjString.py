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

# from uproot.write.key import Key

# class JunkKey(Key):
#     def __init__(self, string):
#         self.string = string
#         self.fVersion = 4
#         self.fObjlen = 17 + len(self.string)
#         self.fDatime = 1573188772
#         self.fKeylen = 0
#         self.fNbytes = self.fObjlen + self.fKeylen
#         self.fCycle = 1
#         self.fSeekKey = 0
#         self.fSeekPdir = 100
#         self.packer = ">ihiIhhii"
#         self.fClassName = b'TObjString'
#         self.fName = self.string
#         self.fTitle = b'Collectable string class'
#         Key.__init__(self, self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle,
#                      self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle)

# from uproot.write.key import Key as SuperKey

# class Key(SuperKey):

#     def __init__(self, string, stringloc):
#         self.string = string
#         self.fVersion = 4
#         self.fObjlen = 17 + len(self.string)
#         self.fDatime = 1573188772
#         self.fKeylen = 0
#         self.fNbytes = self.fObjlen + self.fKeylen
#         self.fCycle = 1
#         self.fSeekKey = stringloc
#         self.fSeekPdir = 100
#         self.packer = ">ihiIhhii"
#         self.fClassName = b'TObjString'
#         self.fName = self.string
#         self.fTitle = b'Collectable string class'
#         SuperKey.__init__(self, self.packer, self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle,
#                      self.fSeekKey, self.fSeekPdir, self.fClassName, self.fName, self.fTitle)


# import numpy

# class TObjString(object):
#     def __init__(self, string):
#         if type(string) is str:
#             string = string.encode("utf-8")
#         self.string = string
        
#     def write_bytes(self, cursor, sink):
#         cnt = 17 + len(self.string) - 4
#         kByteCountMask = numpy.int64(0x40000000)
#         cnt = cnt | kByteCountMask
#         vers = 1
#         cursor.write_fields(sink, ">IH", cnt, vers)
        
#         bytestream =[0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 11, 72, 101, 108, 108, 111, 32, 87, 111, 114, 108, 100]
#         sink.write(numpy.frombuffer(bytes(bytestream), dtype=numpy.uint8), cursor.index)
#         cursor.index += len(bytestream)
        
#         fUniqueID = 0
#         fBits = 33554432
#         cursor.write_fields(sink, ">II", fUniqueID, fBits)
