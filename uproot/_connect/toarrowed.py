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

import re

from collections import OrderedDict

import numpy

from arrowed.oam import PrimitiveOAM
from arrowed.oam import ListCountOAM
from arrowed.oam import ListOffsetOAM
from arrowed.oam import RecordOAM
from arrowed.oam import PointerOAM

import uproot

def defineOAM(tree, rename=lambda x: x.name):
    def recurse(branch):
        fields = OrderedDict()
        for subbranch in branch.branches:
            if len(subbranch.branches) == 0:
                if getattr(subbranch, "dtype", numpy.dtype(object)) is not numpy.dtype(object):
                    if subbranch.name in tree.counter:
                        fields[subbranch.name] = ListCountOAM(tree.counter[subbranch.name].branch, PrimitiveOAM(subbranch.name))
                    else:
                        fields[subbranch.name] = PrimitiveOAM(subbranch.name)
            else:
                fields[subbranch.name] = recurse(subbranch)

        if branch is not tree and branch.name in tree.counter:
            return ListCountOAM(tree.counter[subbranch.name].branch, RecordOAM(fields))
        else:
            return RecordOAM(fields)

    return ListCountOAM(None, recurse(tree))





tree = uproot.open("~/storage/data/small-evnt-tree-fullsplit.root")["tree"]

# tree = uproot.open("~/storage/data/nano-TTLHE-2017-09-04-lz4.root")["Events"]

print defineOAM(tree).format()
