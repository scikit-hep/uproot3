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

def tostr(obj):
    if hasattr(obj, "decode"):
        return obj.decode("ascii")
    else:
        return obj

def branch2name(branch):
    m = branch2name.regex.match(tostr(branch.name))
    if m is not None:
        return m.group(2)
    else:
        return None

branch2name.regex = re.compile(r"(.*\.)*([a-zA-Z_][a-zA-Z0-9_]*)")

def byunderscore(fields, recordname):
    grouped = OrderedDict()
    for name, field in fields.items():
        m = byunderscore.regex.match(name)
        if m is not None and m.group(1) not in fields:
            if m.group(1) not in grouped:
                grouped[m.group(1)] = OrderedDict()
            grouped[m.group(1)][m.group(2)] = field

    done = set()
    out = OrderedDict()
    for name, field in fields.items():
        m = byunderscore.regex.match(name)
        if m is None or m.group(1) not in grouped:
            out[name] = field
        elif m.group(1) not in done:
            out[m.group(1)] = RecordOAM(grouped[m.group(1)], name=m.group(1))
            done.add(m.group(1))
    return RecordOAM(out, name=recordname)

byunderscore.regex = re.compile(r"([a-zA-Z][a-zA-Z0-9]*)_([a-zA-Z_][a-zA-Z0-9_]*)")

def schema(tree, branch2name=branch2name, combine=byunderscore):
    def recurse(branch):
        fields = OrderedDict()
        for subbranch in branch.branches:
            if branch2name is None:
                fieldname = tostr(subbranch.name)
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

        if branch2name is None:
            recordname = tostr(branch.name)
        else:
            recordname = branch2name(branch)

        if combine is None:
            out = RecordOAM(fields, name=recordname)
        elif hasattr(combine, "__code__") and combine.__code__.co_argcount == 2:
            out = combine(fields, recordname)
        else:
            out = combine(fields)

        if branch is not tree and branch.name in tree.counter:
            return ListCountOAM(tree.counter[branch.name].branch, out)
        else:
            return out

    def flatten(rec):
        for n, c in rec.contents.items():
            if isinstance(c, RecordOAM):
                for nc in flatten(c):
                    yield nc
            else:
                yield n, c

    def droplist(t, name):
        if isinstance(t, ListCountOAM):
            return t.contents

        elif isinstance(t, RecordOAM):
            return RecordOAM(dict((n, droplist(c, n)) for n, c in t.contents.items()), name=name)

        else:
            return t

    def arrayofstructs(t):
        if isinstance(t, RecordOAM):
            countarray = None
            for n, c in flatten(t):
                if not isinstance(c, ListCountOAM):
                    countarray = None
                    break
                if countarray is None:
                    countarray = c.countarray
                elif countarray != c.countarray:
                    countarray = None
                    break

            if countarray is None:
                return RecordOAM(OrderedDict((n, arrayofstructs(c)) for n, c in t.contents.items()), name=t.name)
            else:
                return ListCountOAM(countarray, RecordOAM(OrderedDict((n, arrayofstructs(droplist(c, n))) for n, c in t.contents.items()), name=t.name))

        elif isinstance(t, ListCountOAM):
            return ListCountOAM(t.countarray, arrayofstructs(t.contents))

        else:
            return t

    return ListCountOAM(None, arrayofstructs(recurse(tree)))

_schema = schema

def proxy(tree, schema=None):
    if schema is None:
        schema = _schema(tree)
    source = tree.lazyarrays()
    source[None] = numpy.array([tree.numentries], dtype=numpy.int64)
    return schema.resolved(source, lazy=True).proxy(0)

def run(tree, function, env={}, numba={"nopython": True, "nogil": True}, executor=None, cache=None, schema=None, debug=False, *args):
    # get an Object Array Map (OAM) schema
    if schema is None:
        schema = _schema(tree)

    # compile the function, using the OAM as the first and only argument
    compiled = schema.compile(function, env=env, numba=numba, debug=debug)

    # define an accessor that can be applied to every node in the OAM tree
    errorslist = []
    def getarray(tree, schema):
        branchname = schema.name
        if cache is not None and branchname in cache:
            return cache[branchname]

        if branchname is None:
            array = numpy.array([tree.numentries], dtype=numpy.int64)
        else:
            branch = tree.branch(branchname)
            array, res = branch.array(dtype=branch.dtype.newbyteorder("="), executor=executor, block=False)
            errorslist.append(res)

        if cache is not None:
            cache[branchname] = array

        return array

    # set this lazy accessor on everything
    resolved = schema.accessedby(getarray).resolved(tree, lazy=True)

    # but only load the arrays that are actually associated with symbols in the code
    sym2array = {}
    for parameter in compiled.parameters.transformed:
        for symbol, (member, attr) in parameter.sym2obj.items():
            sym2array[symbol] = resolved.findbybase(member).get(attr)

    # if an executor was used, this blocks until all arrays are filled
    for errors in errorslist:
        for cls, err, trc in errors:
            if cls is not None:
                _delayedraise(cls, err, trc)

    return compiled(resolved, *args)
