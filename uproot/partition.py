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

import sys
import glob
import json
import os.path
from collections import namedtuple
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import numpy

import uproot
import uproot.tree

class BasketData(object):
    """Holds some information about baskets for making a decision about where to stop growing a partition.

        * `path` local name or remote URL to the file.
        * `branchname` name of the branch to which this basket belongs.
        * `dtype` Numpy array type that this branch will be read out into; note that `dtype.itemsize` gives the item size in bytes.
        * `itemdims` tuple of fixed-width dimensions for the array (not counted in `dtype.itemsize`).
        * `entrystart` first entry number in this basket.
        * `entryend` last entry number in this basket plus one. (`numentries` is `entryend - entrystart`.)
        * `numbytes` size of this basket in bytes.
    """
    def __init__(self, path, branchname, dtype, itemdims, entrystart, entryend, numbytes):
        if hasattr(path, "encode"): path = path.encode("ascii")
        if hasattr(branchname, "encode"): branchname = branchname.encode("ascii")
        if not isinstance(dtype, numpy.dtype):
            dtype = numpy.dtype(dtype)
        itemdims = tuple(int(x) for x in itemdims)
        entrystart = int(entrystart)
        entryend = int(entryend)
        numbytes = int(numbytes)

        self.path = path
        self.branchname = branchname
        self.dtype = dtype
        self.itemdims = itemdims
        self.entrystart = entrystart
        self.entryend = entryend
        self.numbytes = numbytes

    def __eq__(self, other):
        return isinstance(other, BasketData) and self.path == other.path and self.branchname == other.branchname and self.dtype == other.dtype and self.itemdims == other.itemdims and self.entrystart == other.entrystart and self.entryend == other.entryend and self.numbytes == other.numbytes

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((BasketData, self.path, self.branchname, self.dtype, self.itemdims, self.entrystart, self.entryend, self.numbytes))

    @property
    def numentries(self):
        return self.entryend - self.entrystart

    def __repr__(self):
        return "BasketData({0}, {1}, {2}, {3}, {4}, {5}, {6})".format(repr(self.path), repr(self.branchname), self.dtype, self.itemdims, self.entrystart, self.entryend, self.numbytes)

class Range(object):
    """Represents an entry range in a file; part of a partition.

        * `path` local name or remote URL to the file.
        * `entrystart` the first entry in this range.
        * `entryend` the last entry in this range plus one. (`numentries` is `entryend - entrystart`.)
    """
    def __init__(self, path, entrystart, entryend):
        if hasattr(path, "encode"): path = path.encode("ascii")
        entrystart = int(entrystart)
        entryend = int(entryend)
        self.path = path
        self.entrystart = entrystart
        self.entryend = entryend

    def __eq__(self, other):
        return isinstance(other, Range) and self.path == other.path and self.entrystart == other.entrystart and self.entryend == other.entryend

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((Range, self.path, self.entrystart, self.entryend))

    @property
    def numentries(self):
        return self.entryend - self.entrystart

    def __repr__(self):
        return "Range({0}, {1}, {2})".format(repr(self.path), self.entrystart, self.entryend)

    def toJson(self):
        return {"path": self.path.decode("ascii"), "entrystart": self.entrystart, "entryend": self.entryend}

    @staticmethod
    def fromJson(obj):
        return Range(obj["path"], obj["entrystart"], obj["entryend"])

