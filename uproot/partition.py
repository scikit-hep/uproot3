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

import sys
import glob
import os.path
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
import numpy

import uproot
import uproot.tree

class BasketData(object):
    def __init__(self, path, branchname, dtype, entrystart, entryend, numbytes):
        self.path = path
        self.branchname = branchname
        self.dtype = dtype
        self.entrystart = entrystart
        self.entryend = entryend
        self.numbytes = numbytes

    @property
    def numentries(self):
        return self.entryend - self.entrystart

    def __repr__(self):
        return "BasketData({0}, {1}, {2}, {3}, {4} {5})".format(repr(self.path), repr(self.branchname), self.dtype, self.entrystart, self.entryend, self.numbytes)

class FileRange(object):
    def __init__(self, path, entrystart, entryend):
        self.path = path
        self.entrystart = entrystart
        self.entryend = entryend

    @property
    def numentries(self):
        return self.entryend - self.entrystart

    def __repr__(self):
        return "FileRange({0}, {1}, {2})".format(repr(self.path), self.entrystart, self.entryend)

class Partition(object):
    def __init__(self, *fileranges):
        self.fileranges = fileranges

    @property
    def numentries(self):
        return sum(x.numentries for x in self.fileranges)

    def __repr__(self):
        return "Partition({0})".format(", ".join(map(repr, self.fileranges)))

def partition(path, treepath, branchdtypes=lambda branch: getattr(branch, "dtype", None), by=lambda choices: min(choices, key=lambda x: x.numentries), under=lambda baskets: sum(x.numbytes for x in baskets) < 10*1024**2, memmap=True):
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

    toget = {}
    trees = {}
    def tree(i):
        if i not in trees:
            trees[i] = uproot.open(paths[i], memmap=memmap)[treepath]

            newtoget = dict((b.name, d) for b, d in uproot.tree.TTree._normalizeselection(branchdtypes, trees[i].allbranches))
            if len(toget) != 0:
                for key in set(toget.keys()).union(set(newtoget.keys())):
                    if key not in newtoget:
                        raise ValueError("branch {0} cannot be found in {1}, but it was in {2}".format(repr(key), repr(paths[i]), repr(paths[i - 1])))
                    if key not in toget:
                        del newtoget[key]
                    elif newtoget[key] != newtoget[key]:
                        raise ValueError("branch {0} is a {1} in {2}, but it was a {3} in {4}".format(repr(key), newtoget[key], repr(paths[i]), toget[key], repr(paths[i - 1])))
            if len(toget) == 0:
                toget.update(newtoget)

        return trees[i]

    tree(0)
    lastpartition = None
    while lastpartition is None or lastpartition.fileranges[-1].path != paths[-1] or lastpartition.fileranges[-1].entryend < tree(len(paths) - 1).numentries:
        possiblenext = []
        for branchname, dtype in toget.items():
            # start this branch where the global partitioning process left off
            if lastpartition is None:
                pathi = 0
                basketi = 0
                entryi = 0
                branch = tree(pathi)[branchname]
            else:
                pathi = lastpartition.fileranges[-1]._pathi
                entryi = lastpartition.fileranges[-1].entryend
                branch = tree(pathi)[branchname]
                for basketi in range(branch.numbaskets):
                    if basketi + 1 == branch.numbaskets or branch.basketstart(basketi + 1) > entryi:
                        break

            # accumulate until the constraint is satisfied
            basketdata = []
            while True:
                if basketi >= branch.numbaskets:
                    pathi += 1
                    basketi = 0
                    if pathi >= len(paths):
                        break
                    else:
                        basket = tree(pathi)[branchname]

                basketdata.append(BasketData(paths[pathi],
                                             branchname,
                                             dtype,
                                             branch.basketstart(basketi),
                                             branch.basketstart(basketi) + branch.basketentries(basketi),
                                             branch.basketbytes(basketi)))
                basketdata[-1]._pathi = pathi

                if not under(basketdata):
                    basketdata.pop()
                    break
                else:
                    basketi += 1

            if len(basketdata) == 0:
                raise ValueError("branch {0} starting at entry {1} in file {2} cannot satisfy the constraint".format(repr(branchname), entryi, repr(paths[pathi])))

            # create a possible partition
            fileranges = []
            for basketdatum in basketdata:
                if len(fileranges) == 0 or fileranges[-1]._pathi != basketdatum._pathi:
                    fileranges.append(FileRange(basketdatum.path, basketdatum.entrystart, basketdatum.entryend))
                    fileranges[-1]._pathi = basketdatum._pathi
                else:
                    fileranges[-1].entryend = basketdatum.entryend

            if lastpartition is not None:
                if lastpartition.fileranges[-1]._pathi == fileranges[0]._pathi:
                    fileranges[0].entrystart = lastpartition.fileranges[-1].entryend
                else:
                    fileranges[0].entrystart = 0

            possiblenext.append(Partition(*fileranges))

        lastpartition = by(possiblenext)

        for todrop in set(pathi for pathi in trees if pathi < lastpartition.fileranges[0]._pathi):
            del trees[todrop]

        yield lastpartition
