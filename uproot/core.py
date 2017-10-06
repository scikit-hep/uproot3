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

import uproot.rootio

class TObjArray(uproot.rootio.Deserialized):
    """Represents a TObjArray, an arbitrary-length list of objects in a ROOT file.

    Supports a list-like interface, including iteration, `len`, and `__getitem__`.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = self._readversion(walker)

        if vers >= 3:
            # TObjArray is a TObject
            self._skipversion(walker)
            self._skiptobject(walker)

        if vers >= 2:
            # TObjArray is a not a TObject
            self.name = walker.readstring()

        nobjs, low = walker.readfields("!ii")

        self.items = [uproot.rootio.Deserialized._deserialize(filewalker, walker) for i in range(nobjs)]

        self._checkbytecount(walker.index - start, bcnt)

    def __del__(self):
        del self.items

    def __repr__(self):
        return "<TObjArray len={0} at 0x{1:012x}>".format(len(self.items), id(self))

    def __getitem__(self, i):
        return self.items[i]

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

uproot.rootio.Deserialized.classes[b"TObjArray"] = TObjArray

class TNamed(uproot.rootio.Deserialized):
    """Represents a TNamed; implemented only because it's a supertype of other classes.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = self._readversion(walker)
        self._skipversion(walker)
        self._skiptobject(walker)

        self.name = walker.readstring()
        self.title = walker.readstring()

        self._checkbytecount(walker.index - start, bcnt)

class TAttLine(uproot.rootio.Deserialized):
    """Represents a TAttLine; implemented only because it's a supertype of other classes.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = self._readversion(walker)
        walker.skip("!hhh")  # color, style, width
        self._checkbytecount(walker.index - start, bcnt)

class TAttFill(uproot.rootio.Deserialized):
    """Represents a TAttFill; implemented only because it's a supertype of other classes.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = self._readversion(walker)
        walker.skip("!hh")  # color, style
        self._checkbytecount(walker.index - start, bcnt)

class TAttMarker(uproot.rootio.Deserialized):
    """Represents a TAttMarker; implemented only because it's a supertype of other classes.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = self._readversion(walker)
        walker.skip("!hhf")  # color, style, width
        self._checkbytecount(walker.index - start, bcnt)