class Partition(object):
    """Represents a section of data (possibly crossing file boundaries) to be loaded as contiguous arrays.

        * `index` enumerates this partition; must be contiguous from zero (inclusive) to the PartitionSet's `numpartitions` (exclusive).
        * `ranges` entry ranges within separate files (a partition that doesn't cross file boundaries has exactly one range).
        * `numentries` is the number of entries (calculated from ranges).
    """
    def __init__(self, index, *ranges):
        assert len(ranges) > 0
        assert all(isinstance(x, Range) for x in ranges)

        self.index = index
        self.ranges = ranges

    def __eq__(self, other):
        return isinstance(other, Partition) and self.index == other.index and self.ranges == other.ranges

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((Partition, self.index, self.ranges))

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
    """Represents a way to partition a set of files into 

        * `treepath` is where to find the TTree in each ROOT file.
        * `branchdtypes` is a *dict* from branch name to Numpy array `dtype`.
        * `branchcounters` is a dict from branch name to counter branch name for those branches that have variable width per entry.
        * `branchdims` is a dict from branch name to fixed-width dimensions for those branches that have them.
        * `numpartitions` is the number of partitions as a cross-check on `len(partitions)`, as well as a quick way to get this information in JSON form.
        * `numentries` is the number of entries as a cross-check on `sum(x.numentries for x in partitions)`, as well as a quick way to get this information in JSON form.
        * `partitions` is a list of Partition objects.

    Use the `PartitionSet.fill` method to create a `PartitionSet` from a set of ROOT files and configurable constraints.

    Use the `iterator` function (in this module) to iterate over data described by a `PartitionSet`.

    To iterate over subsets of partitions or subsets of branches, create a short-lived `PartitionSet.Projection` using the `project` method and pass it to `iterator`.
    """

    def __init__(self, treepath, branchdtypes, branchcounters, branchdims, numpartitions, numentries, *partitions):
        assert len(partitions) > 0
        assert all(isinstance(x, Partition) for x in partitions)

        if not isinstance(branchdtypes, dict):
            raise TypeError("branchdtypes must be a dict for PartitionSet constructor")
        assert numpartitions == len(partitions)
        assert [x.index for x in partitions] == list(range(numpartitions))
        assert numentries == sum(x.numentries for x in partitions)

        lastpath = None
        for partition in partitions:
            for filerange in partition.ranges:
                if lastpath != filerange.path:
                    assert filerange.entrystart == 0
                else:
                    assert filerange.entrystart == last
                lastpath = filerange.path
                last = filerange.entryend

        if hasattr(treepath, "encode"): treepath = treepath.encode("ascii")
        branchdtypes = dict((b.encode("ascii") if hasattr(b, "encode") else b, d.encode("ascii") if hasattr(d, "encode") else d) for b, d in branchdtypes.items())
        branchcounters = dict((b.encode("ascii") if hasattr(b, "encode") else b, c.encode("ascii") if hasattr(c, "encode") else c) for b, c in branchcounters.items())
        branchdims = dict((b.encode("ascii") if hasattr(b, "encode") else b, tuple(int(x) for x in d)) for b, d in branchdims.items() if len(d) > 0)
        numpartitions = int(numpartitions)
        numentries = int(numentries)

        self.treepath = treepath
        self.branchdtypes = branchdtypes
        self.branchcounters = branchcounters
        self.branchdims = branchdims
        self.numpartitions = numpartitions
        self.numentries = numentries
        self.partitions = partitions

    def __eq__(self, other):
        return isinstance(other, PartitionSet) and self.treepath == other.treepath and self.branchdtypes == other.branchdtypes and self.branchcounters == other.branchcounters and self.branchdims == other.branchdims and self.numpartitions == other.numpartitions and self.numentries == other.numentries and self.partitions == other.partitions

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((PartitionSet, self.treepath, tuple(sorted(self.branchdtypes.items())), tuple(sorted(self.branchcounters.items())), tuple(sorted(self.branchdims.items())), self.numpartitions, self.numentries, self.partitions))

    def __repr__(self):
        return "<PartitionSet {0} with {1} branches and {2} partitions>".format(repr(self.treepath), len(self.branchdtypes), len(self.partitions))

    class Projection(object):
        def __init__(self, treepath, branchdtypes, *partitions):
            self.treepath = treepath
            self.branchdtypes = branchdtypes
            self.partitions = partitions

        def __eq__(self, other):
            return isinstance(other, PartitionSet.Projection) and self.treepath == other.treepath and self.branchdtypes == other.branchdtypes and self.partitions == other.partitions

        def __ne__(self, other):
            return not self.__eq__(other)

        def __hash__(self):
            return hash((PartitionSet.Projection, self.treepath, tuple(sorted(self.branchdtypes.items())), self.partitions))

        def __repr__(self):
            return "<PartitionSet.Projection {0} with {1} branches and {2} partitions>".format(repr(self.treepath), len(self.branchdtypes), len(self.partitions))

    def project(self, filterpartitions=None, filterbranches=None):
        """Get a `PartitionSet.Projection` to iterate over a subset of the data (subset of partitions, branches, or both).

        Arguments:

            * `filterpartitions`

              If `None` (default), keep all partitions.
              If a number, keep that partition index.
              If an iterable of numbers, keep those partition indexes.
              If a slice, keep the partition indexes in the slice range.
              If a single-argument function, pass the `Partition` objects to that function; partitions that return `True` will be kept.

            * `filterbranches`

              If `None` (default), keep all branches.
              If a string, keep that branch name.
              If an iterable of strings, keep those branch names.
              If a single-argument function, pass the branch names to that function; branches that return `True` will be kept.
              If a two-argument function, pass the branch names and dtypes to that function; branches that return `True` will be kept.

        The `PartitionSet.Projection` returned by this method can be used in place of a `PartitionSet` in this module's `iterator` function.
        """
        if filterpartitions is None:
            partitions = self.partitions

        elif callable(filterpartitions):
            partitions = tuple(p for p in self.partitions if filterpartitions(p))

        elif isinstance(filterpartitions, int):
            partitions = tuple(p for p in self.partitions if p.index == filterpartitions)

        elif isinstance(filterpartitions, slice):
            start = getattr(filterpartitions, "start", 0)
            stop = getattr(filterpartitions, "stop", len(self.partitions))
            step = getattr(filterpartitions, "step", 1)
            if step is None: step = 1
            partitions = tuple(p for p in self.partitions if start <= p.index < stop and (p.index - start) % step == 0)

        else:
            partitions = tuple(p for p in self.partitions if p.index in filterpartitions)

        if filterbranches is None:
            branchdtypes = self.branchdtypes

        elif callable(filterbranches) and filterbranches.__code__.co_argcount == 1:
            branchdtypes = dict((b, d) for b, d in self.branchdtypes.items() if filterbranches(b))

        elif callable(filterbranches) and filterbranches.__code__.co_argcount == 2:
            branchdtypes = dict((b, d) for b, d in self.branchdtypes.items() if filterbranches(b, d))

        elif (sys.version_info[0] <= 2 and isinstance(filterbranches, (unicode, str))) or (sys.version_info[0] > 2 and isinstance(filterbranches, (str, bytes))):
            if hasattr(filterbranches, "encode"):
                filterbranches = filterbranches.encode("ascii")
            branchdtypes = dict((b, d) for b, d in self.branchdtypes.items() if b == filterbranches)

        else:
            filterbranches = [x.encode("ascii") if hasattr(x, "encode") else x for x in filterbranches]
            branchdtypes = dict((b, d) for b, d in self.branchdtypes.items() if b in filterbranches)

        return self.Projection(self.treepath, branchdtypes, *partitions)

    def toJson(self):
        return {"treepath": self.treepath.decode("ascii"),
                "branchdtypes": dict((b.decode("ascii"), str(d)) for b, d in self.branchdtypes.items()),
                "branchcounters": dict((b.decode("ascii"), c.decode("ascii")) for b, c in self.branchcounters.items()),
                "branchdims": dict((b.decode("ascii"), d) for b, d in self.branchdims.items()),
                "numpartitions": self.numpartitions,
                "numentries": self.numentries,
                "partitions": [p.toJson() for p in self.partitions]}

    @staticmethod
    def fromJson(obj):
        return PartitionSet(obj["treepath"],
                            dict((b, numpy.dtype(d)) for b, d in obj["branchdtypes"].items()),
                            obj["branchcounters"],
                            dict((b, tuple(d)) for b, d in obj["branchdims"].items()),
                            obj["numpartitions"],
                            obj["numentries"],
                            *[Partition.fromJson(p) for p in obj["partitions"]])

    def toJsonString(self):
        return json.dumps(self.toJson())

    @staticmethod
    def fromJsonString(obj):
        return PartitionSet.fromJson(json.loads(obj))

    @staticmethod
    def fill(path, treepath, branchdtypes=lambda branch: getattr(branch, "dtype", None), by=lambda choices: min(choices, key=lambda x: x.numentries), under=lambda baskets: sum(x.numbytes for x in baskets) < 10*1024**2, memmap=True, debug=False):
        """Iterate over a set of ROOT files (reading only headers) to optimize a partitioning of the data.

        Returns:

            * a `PartitionSet` that can be saved as JSON and used to read data in optimally sized chunks.

        Arguments:

            * `path` *(required)*

              If a single string, the name of the file, possibly a URL for XRootD.
              If an iterable, a set of names or URLs.
              Local files can be glob patterns (`mydata*.root`).
              After expansion, paths will be traversed in *sorted* order. This is to ensure that entry numbers for the same file set have the same meaning from run to run.

            * `treepath` *(required)*

              A string describing the path through TDirectories (using '/' and ';' conventions) to the TTree of interest. Must be the same in all files.

            * `branchdtypes` (same as in `TTree.iterator`)

              If a single string, the string names the only branch to load.
              If an iterable of strings, all of these are loaded (in the specified order).
              If a dict of `{name: dtype}`, load the specified branch names and cast them into a given `dtype` (such as conversion to little endian).
              If a function from branch names to `dtype` or `None`, load the branches into the given `dtypes` and don't load the branches mapped to `None`.

            * `by` criterion by which data are partitioned; this function chooses from a set of options, passed as an argument.

              Default selects the option with the fewest entries.

                  def by(choices):
                      return min(choices, key=lambda x: x.numentries)

            * `under` criterion that stops growth of a partition for one branch; this function should return `True` or `False`, given a list of `BasketData`.

              Default stops growth before the number of bytes exceeds 10 MB.

                  def under(baskets):
                      return sum(x.numbytes for x in baskets) < 10*1024**2

            * `memmap` (same as in `uproot.open`)

              If `True`, load local files as memory maps. If `False`, load normally.
              The advantage of memory maps is that parallel reads only require one file handle, and random access (of which there is a *lot* in ROOT) is more efficient.
              The advantage of normal files is that memory maps sometimes load more data from disk than intended, which might (?) be a performance issue for slow disks.

            * `debug` if `debug` is `True`, this function prints out each `Partition` as it is created.            
        """
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

        paths = [x.encode("ascii") if hasattr(x, "encode") else x for x in paths]

        trees = {}
        trees[0] = uproot.open(paths[0], memmap=memmap)[treepath]
        toget = dict((b.name, d) for b, d in uproot.tree.TTree._normalizeselection(branchdtypes, trees[0].allbranches))
        counters = dict((countee, counter.branch) for countee, counter in trees[0].counter.items() if countee in toget)
        dims = dict((branch.name, branch.itemdims) for branch in trees[0].allbranches if branch.name in toget and branch.itemdims != ())
        def tree(i):
            if i not in trees:
                trees[i] = uproot.open(paths[i], memmap=memmap)[treepath]

                newtoget = dict((b.name, d) for b, d in uproot.tree.TTree._normalizeselection(branchdtypes, trees[i].allbranches))
                for key in set(toget.keys()).union(set(newtoget.keys())):
                    if key not in newtoget:
                        raise ValueError("branch {0} cannot be found in {1}, but it was in {2}".format(repr(key), repr(paths[i]), repr(paths[i - 1])))
                    if key not in toget:
                        del newtoget[key]
                    elif newtoget[key] != toget[key]:
                        raise ValueError("branch {0} is a {1} in {2}, but it was a {3} in {4}".format(repr(key), newtoget[key], repr(paths[i]), toget[key], repr(paths[i - 1])))

                newcounters = dict((countee, counter.branch) for countee, counter in trees[i].counter.items() if countee in toget)
                for key in set(counters.keys()).union(set(newcounters.keys())):
                    if key not in newcounters:
                        raise ValueError("branch {0} doesn't have a counter in {1}, but it was counted by {2} in {3}".format(repr(key), repr(paths[i]), repr(counters[key]), repr(paths[i - 1])))
                    if key not in counters:
                        raise ValueError("branch {0} is counted by {1} in {2}, but it wasn't counted {3}".format(repr(key), repr(newcounters[key]), repr(paths[i]), repr(paths[i - 1])))
                    elif newcounters[key] != counters[key]:
                        raise ValueError("branch {0} is counted by {1} in {2}, but it is counted by {3} in {4}".format(repr(key), repr(newcounters[key]), repr(paths[i]), repr(counters[key]), repr(paths[i - 1])))

                newdims = dict((branch.name, branch.itemdims) for branch in trees[i].allbranches if branch.name in toget and branch.itemdims != ())
                for key in set(dims.keys()).union(set(newdims.keys())):
                    if key not in newdims:
                        raise ValueError("branch {0} doesn't have dimensions in {1}, but it had dimensions {2} in {3}".format(repr(key), repr(paths[i]), repr(dims[key]), repr(paths[i - 1])))
                    if key not in dims:
                        raise ValueError("branch {0} has dimensions {1} in {2}, but it didn't have dimensions in {3}".format(repr(key), repr(newdims[key]), repr(paths[i]), repr(paths[i - 1])))
                    elif newdims[key] != dims[key]:
                        raise ValueError("branch {0} has dimensions {1} in {2}, but it had dimensions {3} in {4}".format(repr(key), repr(newdims[key]), repr(paths[i]), repr(dims[key]), repr(paths[i - 1])))

            return trees[i]

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
                                                 branch.itemdims,
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
                    if len(ranges) == 0:
                        # this might be the first basket to go into a range
                        if len(partitions) == 0:
                            # this is the first basket/range/partition ever
                            ranges.append(Range(basketdatum.path, basketdatum.entrystart, basketdatum.entryend))
                            ranges[-1]._pathi = basketdatum._pathi

                        elif partitions[-1].ranges[-1]._pathi == basketdatum._pathi:
                            # this is a continuation of the same file from a previous partition
                            if partitions[-1].ranges[-1].entryend < basketdatum.entryend:
                                # the first basket extends beyond the last entry in the last partition; include only the new stuff
                                ranges.append(Range(basketdatum.path, partitions[-1].ranges[-1].entryend, basketdatum.entryend))
                                ranges[-1]._pathi = basketdatum._pathi
                            else:
                                # the first basket is contained within the previous partition
                                pass

                        else:
                            # this is a new file, not seen in previous partitions
                            ranges.append(Range(basketdatum.path, basketdatum.entrystart, basketdatum.entryend))
                            ranges[-1]._pathi = basketdatum._pathi

                    else:
                        # this is not the first basket
                        if ranges[-1]._pathi == basketdatum._pathi:
                            # continuation of the same file
                            ranges[-1].entryend = basketdatum.entryend
                        else:
                            # new file
                            ranges.append(Range(basketdatum.path, basketdatum.entrystart, basketdatum.entryend))
                            ranges[-1]._pathi = basketdatum._pathi

                possiblenext.append(Partition(partitioni, *ranges))

            partitions.append(by(possiblenext))
            if debug:
                print(partitions[-1])

            for todrop in set(pathi for pathi in trees if pathi < partitions[-1].ranges[0]._pathi):
                del trees[todrop]

            partitioni += 1

        return PartitionSet(treepath, toget, counters, dims, len(partitions), sum(x.numentries for x in partitions), *partitions)

