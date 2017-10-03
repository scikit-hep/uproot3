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

def branch2name(branch):
    m = re.match(r"(.*\.)*([a-zA-Z_][a-zA-Z0-9_]*)", branch.name)
    if m is not None:
        return m.group(2)
    else:
        return None

def byunderscore(fields):
    grouped = OrderedDict()
    for name, field in fields.items():
        m = re.match(r"([^_]*)_(.*)", name)
        if m is not None and m.group(1) not in fields:
            if m.group(1) not in grouped:
                grouped[m.group(1)] = OrderedDict()
            grouped[m.group(1)][m.group(2)] = field

    done = set()
    out = OrderedDict()
    for name, field in fields.items():
        m = re.match(r"([^_]*)_(.*)", name)
        if m is None or m.group(1) not in grouped:
            out[name] = field
        elif m.group(1) not in done:
            out[m.group(1)] = RecordOAM(grouped[m.group(1)])
            done.add(m.group(1))
    return RecordOAM(out)

def tree2oam(tree, branch2name=branch2name):
    def recurse(branch):
        fields = OrderedDict()
        for subbranch in branch.branches:
            if branch2name is None:
                fieldname = subbranch.name
            else:
                fieldname = branch2name(subbranch)

            if fieldname is not None:
                if len(subbranch.branches) == 0:
                    if getattr(subbranch, "dtype", numpy.dtype(object)) is not numpy.dtype(object):
                        if subbranch.name in tree.counter:
                            fields[fieldname] = ListCountOAM(tree.counter[subbranch.name].branch, PrimitiveOAM(subbranch.name))
                        else:
                            fields[fieldname] = PrimitiveOAM(subbranch.name)
                else:
                    fields[fieldname] = recurse(subbranch)

        out = byunderscore(fields)

        if branch is not tree and branch.name in tree.counter:
            return ListCountOAM(tree.counter[subbranch.name].branch, out)
        else:
            return out

    def arrayofstructs(t):
        if isinstance(t, RecordOAM):
            countarray = None
            for c in t.contents.values():
                if not isinstance(c, ListCountOAM):
                    countarray = None
                    break
                if countarray is None:
                    countarray = c.countarray
                elif countarray != c.countarray:
                    countarray = None
                    break

            if countarray is None:
                return RecordOAM(OrderedDict((n, arrayofstructs(c)) for n, c in t.contents.items()))
            else:
                return ListCountOAM(countarray, RecordOAM(OrderedDict((n, arrayofstructs(c.contents)) for n, c in t.contents.items())))

        elif isinstance(t, ListCountOAM):
            return ListCountOAM(t.countarray, t.contents)

        else:
            return t

    return ListCountOAM(None, arrayofstructs(recurse(tree)))





# tree = uproot.open("~/storage/data/small-evnt-tree-fullsplit.root")["tree"]

# tree = uproot.open("~/storage/data/TTJets_13TeV_amcatnloFXFX_pythia8_2_77.root")["Events"]

tree = uproot.open("~/storage/data/nano-TTLHE-2017-09-04-lz4.root")["Events"]

print tree2oam(tree).format()
