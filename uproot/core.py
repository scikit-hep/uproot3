#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uproot.rootio

class TObjArray(uproot.rootio.Deserialized):
    """Represents a TObjArray, an arbitrary-length list of objects in a ROOT file.

    Supports a list-like interface, including iteration, `len`, and `__getitem__`.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()

        if vers >= 3:
            # TObjArray is a TObject
            walker.skipversion()
            walker.skiptobject()

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
        vers, bcnt = walker.readversion()
        walker.skipversion()
        walker.skiptobject()

        self.name = walker.readstring()
        self.title = walker.readstring()

        self._checkbytecount(walker.index - start, bcnt)

class TAttLine(uproot.rootio.Deserialized):
    """Represents a TAttLine; implemented only because it's a supertype of other classes.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hhh")  # color, style, width
        self._checkbytecount(walker.index - start, bcnt)

class TAttFill(uproot.rootio.Deserialized):
    """Represents a TAttFill; implemented only because it's a supertype of other classes.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hh")  # color, style
        self._checkbytecount(walker.index - start, bcnt)

class TAttMarker(uproot.rootio.Deserialized):
    """Represents a TAttMarker; implemented only because it's a supertype of other classes.
    """
    def __init__(self, filewalker, walker):
        walker.startcontext()
        start = walker.index
        vers, bcnt = walker.readversion()
        walker.skip("!hhf")  # color, style, width
        self._checkbytecount(walker.index - start, bcnt)
