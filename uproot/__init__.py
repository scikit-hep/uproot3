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

del uproot

def open(path, memmap=True):
    """Opens a single file for reading.

    Arguments:

        * `path`

          The name of the file, possibly a URL for XRootD.

        * `memmap` (same as in `uproot.iterator`)

          If `True`, load local files as memory maps. If `False`, load normally.
          The advantage of memory maps is that parallel reads only require one file handle, and random access (of which there is a *lot* in ROOT) is more efficient.
          The advantage of normal files is that memory maps sometimes load more data from disk than intended, which might (?) be a performance issue for slow disks.
    """
    try:
        from urlparse import urlparse
    except ImportError:
        from urllib.parse import urlparse
    import uproot.rootio

    parsed = urlparse(path)
    if parsed.scheme == "file" or parsed.scheme == "":
        path = parsed.netloc + parsed.path
        if memmap:
            import uproot._walker.arraywalker
            return uproot.rootio.TFile(uproot._walker.arraywalker.ArrayWalker.memmap(path))
        else:
            import uproot._walker.localfilewalker
            return uproot.rootio.TFile(uproot._walker.localfilewalker.LocalFileWalker(path))

    elif parsed.scheme == "root":
        return xrootd(path)

    else:
        raise ValueError("URI scheme not recognized: {0}".format(path))

def xrootd(path):
    """Opens a single remote file for reading.

    Although `uproot.open` will use XRootD when it encounters a URL, this function *always* invokes XRootD.
    """
    import uproot._walker.xrootdwalker
    import uproot.rootio
    return uproot.rootio.TFile(uproot._walker.xrootdwalker.XRootDWalker(path))

def iterator(entries, path, treepath, branchdtypes=lambda branch: branch.dtype, memmap=True, executor=None, outputtype=dict, reportentries=False):
    """Iterates over a collection of files, a fixed number of entries at a time (even across the gap between files).

    Use this function when you have a huge dataset, too large to load into memory, spread across many files. Example use:

        for px, py in uproot.iterator(10000, "/bigdisk/mydata*.root", "events", ["px", "py"], outputtype=tuple):
            do_something(sqrt(px**2 + py**2))

    Arguments:

        * `entries` *(required)*

          If a positive integer, the number of entries to yield in each step of iteration.
          Otherwise, `entries` is interpreted as an iterable over `(entrystart, entryend)` ranges, which must be strictly increasing.

        * `path` *(required)*

          If a single string, the name of the file, possibly a URL for XRootD.
          If an iterable, a set of names or URLs.
          Local files can be glob patterns (`mydata*.root`).
          After expansion, paths will be traversed in *sorted* order. This is to ensure that entry numbers for the same file set have the same meaning from run to run.

        * `branchdtypes` (same as in `TTree.iterator`)

          If a single string, the string names the only branch to load.
          If an iterable of strings, all of these are loaded (in the specified order).
          If a dict of `{name: dtype}`, load the specified branch names and cast them into a given `dtype` (such as conversion to little endian).
          If a function from branch names to `dtype` or `None`, load the branches into the given `dtypes` and don't load the branches mapped to `None`.

        * `memmap` (same as in `uproot.open`)

          If `True`, load local files as memory maps. If `False`, load normally.
          The advantage of memory maps is that parallel reads only require one file handle, and random access (of which there is a *lot* in ROOT) is more efficient.
          The advantage of normal files is that memory maps sometimes load more data from disk than intended, which might (?) be a performance issue for slow disks.

        * `executor` (same as in `TTree.iterator`)

          A `concurrent.futures.Executor` that would be used to parallelize the basket loading/decompression.
          If `None`, the process is serial.

        * `outputtype` (same as in `TTree.iterator`)

          Constructor for the objects to yield in the iterator. Good choices include `dict`, `tuple`, `namedtuple`, `list`.

        * `reportentries`

          If `True`, yield `(entrystart, entryend, data)` instead of just `data`. Intended as a convenience or cross-check for analysis.
          These are not entry numbers in any one file, they're global numbers for the whole set of files (much like TChain in ROOT).
    """
    import sys
    import glob
    import os.path
    from collections import namedtuple
    try:
        from urlparse import urlparse
    except ImportError:
        from urllib.parse import urlparse
    import numpy
    import uproot.tree

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
            while x < tree.numentries:
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
