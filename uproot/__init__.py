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

# load all classes into uproot.rootio.Deserialized.classes
import uproot.rootio
import uproot.core
import uproot.tree

def open(path, memmap=True):
    try:
        from urlparse import urlparse
    except ImportError:
        from urllib.parse import urlparse

    parsed = urlparse(path)
    if parsed.scheme == "file" or parsed.scheme == "":
        path = parsed.netloc + parsed.path
        if memmap:
            import uproot.walker.arraywalker
            return uproot.rootio.TFile(uproot.walker.arraywalker.ArrayWalker.memmap(path))
        else:
            import uproot.walker.localfilewalker
            return uproot.rootio.TFile(uproot.walker.localfilewalker.LocalFileWalker(path))

    elif parsed.scheme == "root":
        return xrootd(path)

    else:
        raise ValueError("URI scheme not recognized: {0}".format(path))

def memmap(localpath):
    import uproot.walker.arraywalker
    return uproot.rootio.TFile(uproot.walker.arraywalker.ArrayWalker.memmap(localpath))

def xrootd(path):
    import uproot.walker.xrootdwalker
    return uproot.rootio.TFile(uproot.walker.xrootdwalker.XRootDWalker(path))

def iterator(entries, path, treepath, branchdtypes=lambda branch: branch.dtype, memmap=True, executor=None, outputtype=dict, reportentries=False):
    import sys
    import glob
    import os.path
    from collections import namedtuple
    try:
        from urlparse import urlparse
    except ImportError:
        from urllib.parse import urlparse

    import numpy

    if hasattr(path, "decode"):
        path = path.decode("ascii")

    def explode(x):
        parsed = urlparse(x)
        if parsed.scheme == "file" or parsed.scheme == "":
            return sorted(glob.glob(os.path.expanduser(parsed.netloc + parsed.path)))
        else:
            return [x]

    if (sys.version_info[0] <= 2 and isinstance(path, unicode)) or \
       (sys.version_info[0] > 2 and isinstance(path, str)):
        paths = explode(path)
    else:
        paths = [y for x in path for y in explode(x)]

    if not isinstance(entries, int) or entries < 1:
        raise ValueError("number of entries per iteration must be an integer, at least 1")

    oldpath = None
    oldtoget = None

    holdover = None
    holdoverentries = 0

    outerstart = 0
    outerend = 0

    for path in paths:
        tree = open(path, memmap)[treepath]

        toget = list(uproot.tree.TTree._normalizeselection(branchdtypes, tree.allbranches))

        newtoget = dict((b.name, d) for b, d in toget)
        if oldtoget is not None:
            for key in set(oldtoget.keys()).union(set(newtoget.keys())):
                if key not in newtoget:
                    raise ValueError("branch {0} cannot be found in {1}, but it was in {2}".format(repr(key), repr(path), repr(oldpath)))

                if key not in oldtoget:
                    del newtoget[key]
                elif newtoget[key] != newtoget[key]:
                    raise ValueError("branch {0} is a {1} in {2}, but it was a {3} in {4}".format(repr(key), newtoget[key], repr(path), oldtoget[key], repr(oldpath)))

        oldpath = path
        oldtoget = newtoget

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, dtype in toget])

        def output(arrays, outerstart, outerend):
            if outputtype == dict:
                out = arrays
            elif issubclass(outputtype, dict) or outputtype == tuple or outputtype == list:
                out = outputtype(arrays.items())
            else:
                out = outputtype(*[array for name, array in arrays.items()])

            if reportentries:
                return outerstart, outerend, out
            else:
                return out

        def ranges():
            x = 0
            while x < tree.entries:
                if x == 0 and holdoverentries != 0:
                    nextx = x + (entries - holdoverentries)
                    yield (x, nextx)
                    x = nextx
                else:
                    yield (x, x + entries)
                    x += entries

        for entrystart, entryend, arrays in tree.iterator(ranges(), newtoget, executor=executor, outputtype=dict, reportentries=True):
            thisentries = entryend - entrystart

            if holdover is not None:
                arrays = dict((name, numpy.concatenate((oldarray, arrays[name]))) for name, oldarray in holdover.items())
                thisentries += holdoverentries
                holdover = None
                holdoverentries = 0

            if thisentries < entries:
                holdover = arrays
                holdoverentries = thisentries

            else:
                yield output(arrays, outerstart, outerstart + thisentries)
                outerstart = outerend = outerstart + thisentries

    if holdover is not None:
        yield output(arrays, outerstart, outerstart + thisentries)