def iterator(partitionset, memmap=True, executor=None):
    """Iterates over a collection of files, yielding arrays for each partition in a given `PartitionSet` (even across the gap between files).

    Arguments:

        * a `PartitionSet` declaring the file and tree paths from which to get data as well as the entries to use as boundaries.

        * `memmap` (same as in `uproot.open`)

          If `True`, load local files as memory maps. If `False`, load normally.
          The advantage of memory maps is that parallel reads only require one file handle, and random access (of which there is a *lot* in ROOT) is more efficient.
          The advantage of normal files is that memory maps sometimes load more data from disk than intended, which might (?) be a performance issue for slow disks.

        * `executor` (same as in `TTree.iterator`)

          A `concurrent.futures.Executor` that would be used to parallelize the basket loading/decompression.
          If `None`, the process is serial.
    """
    treedata = {}
    def complete(nextpartition):
        for filerange in partitionset.partitions[nextpartition].ranges:
            if filerange.path not in treedata or not any(entrystart == filerange.entrystart and entryend == filerange.entryend for entrystart, entryend, arrays in treedata[filerange.path]):
                return False
        return True

    def output(nextpartition):
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

        return outarrays
        
    oldpath = None
    nextpartition = 0
    for partition in partitionset.partitions:
        for filerange in partition.ranges:
            if oldpath != filerange.path:
                if oldpath is not None:
                    treedata[oldpath] = list(tree.iterator(entries, partitionset.branchdtypes, executor=executor, outputtype=dict, reportentries=True))
                tree = uproot.open(filerange.path, memmap=memmap)[partitionset.treepath]
                entries = []
            entries.append((filerange.entrystart, filerange.entryend))
            oldpath = filerange.path

        while nextpartition < len(partitionset.partitions):
            if not complete(nextpartition):
                break
            else:
                yield output(nextpartition)
                nextpartition += 1

    if oldpath is not None:
        treedata[oldpath] = list(tree.iterator(entries, partitionset.branchdtypes, executor=executor, outputtype=dict, reportentries=True))

    while nextpartition < len(partitionset.partitions):
        if not complete(nextpartition):
            break
        else:
            yield output(nextpartition)
            nextpartition += 1
