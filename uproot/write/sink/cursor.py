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

class Cursor(object):
    def __init__(self, index):
        self.index = index

    def skip(self, numbytes):
        self.index += numbytes

    def update_fields(self, sink, format, *args):
        sink.write(format.pack(*args), self.index)

    def write_fields(self, sink, format, *args):
        self.update_fields(sink, format, *args)
        self.index += format.size

    @staticmethod
    def length_string(string):
        if len(string) < 255:
            return len(string) + 1
        else:
            return len(string) + 5

    @staticmethod
    def length_strings(strings):
        return sum(Cursor.length_string(x) for x in strings)

    _format_byte = struct.Struct("B")
    _format_byteint = struct.Struct(">Bi")
    def update_string(self, sink, data):
        if len(data) < 255:
            sink.write(self._format_byte.pack(len(data)), self.index)
            sink.write(data, self.index + 1)
        else:
            sink.write(self._format_byteint.pack(255, len(data)), self.index)
            sink.write(data, self.index + 5)

    def write_string(self, sink, data):
        self.update_string(sink, data)
        self.index += self.length_string(data)

    def update_cstring(self, sink, data):
        sink.write(data, self.index)
        sink.write(b"\x00")

    def write_cstring(self, sink, data):
        self.update_cstring(sink, data)
        self.index += len(data) + 1

    def update_data(self, sink, data):
        sink.write(data, self.index)

    def write_data(self, sink, data):
        self.update_data(sink, data)
        self.index += len(data)

    def update_array(self, sink, data):
        sink.write(data.tostring(), self.index)

    def write_array(self, sink, data):
        self.update_array(sink, data)
        self.index += data.nbytes
