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
    def __init__(self, numentries, numbytes):
        self.numentries = numentries
        self.numbytes = numbytes

    def __repr__(self):
        return "BasketData({0}, {1})".format(numentries, numbytes)

class TreeData(object):
    def __init__(self, filepath, basketdata):
        self.filepath = filepath
        self.basketdata = basketdata

    def __repr__(self):
        return "TreeData({0}, {1})".format(repr(self.filepath), self.basketdata)

class FilesetData(object):
    def __init__(self, treepath, allbranchtypes, counter, trees):
        self.treepath = treepath
        self.allbranchtypes = allbranchtypes
        self.counter = counter
        self.trees = trees

    def __repr__(self):
        return "FilesetData({0}, {1}, {2}, {3})".format(repr(self.treepath), self.allbranchtypes, self.counter, self.trees)

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
        return "Partition({0})".format(", ".join(self.fileranges))

def basketdata(path, treepath, branchdtypes=lambda branch: getattr(branch, "dtype", None), memmap=True):
    pass



def partition(path, treepath, by=lambda choices: min(choices, key=lambda x: x.numentries), constraint=lambda baskets: sum(x.numbytes for x in baskets) < 10**1024**2):
    pass
    # if hasattr(path, "decode"):
    #     path = path.decode("ascii")

    # def explode(x):
    #     parsed = urlparse(x)
    #     if parsed.scheme == "file" or parsed.scheme == "":
    #         return sorted(glob.glob(os.path.expanduser(parsed.netloc + parsed.path)))
    #     else:
    #         return [x]

    # if (sys.version_info[0] <= 2 and isinstance(path, unicode)) or \
    #    (sys.version_info[0] > 2 and isinstance(path, str)):
    #     paths = explode(path)
    # else:
    #     paths = [y for x in path for y in explode(x)]

    # trees = {}
    # def tree(i):
    #     if i not in trees:
    #         trees[i] = uproot.open(paths[i], memmap=memmap)
    #     return trees[i]

    

