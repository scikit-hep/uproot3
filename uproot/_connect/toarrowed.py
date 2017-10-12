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

from collections import OrderedDict

import numpy

from arrowed.schema import Primitive
from arrowed.schema import ListCount
from arrowed.schema import ListOffset
from arrowed.schema import Record
from arrowed.schema import Pointer

from uproot import iterator

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
            out[m.group(1)] = Record(grouped[m.group(1)], name=m.group(1))
            done.add(m.group(1))
    return Record(out, name=recordname)

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
                            fields[fieldname] = ListCount(tree.counter[subbranch.name].branch, Primitive(subbranch.name))
                        else:
                            fields[fieldname] = Primitive(subbranch.name)
                else:
                    fields[fieldname] = recurse(subbranch)

        if branch2name is None:
            recordname = tostr(branch.name)
        else:
            recordname = branch2name(branch)

        if combine is None:
            out = Record(fields, name=recordname)
        elif hasattr(combine, "__code__") and combine.__code__.co_argcount == 2:
            out = combine(fields, recordname)
        else:
            out = combine(fields)

        if branch is not tree and branch.name in tree.counter:
            return ListCount(tree.counter[branch.name].branch, out)
        else:
            return out

    def flatten(rec):
        for n, c in rec.contents.items():
            if isinstance(c, Record):
                for nc in flatten(c):
                    yield nc
            else:
                yield n, c

    def droplist(t, name):
        if isinstance(t, ListCount):
            return t.contents

        elif isinstance(t, Record):
            return Record(dict((n, droplist(c, n)) for n, c in t.contents.items()), name=name)

        else:
            return t

    def arrayofstructs(t):
        if isinstance(t, Record):
            countarray = None
            for n, c in flatten(t):
                if not isinstance(c, ListCount):
                    countarray = None
                    break
                if countarray is None:
                    countarray = c.countarray
                elif countarray != c.countarray:
                    countarray = None
                    break

            if countarray is None:
                return Record(OrderedDict((n, arrayofstructs(c)) for n, c in t.contents.items()), name=t.name)
            else:
                return ListCount(countarray, Record(OrderedDict((n, arrayofstructs(droplist(c, n))) for n, c in t.contents.items()), name=t.name))

        elif isinstance(t, ListCount):
            return ListCount(t.countarray, arrayofstructs(t.contents))

        else:
            return t

    return ListCount(None, arrayofstructs(recurse(tree)))

_schema = schema

def proxy(tree, schema=None):
    if schema is None:
        schema = _schema(tree)
    source = tree.lazyarrays()
    source[None] = numpy.array([tree.numentries], dtype=numpy.int32)
    return schema.resolved(source, lazy=True).proxy(0)

def run(tree, function, args=(), paramtypes={}, env={}, numba={"nopython": True, "nogil": True}, executor=None, fcncache=None, datacache=None, schema=None, debug=False):
    # get an object array map schema
    if schema is None:
        schema = _schema(tree)

    # compile the function, using the schema as the first and only argument
    compiled = schema.compile(function, paramtypes=paramtypes, env=env, numba=numba, fcncache=fcncache, debug=debug)

    # define an accessor that can be applied to every node in the schema tree
    errorslist = []
    def getarray(tree, schema):
        branchname = schema.name
        if datacache is not None and branchname in datacache:
            return datacache[branchname]

        if branchname is None:
            array = numpy.array([tree.numentries], dtype=numpy.int32)
        else:
            branch = tree.branch(branchname)
            array, res = branch.array(dtype=branch.dtype.newbyteorder("="), executor=executor, block=False)
            errorslist.append(res)

        if datacache is not None:
            datacache[branchname] = array

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

def compile(tree, function, paramtypes={}, env={}, numba={"nopython": True, "nogil": True}, fcncache=None, schema=None, debug=False):
    if schema is None:
        schema = _schema(tree)
    dtypes = dict((b.name, b.dtype) for b in tree.allbranches if getattr(b, "dtype", None) is not None)
    return ArrowedFunction(schema, dtypes, schema.compile(function, paramtypes=paramtypes, env=env, numba=numba, fcncache=fcncache, debug=debug))

class ArrowedFunction(object):
    def __init__(self, schema, dtypes, compiled):
        self._schema = schema
        self._dtypes = dtypes
        self._compiled = compiled

    def run(self, entries, path, treepath, args=(), memmap=True, executor=None, datacache=None, reportentries=False):
        if datacache is not None:
            raise NotImplementedError

        entriesarray = [entries]

        def getarray(arrays, schema):
            branchname = schema.name
            if branchname is None:
                array = numpy.array(entriesarray, dtype=numpy.int32)
            else:
                array = arrays[branchname]
            return array

        accessor = self._schema.accessedby(getarray)

        branchdtypes = {}
        for parameter in self._compiled.parameters.transformed:
            for symbol, (member, attr) in parameter.sym2obj.items():
                branchname = member.name
                if branchname is not None:
                    branchdtypes[branchname] = self._dtypes[branchname].newbyteorder("=")

        for entrystart, entryend, arrays in iterator(entries, path, treepath, branchdtypes, memmap=memmap, executor=executor, reportentries=True):
            entriesarray = [entryend - entrystart]

            resolved = accessor.resolved(arrays, lazy=True)
            for parameter in self._compiled.parameters.transformed:
                for symbol, (member, attr) in parameter.sym2obj.items():
                    resolved.findbybase(member).get(attr)

            out = self._compiled(resolved, *args)
            if reportentries:
                yield entrystart, entryend, out
            else:
                yield out
