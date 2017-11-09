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

import re

import numpy

from uproot.interp.numerical import asdtype
from uproot.interp.numerical import asarray

def interpret(branch, classes=None, swapbytes=True):
    if classes is None:
        classes = branch._context.classes

    class NotNumpy(Exception): pass

    def leaf2dtype(leaf):
        classname = leaf.__class__.__name__
        if classname == "TLeafO":
            return numpy.dtype(numpy.bool)
        elif classname == "TLeafB":
            if leaf.fIsUnsigned:
                return numpy.dtype(numpy.uint8)
            else:
                return numpy.dtype(numpy.int8)
        elif classname == "TLeafS":
            if leaf.fIsUnsigned:
                return numpy.dtype(numpy.uint16)
            else:
                return numpy.dtype(numpy.int16)
        elif classname == "TLeafI":
            if leaf.fIsUnsigned:
                return numpy.dtype(numpy.uint32)
            else:
                return numpy.dtype(numpy.int32)
        elif classname == "TLeafL":
            if leaf.fIsUnsigned:
                return numpy.dtype(numpy.uint64)
            else:
                return numpy.dtype(numpy.int64)
        elif classname == "TLeafF":
            return numpy.dtype(numpy.float32)
        elif classname == "TLeafD":
            return numpy.dtype(numpy.float64)
        else:
            raise NotNumpy

    dims = ()
    if len(branch.fLeaves) == 1:
        m = interpret._titlehasdims.match(branch.fLeaves[0].fTitle)
        if m is not None:
            dims = tuple(int(x) for x in re.findall(interpret._itemdimpattern, branch.fLeaves[0].fTitle))
    else:
        for leaf in branch.fLeaves:
            if interpret._titlehasdims.match(leaf.fTitle):
                return None

    try:
        if len(branch.fLeaves) == 1:
            fromdtype = leaf2dtype(branch.fLeaves[0]).newbyteorder(">")
            if swapbytes:
                return asdtype(fromdtype, fromdtype.newbyteorder("="), dims, dims)
            else:
                return asdtype(fromdtype, fromdtype, dims, dims)
        else:
            fromdtype = numpy.dtype([(leaf.fName, leaf2dtype(leaf).newbyteorder(">")) for leaf in branch.fLeaves])
            if swapbytes:
                todtype = numpy.dtype([(leaf.fName, leaf2dtype(leaf).newbyteorder("=")) for leaf in branch.fLeaves])
            else:
                todtype = fromdtype
            return asdtype(fromdtype, todtype, dims, dims)

    except NotNumpy:
        if len(branch.fLeaves) == 1:
            if branch.fLeaves[0].__class__.__name__ == "TLeafC":
                raise NotImplementedError("point this at the new Strings class!")

            elif branch.fLeaves[0].__class__.__name__ == "TLeafElement":
                classname = None
                if classname in classes:
                    raise NotImplementedError("point this at a class generated from streamers!")

        return None

interpret._titlehasdims = re.compile(br"^([^\[\]]+)(\[[^\[\]]+\])+")
interpret._itemdimpattern = re.compile(br"\[([1-9][0-9]*)\]")
