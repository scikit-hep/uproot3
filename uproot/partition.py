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
import json
import os.path
from collections import namedtuple
from collections import OrderedDict
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

class Range(object):
    def __init__(self, path, entrystart, entryend):
        self.path = path
        self.entrystart = entrystart
        self.entryend = entryend

    @property
    def numentries(self):
        return self.entryend - self.entrystart

    def __repr__(self):
        return "Range({0}, {1}, {2})".format(repr(self.path), self.entrystart, self.entryend)

    def toJson(self):
        return {"path": self.path, "entrystart": self.entrystart, "entryend": self.entryend}

    @staticmethod
    def fromJson(obj):
        return Range(obj["path"], obj["entrystart"], obj["entryend"])

class Partition(object):
    def __init__(self, index, *ranges):
        self.index = index
        self.ranges = ranges

    @property
    def numentries(self):
        return sum(x.numentries for x in self.ranges)

    def __repr__(self):
        return "Partition({0}, {1})".format(self.index, ", ".join(map(repr, self.ranges)))

    def toJson(self):
        return {"index": self.index, "ranges": [x.toJson() for x in self.ranges]}

    @staticmethod
    def fromJson(obj):
        return Partition(obj["index"], *[Range.fromJson(x) for x in obj["ranges"]])

class PartitionSet(object):
    def __init__(self, treepath, branchdtypes, *partitions):
        if not isinstance(branchdtypes, dict):
            raise TypeError("branchdtypes must be a dict for PartitionSet constructor")

        self.treepath = treepath
        self.branchdtypes = branchdtypes
        self.partitions = partitions

    def __repr__(self):
        return "<PartitionSet len={0}>".format(len(self.partitions))

    @property
    def numentries(self):
        return sum(x.numentries for x in self.partitions)

    def toJson(self):
        return {"treepath": self.treepath,
                "branchdtypes": dict((b, str(d)) for b, d in branchdtypes.items()),
                "partitions": [p.toJson() for p in self.partitions]}

    @staticmethod
    def fromJson(obj):
        return PartitionSet(obj["treepath"],
                            dict((b, numpy.dtype(d)) for b, d in obj["branchdtypes"]),
                            [Partition.fromJson(p) for p in obj["partitions"]])

    def toJsonString(self):
        return json.dumps(self.toJson())

    @staticmethod
    def fromJsonString(obj):
        return PartitionSet.fromJson(json.loads(obj))

    @staticmethod
    def fill(path, treepath, branchdtypes=lambda branch: getattr(branch, "dtype", None), by=lambda choices: min(choices, key=lambda x: x.numentries), under=lambda baskets: sum(x.numbytes for x in baskets) < 10*1024**2, memmap=True, debug=False):
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
        partitions = []
        partitioni = 0
        while len(partitions) == 0 or partitions[-1].ranges[-1].path != paths[-1] or partitions[-1].ranges[-1].entryend < tree(len(paths) - 1).numentries:
            possiblenext = []
            for branchname, dtype in toget.items():
                # start this branch where the global partitioning process left off
                if len(partitions) == 0:
                    pathi = 0
                    basketi = 0
                    entryi = 0
                    branch = tree(pathi)[branchname]
                else:
                    pathi = partitions[-1].ranges[-1]._pathi
                    entryi = partitions[-1].ranges[-1].entryend
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

                    for basketdatum in basketdata:
                        assert basketdatum.entrystart != basketdatum.entryend

                    if not under(basketdata):
                        basketdata.pop()
                        break
                    else:
                        basketi += 1

                if len(basketdata) == 0:
                    raise ValueError("branch {0} starting at entry {1} in file {2} cannot satisfy the constraint".format(repr(branchname), entryi, repr(paths[pathi])))

                # create a possible partition
                ranges = []
                for basketdatum in basketdata:
                    if len(ranges) == 0 or ranges[-1]._pathi != basketdatum._pathi:
                        ranges.append(Range(basketdatum.path, basketdatum.entrystart, basketdatum.entryend))
                        ranges[-1]._pathi = basketdatum._pathi
                    else:
                        ranges[-1].entryend = basketdatum.entryend

                if len(partitions) != 0:
                    if partitions[-1].ranges[-1]._pathi == ranges[0]._pathi:
                        ranges[0].entrystart = partitions[-1].ranges[-1].entryend
                    else:
                        ranges[0].entrystart = 0

                possiblenext.append(Partition(partitioni, *filter(lambda r: r.entrystart != r.entryend, ranges)))

            partitions.append(by(possiblenext))
            if debug:
                print(partitions[-1])

            for todrop in set(pathi for pathi in trees if pathi < partitions[-1].ranges[0]._pathi):
                del trees[todrop]

            partitioni += 1

        return PartitionSet(treepath, toget, *partitions)

def iterator(partitionset, memmap=True, executor=None, outputtype=dict):
    if outputtype == namedtuple:
        outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, dtype, cache in partitionset.branchdtypes])

    def output(arrays):
        if outputtype == dict or outputtype == OrderedDict:
            return arrays
        elif issubclass(outputtype, dict):
            return outputtype(arrays.items())
        elif outputtype == tuple or outputtype == list:
            return outputtype(arrays.values())
        else:
            return outputtype(*arrays.values())

    oldpath = None
    treedata = {}
    nextpartition = 0
    for partition in partitionset.partitions:
        for filerange in partition.ranges:
            if oldpath != filerange.path:
                if oldpath is not None:
                    treedata[oldpath] = list(tree.iterator(entries, partitionset.branchdtypes, executor=executor, outputtype=OrderedDict, reportentries=True))
                tree = uproot.open(filerange.path, memmap=memmap)[partitionset.treepath]
                entries = []
            entries.append((filerange.entrystart, filerange.entryend))
            oldpath = filerange.path

        while True:
            complete = True
            for filerange in partitionset.partitions[nextpartition].ranges:
                if filerange.path not in treedata or not any(entrystart == filerange.entrystart and entryend == filerange.entryend for entrystart, entryend, arrays in treedata[filerange.path]):
                    complete = False
                    break

            if not complete:
                break
            else:
                arraylists = dict((x, []) for x in partitionset.branchdtypes)
                for filerange in partitionset.partitions[nextpartition].ranges:
                    for used, (entrystart, entryend, arrays) in enumerate(treedata[filerange.path]):
                        if filerange.entrystart == entrystart and filerange.entryend == entryend:
                            for name, array in arrays.items():
                                arraylists[name].append(array)
                            break
                    treedata[filerange.path] = treedata[filerange.path][used + 1:]
                    if len(treedata[filerange.path]) == 0:
                        del treedata[filerange.path]

                outarrays = {}
                for name, arraylist in arraylists.items():
                    if len(arraylist) == 0:
                        outarrays[name] = numpy.array([], dtype=partitionset.branchdtypes[name])
                    elif len(arraylist) == 1:
                        outarrays[name] = arraylist[0]
                    else:
                        outarrays[name] = numpy.concatenate(arraylist)

                nextpartition += 1
                yield output(outarrays)


