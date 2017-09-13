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

def xrootd(remotepath):
    raise NotImplementedError
