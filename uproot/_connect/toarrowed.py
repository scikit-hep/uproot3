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

from arrowed.oam import PrimitiveOAM
from arrowed.oam import ListCountOAM
from arrowed.oam import ListOffsetOAM
from arrowed.oam import RecordOAM
from arrowed.oam import PointerOAM

import uproot

def defineOAM(tree, rename=lambda x: x.name):
    class ListWithName(list):
        def __init__(self, name):
            super(ListWithName, self).__init__()
            self.name = name

    def recurse(branch):
        bycounter = {}
        for subbranch in branch.branches:
            if len(subbranch.leaves) == 1:
                counter = subbranch.leaves[0].counter
                if counter is not None:
                    counter = counter.name

                if counter not in bycounter:
                    bycounter[counter] = ListWithName(subbranch.name)

                if len(subbranch.branches) == 0:
                    bycounter[counter].append(subbranch)
                else:
                    bycounter[counter].append(recurse(subbranch))

        return bycounter
    
    structure = recurse(tree)

    def recurse(counter, group):
        fields = {}
        for obj in group:
            if isinstance(obj, dict):
                for subcounter, subgroup in obj.items():
                    # no more than one level may be counted
                    assert counter is None or subcounter is None
                    if counter is None:
                        counter = subcounter
                    fields[subgroup.name] = recurse(counter, subgroup)

            elif hasattr(obj, "dtype"):
                fields[obj.name] = PrimitiveOAM(obj.name)

        if counter is None:
            return RecordOAM(fields)
        else:
            print "HERE", fields

            return ListCountOAM(counter, RecordOAM(fields))

    return ListCountOAM(None, RecordOAM(dict(recurse(counter, group) for counter, group in structure.items())))

tree = uproot.open("~/storage/data/small-evnt-tree-fullsplit.root")["tree"]

# tree = uproot.open("~/storage/data/nano-TTLHE-2017-09-04-lz4.root")["Events"]

print defineOAM(tree).format()
