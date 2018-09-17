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

# class Key(object):
#     def __init__(self, packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle):
#         self.packer = packer
#         self.fVersion = fVersion
#         self.fNbytes = fNbytes
#         self.fObjlen = fObjlen
#         self.fDatime = fDatime
#         self.fKeylen = fKeylen
#         self.fCycle = fCycle
#         self.fSeekKey = fSeekKey
#         self.fSeekPdir = fSeekPdir
#         self.fClassName = fClassName
#         self.fName = fName
#         self.fTitle = fTitle
        
#     def write_key(self, cursor, sink):
#         cursor.write_fields(sink, self.packer, self.fVersion, self.fNbytes, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)
#         cursor.write_strings(sink, self.fClassName)
#         cursor.write_strings(sink, self.fName)
#         cursor.write_strings(sink, self.fTitle)
        
#     def update_key(self, cursor, sink):
#         cursor.update_fields(sink, self.packer, self.fVersion, self.fNbytes, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir)
#         cursor.update_strings(sink, self.fClassName)
#         cursor.update_strings(sink, self.fName)
#         cursor.update_strings(sink, self.fTitle)
