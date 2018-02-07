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

import base64
import glob
import inspect
import numbers
import os.path
import struct
import sys
import threading
import warnings
from collections import namedtuple
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
try:
    from collections import OrderedDict
except ImportError:
    # simple OrderedDict implementation for Python 2.6
    class OrderedDict(dict):
        def __init__(self, items=(), **kwds):
            items = list(items)
            self._order = [k for k, v in items] + [k for k, v in kwds.items()]
            super(OrderedDict, self).__init__(items)
        def keys(self):
            return self._order
        def values(self):
            return [self[k] for k in self._order]
        def items(self):
            return [(k, self[k]) for k in self._order]
        def __setitem__(self, name, value):
            if name not in self._order:
                self._order.append(name)
            super(OrderedDict, self).__setitem__(name, value)
        def __delitem__(self, name):
            if name in self._order:
                self._order.remove(name)
            super(OrderedDict, self).__delitem__(name)
        def __repr__(self):
            return "OrderedDict([{0}])".format(", ".join("({0}, {1})".format(repr(k), repr(v)) for k, v in self.items()))

import numpy

import uproot.rootio
from uproot.rootio import _bytesid
from uproot.rootio import nofilter
from uproot.interp.auto import interpret
from uproot.interp.jagged import asjagged
from uproot.interp.numerical import asdtype
from uproot.source.cursor import Cursor
from uproot.source.memmap import MemmapSource
from uproot.source.xrootd import XRootDSource

if sys.version_info[0] <= 2:
    string_types = (unicode, str)
else:
    string_types = (str, bytes)

def _delayedraise(excinfo):
    if excinfo is not None:
        cls, err, trc = excinfo
        if sys.version_info[0] <= 2:
            exec("raise cls, err, trc")
        else:
            raise err.with_traceback(trc)

################################################################ high-level interface

def iterate(path, treepath, branches=None, entrysteps=None, outputtype=dict, reportentries=False, cache=None, basketcache=None, keycache=None, executor=None, blocking=True, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, **options):
    for tree, newbranches, globalentrystart in _iterate(path, treepath, branches, localsource, xrootdsource, **options):
        for start, stop, arrays in tree.iterate(branches=newbranches, entrysteps=entrysteps, outputtype=outputtype, reportentries=True, entrystart=0, entrystop=tree.numentries, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking):
            if reportentries:
                yield globalentrystart + start, globalentrystart + stop, arrays
            else:
                yield arrays
        
def _iterate(path, treepath, branches, localsource, xrootdsource, **options):
    def explode(x):
        parsed = urlparse(x)
        if _bytesid(parsed.scheme) == b"file" or len(parsed.scheme) == 0:
            return sorted(glob.glob(os.path.expanduser(parsed.netloc + parsed.path)))
        else:
            return [x]

    if isinstance(path, string_types):
        paths = explode(path)
    else:
        paths = [y for x in path for y in explode(x)]

    oldpath = None
    oldbranches = None
    holdover = None
    holdoverentries = 0
    outerstart = 0
    globalentrystart = 0
    for path in paths:
        tree = uproot.rootio.open(path, localsource=localsource, xrootdsource=xrootdsource, **options)[treepath]
        listbranches = list(tree._normalize_branches(branches))

        newbranches = OrderedDict((branch.name, interpretation) for branch, interpretation in listbranches)
        if oldbranches is not None:
            for key in set(oldbranches.keys()).union(set(newbranches.keys())):
                if key not in newbranches:
                    raise ValueError("branch {0} cannot be found in {1}, but it was in {2}".format(repr(key), repr(path), repr(oldpath)))
                if key not in oldbranches:
                    del newbranches[key]
                elif not newbranches[key].compatible(oldbranches[key]):
                    raise ValueError("branch {0} interpreted as {1} in {2}, but as {3} in {4}".format(repr(key), newbranches[key], repr(path), oldbranches[key], repr(oldpath)))

        oldpath = path
        oldbranches = newbranches

        yield tree, newbranches, globalentrystart
        globalentrystart += tree.numentries

################################################################ methods for TTree

class TTreeMethods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    _copycontext = True

    def _attachstreamer(self, branch, streamer, streamerinfosmap):
        if streamer is None:
            return

        elif isinstance(streamer, uproot.rootio.TStreamerInfo):
            if len(streamer.fElements) == 1 and isinstance(streamer.fElements[0], uproot.rootio.TStreamerBase) and streamer.fElements[0].fName == b"TObjArray":
                if streamer.fName == b"TClonesArray":
                    return self._attachstreamer(branch, streamerinfosmap.get(branch.fClonesName, None), streamerinfosmap)
                else:
                    # FIXME: can only determine streamer by reading some values?
                    return

            elif len(streamer.fElements) == 1 and isinstance(streamer.fElements[0], uproot.rootio.TStreamerSTL) and streamer.fElements[0].fName == b"This":
                return self._attachstreamer(branch, streamer.fElements[0], streamerinfosmap)

        branch._streamer = streamer

        digDeeperTypes = (uproot.rootio.TStreamerObject, uproot.rootio.TStreamerObjectAny, uproot.rootio.TStreamerObjectPointer, uproot.rootio.TStreamerObjectAnyPointer)

        members = None
        if isinstance(streamer, uproot.rootio.TStreamerInfo):
            members = streamer.members
        elif isinstance(streamer, digDeeperTypes):
            typename = streamer.fTypeName.rstrip(b"*")
            if typename in streamerinfosmap:
                members = streamerinfosmap[typename].members
        elif isinstance(streamer, uproot.rootio.TStreamerSTL):
            try:
                # FIXME: string manipulation only works for one-parameter templates
                typename = streamer.fTypeName[streamer.fTypeName.index(b"<") + 1 : streamer.fTypeName.rindex(b">")].rstrip(b"*")
            except ValueError:
                pass
            else:
                if typename in streamerinfosmap:
                    members = streamerinfosmap[typename].members

        if members is not None:
            for subbranch in branch.fBranches:
                name = subbranch.fName
                if name.startswith(branch.fName + b"."):           # drop parent branch's name
                    name = name[len(branch.fName) + 1:]

                submembers = members
                while True:                                        # drop nested struct names one at a time
                    try:
                        index = name.index(b".")
                    except ValueError:
                        break
                    else:
                        base, name = name[:index], name[index + 1:]
                        if base in submembers and isinstance(submembers[base], digDeeperTypes):
                            submembers = streamerinfosmap[submembers[base].fTypeName.rstrip(b"*")].members

                try:
                    name = name[:name.index(b"[")]
                except ValueError:
                    pass

                self._attachstreamer(subbranch, submembers.get(name, None), streamerinfosmap)

    def _postprocess(self, source, cursor, context):
        context.treename = self.name
        for branch in self.fBranches:
            self._attachstreamer(branch, context.streamerinfosmap.get(getattr(branch, "fClassName", None), None), context.streamerinfosmap)
        
    @property
    def name(self):
        return self.fName

    @property
    def title(self):
        return self.fTitle

    @property
    def numentries(self):
        return self.fEntries

    def iterkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        for branch in self.itervalues(recursive, filtername, filtertitle):
            yield branch.name

    def itervalues(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        for branch in self.fBranches:
            if filtername(branch.name) and filtertitle(branch.title):
                yield branch
            if recursive:
                for x in branch.itervalues(recursive, filtername, filtertitle):
                    yield x

    def iteritems(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        for branch in self.fBranches:
            if filtername(branch.name) and filtertitle(branch.title):
                yield branch.name, branch
            if recursive:
                for x in branch.iteritems(recursive, filtername, filtertitle):
                    yield x

    def keys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.iterkeys(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def values(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.itervalues(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def items(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.iteritems(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def allkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return self.keys(recursive=True, filtername=filtername, filtertitle=filtertitle)

    def allvalues(self, filtername=nofilter, filtertitle=nofilter):
        return self.values(recursive=True, filtername=filtername, filtertitle=filtertitle)

    def allitems(self, filtername=nofilter, filtertitle=nofilter):
        return self.items(recursive=True, filtername=filtername, filtertitle=filtertitle)

    def get(self, name):
        name = _bytesid(name)
        for branch in self.values():
            if branch.name == name:
                return branch
            try:
                return branch.get(name)
            except KeyError:
                pass
        raise KeyError("not found: {0}".format(repr(name)))

    def __contains__(self, name):
        try:
            self.get(name)
        except KeyError:
            return False
        else:
            return True

    def clusters(self, branches=None, entrystart=None, entrystop=None, strict=False):
        branches = list(self._normalize_branches(branches))

        if len(branches) == 0:
            yield self._normalize_entrystartstop(entrystart, entrystop)

        else:
            # convenience class; simplifies presentation of the algorithm
            class BranchCursor(object):
                def __init__(self, branch):
                    self.branch = branch
                    self.basketstart = 0
                    self.basketstop = 0
                @property
                def entrystart(self):
                    return self.branch.basket_entrystart(self.basketstart)
                @property
                def entrystop(self):
                    return self.branch.basket_entrystop(self.basketstop)

            cursors = [BranchCursor(branch) for branch, interpretation in branches]

            # everybody starts at the same entry number; if there is no such place before someone runs out of baskets, there will be an exception
            leadingstart = max(cursor.entrystart for cursor in cursors)
            while not all(cursor.entrystart == leadingstart for cursor in cursors):
                for cursor in cursors:
                    while cursor.entrystart < leadingstart:
                        cursor.basketstart += 1
                        cursor.basketstop += 1
                leadingstart = max(cursor.entrystart for cursor in cursors)

            entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)

            # move all cursors forward, yielding a (start, stop) pair if their baskets line up
            while any(cursor.basketstop < cursor.branch.numbaskets for cursor in cursors):
                # move all subleading baskets forward until they are no longer subleading
                leadingstop = max(cursor.entrystop for cursor in cursors)
                for cursor in cursors:
                    while cursor.entrystop < leadingstop:
                        cursor.basketstop += 1

                # if they all line up, this is a good cluster
                if all(cursor.entrystop == leadingstop for cursor in cursors):
                    # check to see if it's within the bounds the user requested (strictly or not strictly)
                    if strict:
                        if entrystart <= leadingstart and leadingstop <= entrystop:
                            yield leadingstart, leadingstop
                    else:
                        if entrystart < leadingstop and leadingstart < entrystop:
                            yield leadingstart, leadingstop

                    # anyway, move all the starts to the new stopping position and move all stops forward by one
                    leadingstart = leadingstop
                    for cursor in cursors:
                        cursor.basketstart = cursor.basketstop
                        cursor.basketstop += 1

                # stop iterating if we're past all acceptable clusters
                if leadingstart >= entrystop:
                    break

    def array(self, branch, interpretation=None, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        return self.get(branch).array(interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking)

    def lazyarray(self, branch, interpretation=None, cache=None, basketcache=None, keycache=None, executor=None):
        return self.get(branch).lazyarray(interpretation=interpretation, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor)

    def arrays(self, branches=None, outputtype=dict, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        branches = list(self._normalize_branches(branches))

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])

        futures = [(branch.name, branch.array(interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=False)) for branch, interpretation in branches]

        if issubclass(outputtype, dict):
            def wait():
                return outputtype([(name, future()) for name, future in futures])
        elif outputtype == tuple or outputtype == list:
            def wait():
                return outputtype([future() for name, future in futures])
        else:
            def wait():
                return outputtype(*[future() for name, future in futures])

        if blocking:
            return wait()
        else:
            return wait
        
    def lazyarrays(self, branches=None, outputtype=dict, cache=None, basketcache=None, keycache=None, executor=None):
        branches = list(self._normalize_branches(branches))

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])

        lazyarrays = [(branch.name, branch.lazyarray(interpretation=interpretation, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor)) for branch, interpretation in branches]

        if issubclass(outputtype, dict):
            return outputtype(lazyarrays)
        elif outputtype == tuple or outputtype == list:
            return outputtype([lazyarray for name, lazyarray in lazyarrays])
        else:
            return outputtype(*[lazyarray for name, lazyarray in lazyarrays])

    def iterate(self, branches=None, entrysteps=None, outputtype=dict, reportentries=False, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)

        if entrysteps is None:
            entrysteps = self.clusters(branches, entrystart=entrystart, entrystop=entrystop, strict=False)

        elif isinstance(entrysteps, numbers.Integral):
            entrystepsize = entrysteps
            if entrystepsize <= 0:
                raise ValueError("if an integer, entrysteps must be positive")
            
            def startstop():
                start = entrystart
                while start < entrystop and start < self.numentries:
                    stop = min(start + entrystepsize, entrystop)
                    yield start, stop
                    start = stop
            entrysteps = startstop()

        else:
            try:
                iter(entrysteps)
            except TypeError:
                raise TypeError("entrysteps must be None for cluster iteration, a positive integer for equal steps in number of entries, or an iterable of 2-tuples for explicit entry starts (inclusive) and stops (exclusive)")

        branches = list(self._normalize_branches(branches))

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])

        branchinfo = [(branch, interpretation, branch._basket_itemoffset(interpretation, 0, branch.numbaskets, keycache), branch._basket_entryoffset(0, branch.numbaskets)) for branch, interpretation in branches]

        if keycache is None:
            keycache = uproot.cache.memorycache.ThreadSafeDict()

        if basketcache is None:
            basketcache = uproot.cache.memorycache.ThreadSafeDict()
            explicit_basketcache = False
        else:
            explicit_basketcache = True
                
        def evaluate(interpretation, future, past, cachekey):
            if future is None:
                return past
            else:
                out = interpretation.finalize(future())
                if cache is not None:
                    cache[cachekey] = out
                return out

        if issubclass(outputtype, dict):
            def wrap_for_python_scope(futures):
                return lambda: outputtype([(name, evaluate(interpretation, future, past, cachekey)) for name, interpretation, future, past, cachekey in futures])
        elif outputtype == tuple or outputtype == list:
            def wrap_for_python_scope(futures):
                return lambda: outputtype([evaluate(interpretation, future, past, cachekey) for name, interpretation, future, past, cachekey in futures])
        else:
            def wrap_for_python_scope(futures):
                return lambda: outputtype(*[evaluate(interpretation, future, past, cachekey) for name, interpretation, future, past, cachekey in futures])

        for start, stop in entrysteps:
            start = max(start, entrystart)
            stop = min(stop, entrystop)
            if start > stop:
                continue

            futures = []
            for branch, interpretation, basket_itemoffset, basket_entryoffset in branchinfo:
                cachekey = branch._cachekey(interpretation, start, stop)
                if cache is not None:
                    out = cache.get(cachekey, None)
                    if out is not None:
                        futures.append((branch.name, interpretation, None, out, cachekey))
                        continue
                future = branch._step_array(interpretation, basket_itemoffset, basket_entryoffset, start, stop, basketcache, keycache, executor, explicit_basketcache)
                futures.append((branch.name, interpretation, future, None, cachekey))

            out = wrap_for_python_scope(futures)

            if blocking:
                out = out()

            if reportentries:
                yield start, stop, out
            else:
                yield out

    def _format(self, indent=""):
        # TODO: add TTree data to the bottom of this
        out = []
        for branch in self.fBranches:
            out.extend(branch._format(indent))
        return out

    def show(self, foldnames=False, stream=sys.stdout):
        if stream is None:
            return "\n".join(self._format(foldnames))
        else:
            for line in self._format(foldnames):
                stream.write(line)
                stream.write("\n")

    def _recover(self):
        for branch in self.allvalues():
            branch._recover()

    def _normalize_branches(self, arg):
        if arg is None:                                    # no specification; read all branches
            for branch in self.allvalues():                # that have interpretations
                interpretation = interpret(branch)
                if interpretation is not None:
                    yield branch, interpretation

        elif callable(arg):
            for branch in self.allvalues():
                result = arg(branch)
                if result is None:
                    pass
                elif result is True:                       # function is a filter
                    interpretation = interpret(branch)
                    if interpretation is not None:
                        yield branch, interpretation
                else:                                      # function is giving interpretations
                    yield branch, branch._normalize_dtype(result)

        elif isinstance(arg, dict):
            for name, interpretation in arg.items():       # dict of branch-interpretation pairs
                name = _bytesid(name)
                branch = self.get(name)
                interpretation = branch._normalize_dtype(interpretation)
                yield branch, interpretation

        elif isinstance(arg, string_types):
            name = _bytesid(arg)                           # one explicitly given branch name
            branch = self.get(name)
            interpretation = interpret(branch)             # but no interpretation given
            if interpretation is None:
                raise ValueError("cannot interpret branch {0} as a Python type".format(repr(name)))
            else:
                yield branch, interpretation

        else:
            try:
                names = iter(arg)                          # only way to check for iterable (in general)
            except:
                raise TypeError("'branches' argument not understood")
            else:
                for name in names:
                    name = _bytesid(name)
                    branch = self.get(name)
                    interpretation = interpret(branch)     # but no interpretation given
                    if interpretation is None:
                        raise ValueError("cannot interpret branch {0} as a Python type".format(repr(name)))
                    else:
                        yield branch, interpretation

    def _normalize_entrystartstop(self, entrystart, entrystop):
        if entrystart is None:
            entrystart = 0
        if entrystop is None:
            entrystop = self.numentries
        if entrystop < entrystart:
            raise IndexError("entrystop must be greater than or equal to entrystart")
        return entrystart, entrystop

    def __len__(self):
        return self.numentries

    def __getitem__(self, name):
        return self.get(name)

    def __iter__(self):
        # prevent Python's attempt to interpret __len__ and __getitem__ as iteration
        raise TypeError("'TTree' object is not iterable")

    @property
    def pandas(self):
        import uproot._connect.to_pandas
        return uproot._connect.to_pandas.TTreeMethods_pandas(self)

uproot.rootio.methods["TTree"] = TTreeMethods

################################################################ methods for TBranch

class TBranchMethods(object):
    # # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def _postprocess(self, source, cursor, context):
        self._source = source
        self._context = context
        self._streamer = None
        self._recoveredbasket = None
        self._triedrecover = False

    @property
    def name(self):
        return self.fName

    @property
    def title(self):
        return self.fTitle

    @property
    def numentries(self):
        return self.fEntries   # or self.fEntryNumber?

    def iterkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        for branch in self.itervalues(recursive, filtername, filtertitle):
            yield branch.name

    def itervalues(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        for branch in self.fBranches:
            if filtername(branch.name) and filtertitle(branch.title):
                yield branch
            if recursive:
                for x in branch.itervalues(recursive, filtername, filtertitle):
                    yield x

    def iteritems(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        for branch in self.fBranches:
            if filtername(branch.name) and filtertitle(branch.title):
                yield branch.name, branch
            if recursive:
                for x in branch.iteritems(recursive, filtername, filtertitle):
                    yield x

    def keys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.iterkeys(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def values(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.itervalues(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def items(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.iteritems(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def allkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return self.keys(recursive=True, filtername=filtername, filtertitle=filtertitle)

    def allvalues(self, filtername=nofilter, filtertitle=nofilter):
        return self.values(recursive=True, filtername=filtername, filtertitle=filtertitle)

    def allitems(self, filtername=nofilter, filtertitle=nofilter):
        return self.items(recursive=True, filtername=filtername, filtertitle=filtertitle)

    @property
    def numbaskets(self):
        self._tryrecover()
        if self._recoveredbasket is None:
            return self.fWriteBasket
        else:
            return self.fWriteBasket + 1

    def _cachekey(self, interpretation, entrystart, entrystop):
        return "{0};{1};{2};{3};{4}-{5}".format(base64.b64encode(self._context.uuid).decode("ascii"), self._context.treename.decode("ascii"), self.name.decode("ascii"), interpretation.identifier, entrystart, entrystop)

    def _basketcachekey(self, i):
        return "{0};{1};{2};{3};raw".format(base64.b64encode(self._context.uuid).decode("ascii"), self._context.treename.decode("ascii"), self.name.decode("ascii"), i)

    def _keycachekey(self, i):
        return "{0};{1};{2};{3};key".format(base64.b64encode(self._context.uuid).decode("ascii"), self._context.treename.decode("ascii"), self.name.decode("ascii"), i)

    def _threadsafe_key(self, i, keycache, complete):
        key = None
        if keycache is not None:
            key = keycache.get(self._keycachekey(i), None)

        if key is None:
            keysource = self._source.threadlocal()
            try:
                key = self._basketkey(keysource, i, complete)
                if keycache is not None:
                    keycache[self._keycachekey(i)] = key
            finally:
                keysource.dismiss()

        return key

    def _threadsafe_iterate_keys(self, keycache, complete, basketstart=None, basketstop=None):
        if basketstart is None:
            basketstart = 0
        if basketstop is None:
            basketstop = self.numbaskets

        done = False
        if keycache is not None:
            keys = [keycache.get(self._keycachekey(i), None) for i in range(basketstart, basketstop)]
            if all(x is not None for x in keys):
                for key in keys:
                    yield key
                done = True

        if not done:
            keysource = self._source.threadlocal()
            try:
                for i in range(basketstart, basketstop):
                    key = None if keycache is None else keycache.get(self._keycachekey(i), None)
                    if key is None:
                        key = self._basketkey(keysource, i, complete)
                        if keycache is not None:
                            keycache[self._keycachekey(i)] = key
                        yield key
                    else:
                        yield key
            finally:
                keysource.dismiss()

    def uncompressedbytes(self, keycache=None):
        return sum(key.fObjlen for key in self._threadsafe_iterate_keys(keycache, False))

    def compressedbytes(self, keycache=None):
        return sum(key.fNbytes - key.fKeylen for key in self._threadsafe_iterate_keys(keycache, False))

    def compressionratio(self, keycache=None):
        numer, denom = 0, 0
        for key in self._threadsafe_iterate_keys(keycache, False):
            numer += key.fObjlen
            denom += key.fNbytes - key.fKeylen
        return float(numer) / float(denom)

    def _normalize_dtype(self, interpretation):
        if inspect.isclass(interpretation) and issubclass(interpretation, numpy.generic):
            return self._normalize_dtype(numpy.dtype(interpretation))

        elif isinstance(interpretation, numpy.dtype):      # user specified a Numpy dtype
            default = interpret(self)
            if isinstance(default, (asdtype, asjagged)):
                return default.to(interpretation)
            else:
                raise ValueError("cannot cast branch {0} (default interpretation {1}) as dtype {2}".format(repr(self.name), default, interpretation))

        elif isinstance(interpretation, numpy.ndarray):    # user specified a Numpy array
            default = interpret(self)
            if isinstance(default, asdtype):
                return default.toarray(interpretation)
            else:
                raise ValueError("cannot cast branch {0} (default interpretation {1}) as dtype {2}".format(repr(self.name), default, interpretation))

        elif not isinstance(interpretation, uproot.interp.interp.Interpretation):
            raise TypeError("branch interpretation must be an Interpretation, not {0} (type {1})".format(interpretation, type(interpretation)))

        else:
            return interpretation
            
    def _normalize_interpretation(self, interpretation):
        if interpretation is None:
            interpretation = interpret(self)
        else:
            interpretation = self._normalize_dtype(interpretation)

        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type".format(repr(self.name)))

        return interpretation

    def numitems(self, interpretation=None, keycache=None):
        self._tryrecover()
        interpretation = self._normalize_interpretation(interpretation)
        return sum(interpretation.numitems(key.border, self.basket_numentries(i)) for i, key in enumerate(_threadsafe_iterate_keys(keycache, True)))

    @property
    def compression(self):
        return uproot.source.compressed.Compression(self.fCompress)

    def basket_entrystart(self, i):
        self._tryrecover()

        if 0 <= i < self.numbaskets:
            return self.fBasketEntry[i]

        else:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

    def basket_entrystop(self, i):
        self._tryrecover()

        if 0 <= i < self.fWriteBasket:
            return self.fBasketEntry[i + 1]

        elif i == self.numbaskets - 1:
            return self.fEntries   # or self.fEntryNumber?

        else:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

    def basket_numentries(self, i):
        return self.basket_entrystop(i) - self.basket_entrystart(i)

    def basket_uncompressedbytes(self, i, keycache=None):
        self._tryrecover()
        return self._threadsafe_key(i, keycache, False).fObjlen

    def basket_compressedbytes(self, i):
        self._tryrecover()
        key = self._threadsafe_key(i, keycache, False)
        return key.fNbytes - key.fKeylen

    def basket_numitems(self, i, interpretation=None, keycache=None):
        self._tryrecover()
        interpretation = self._normalize_interpretation(interpretation)
        key = self._threadsafe_key(i, keycache, True)
        return interpretation.numitems(key.border, self.basket_numentries(i))
            
    def get(self, name):
        name = _bytesid(name)
        for branch in self.values():
            if branch.name == name:
                return branch
            try:
                return branch.get(name)
            except KeyError:
                pass
        raise KeyError("not found: {0}".format(repr(name)))

    def _normalize_entrystartstop(self, entrystart, entrystop):
        if entrystart is None:
            entrystart = 0
        if entrystop is None:
            entrystop = self.numentries
        if entrystop < entrystart:
            raise IndexError("entrystop must be greater than or equal to entrystart")
        return entrystart, entrystop

    def _localentries(self, i, entrystart, entrystop):
        local_entrystart = max(0, entrystart - self.basket_entrystart(i))
        local_entrystop  = max(0, min(entrystop - self.basket_entrystart(i), self.basket_entrystop(i) - self.basket_entrystart(i)))
        return local_entrystart, local_entrystop

    def _basket(self, i, interpretation, local_entrystart, local_entrystop, basketcache, keycache):
        basketdata = None
        if basketcache is not None:
            basketcachekey = self._basketcachekey(i)
            basketdata = basketcache.get(basketcachekey, None)

        key = self._threadsafe_key(i, keycache, True)

        if basketdata is None:
            basketdata = key.basketdata()

        if basketcache is not None:
            basketcache[basketcachekey] = basketdata

        if key.fObjlen == key.border:
            data, offsets = basketdata, None
        else:
            data = basketdata[:key.border]
            offsets = numpy.empty((key.fObjlen - key.border - 4) // 4, dtype=numpy.int32)  # native endian
            offsets[:-1] = basketdata[key.border + 4 : -4].view(">i4")                     # read as big-endian and convert
            offsets[-1] = key.fLast
            numpy.subtract(offsets, key.fKeylen, offsets)

        return interpretation.fromroot(data, offsets, local_entrystart, local_entrystop)

    def basket(self, i, interpretation=None, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None):
        self._tryrecover()

        if not 0 <= i < self.numbaskets:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

        interpretation = self._normalize_interpretation(interpretation)
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)
        local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)
        entrystart = self.basket_entrystart(i) + local_entrystart
        entrystop = self.basket_entrystart(i) + local_entrystop
        numentries = local_entrystop - local_entrystart

        if cache is not None:
            cachekey = self._cachekey(interpretation, entrystart, entrystop)
            out = cache.get(cachekey, None)
            if out is not None:
                return out

        source = self._basket(i, interpretation, local_entrystart, local_entrystop, basketcache, keycache)
        numitems = interpretation.source_numitems(source)

        destination = interpretation.destination(numitems, numentries)
        interpretation.fill(source, destination, 0, numitems, 0, numentries)
        out = interpretation.finalize(destination)

        if cache is not None:
            cache[cachekey] = out
        return out

    def _basketstartstop(self, entrystart, entrystop):
        basketstart, basketstop = None, None
        for i in range(self.numbaskets):
            if basketstart is None:
                if entrystart < self.basket_entrystop(i) and self.basket_entrystart(i) < entrystop:
                    basketstart = i
                    basketstop = i
            else:
                if self.basket_entrystart(i) < entrystop:
                    basketstop = i

        if basketstop is not None:
            basketstop += 1    # stop is exclusive

        return basketstart, basketstop

    def baskets(self, interpretation=None, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None, reportentries=False, executor=None, blocking=True):
        self._tryrecover()

        interpretation = self._normalize_interpretation(interpretation)
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)
        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if basketstart is None:
            if blocking:
                return []
            else:
                def wait():
                    return []
                return wait

        out = [None] * (basketstop - basketstart)

        def fill(j):
            try:
                basket = self.basket(j + basketstart, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, cache=cache, basketcache=basketcache, keycache=keycache)
                if reportentries:
                    local_entrystart, local_entrystop = self._localentries(j + basketstart, entrystart, entrystop)
                    basket = (local_entrystart + self.basket_entrystart(j + basketstart),
                              local_entrystop + self.basket_entrystart(j + basketstart),
                              basket)
            except:
                return sys.exc_info()
            else:
                out[j] = basket
                return None

        if executor is None:
            for j in range(basketstop - basketstart):
                _delayedraise(fill(j))
            excinfos = ()
        else:
            excinfos = executor.map(fill, range(basketstop - basketstart))

        if blocking:
            for excinfo in excinfos:
                _delayedraise(excinfo)
            return out
        else:
            def wait():
                for excinfo in excinfos:
                    _delayedraise(excinfo)
                return out
            return wait

    def iterate_baskets(self, interpretation=None, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None, reportentries=False):
        self._tryrecover()

        interpretation = self._normalize_interpretation(interpretation)
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)

        for i in range(self.numbaskets):
            if entrystart < self.basket_entrystop(i) and self.basket_entrystart(i) < entrystop:
                local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)

                if local_entrystop > local_entrystart:
                    if reportentries:
                        yield (local_entrystart + self.basket_entrystart(i),
                               local_entrystop + self.basket_entrystart(i),
                               self.basket(i, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, cache=cache, basketcache=basketcache, keycache=keycache))
                    else:
                        yield self.basket(i, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, cache=cache, basketcache=basketcache, keycache=keycache)

    def _basket_itemoffset(self, interpretation, basketstart, basketstop, keycache):
        basket_itemoffset = [0]
        for j, key in enumerate(self._threadsafe_iterate_keys(keycache, True, basketstart, basketstop)):
            i = basketstart + j
            numitems = interpretation.numitems(key.border, self.basket_numentries(i))
            basket_itemoffset.append(basket_itemoffset[-1] + numitems)
        return basket_itemoffset

    def _basket_entryoffset(self, basketstart, basketstop):
        basket_entryoffset = [0]
        for i in range(basketstart, basketstop):
            basket_entryoffset.append(basket_entryoffset[-1] + self.basket_numentries(i))
        return basket_entryoffset

    def array(self, interpretation=None, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        self._tryrecover()

        interpretation = self._normalize_interpretation(interpretation)
        entrystart, entrystop = self._normalize_entrystartstop(entrystart, entrystop)
        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if cache is not None:
            cachekey = self._cachekey(interpretation, entrystart, entrystop)
            out = cache.get(cachekey, None)
            if out is not None:
                if blocking:
                    return out
                else:
                    return lambda: out

        if basketstart is None:
            if blocking:
                return interpretation.empty()
            else:
                def wait():
                    return interpretation.empty()
                return wait

        if keycache is None:
            keycache = uproot.cache.memorycache.ThreadSafeDict()

        basket_itemoffset = self._basket_itemoffset(interpretation, basketstart, basketstop, keycache)
        basket_entryoffset = self._basket_entryoffset(basketstart, basketstop)

        destination = interpretation.destination(basket_itemoffset[-1], basket_entryoffset[-1])

        def fill(j):
            try:
                i = j + basketstart
                local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)
                source = self._basket(i, interpretation, local_entrystart, local_entrystop, basketcache, keycache)

                expecteditems = basket_itemoffset[j + 1] - basket_itemoffset[j]
                source_numitems = interpretation.source_numitems(source)

                expectedentries = basket_entryoffset[j + 1] - basket_entryoffset[j]
                source_numentries = local_entrystop - local_entrystart 

                if j + 1 == basketstop - basketstart:
                    if expecteditems > source_numitems:
                        basket_itemoffset[j + 1] -= expecteditems - source_numitems
                    if expectedentries > source_numentries:
                        basket_entryoffset[j + 1] -= expectedentries - source_numentries

                elif j == 0:
                    if expecteditems > source_numitems:
                        basket_itemoffset[j] += expecteditems - source_numitems
                    if expectedentries > source_numentries:
                        basket_entryoffset[j] += expectedentries - source_numentries

                interpretation.fill(source,
                                    destination,
                                    basket_itemoffset[j],
                                    basket_itemoffset[j + 1],
                                    basket_entryoffset[j],
                                    basket_entryoffset[j + 1])

            except:
                return sys.exc_info()

        if executor is None:
            for j in range(basketstop - basketstart):
                _delayedraise(fill(j))
            excinfos = ()
        else:
            excinfos = executor.map(fill, range(basketstop - basketstart))

        def wait():
            for excinfo in excinfos:
                _delayedraise(excinfo)

            clipped = interpretation.clip(destination,
                                          basket_itemoffset[0],
                                          basket_itemoffset[-1],
                                          basket_entryoffset[0],
                                          basket_entryoffset[-1])

            out = interpretation.finalize(clipped)
            if cache is not None:
                cache[cachekey] = out
            return out

        if blocking:
            return wait()
        else:
            return wait

    def _step_array(self, interpretation, basket_itemoffset, basket_entryoffset, entrystart, entrystop, basketcache, keycache, executor, explicit_basketcache):
        self._tryrecover()

        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if basketstart is None:
            return lambda: interpretation.empty()

        basket_itemoffset = basket_itemoffset[basketstart : basketstop + 1]
        basket_itemoffset = [x - basket_itemoffset[0] for x in basket_itemoffset]

        basket_entryoffset = basket_entryoffset[basketstart : basketstop + 1]
        basket_entryoffset = [x - basket_entryoffset[0] for x in basket_entryoffset]

        destination = interpretation.destination(basket_itemoffset[-1], basket_entryoffset[-1])

        def fill(j):
            try:
                i = j + basketstart
                local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)
                source = self._basket(i, interpretation, local_entrystart, local_entrystop, basketcache, keycache)

                expecteditems = basket_itemoffset[j + 1] - basket_itemoffset[j]
                source_numitems = interpretation.source_numitems(source)

                expectedentries = basket_entryoffset[j + 1] - basket_entryoffset[j]
                source_numentries = local_entrystop - local_entrystart

                if j + 1 == basketstop - basketstart:
                    if expecteditems > source_numitems:
                        basket_itemoffset[j + 1] -= expecteditems - source_numitems
                    if expectedentries > source_numentries:
                        basket_entryoffset[j + 1] -= expectedentries - source_numentries

                elif j == 0:
                    if expecteditems > source_numitems:
                        basket_itemoffset[j] += expecteditems - source_numitems
                    if expectedentries > source_numentries:
                        basket_entryoffset[j] += expectedentries - source_numentries

                interpretation.fill(source,
                                    destination,
                                    basket_itemoffset[j],
                                    basket_itemoffset[j + 1],
                                    basket_entryoffset[j],
                                    basket_entryoffset[j + 1])

            except:
                return sys.exc_info()

        if executor is None:
            for j in range(basketstop - basketstart):
                _delayedraise(fill(j))
            excinfos = ()
        else:
            excinfos = executor.map(fill, range(basketstop - basketstart))

        def wait():
            for excinfo in excinfos:
                _delayedraise(excinfo)

            if not explicit_basketcache:
                for i in range(basketstop - 1):  # not including the last real basket
                    try:
                        del basketcache[self._basketcachekey(i)]
                    except KeyError:
                        pass

            return interpretation.clip(destination,
                                       basket_itemoffset[0],
                                       basket_itemoffset[-1],
                                       basket_entryoffset[0],
                                       basket_entryoffset[-1])

        return wait

    def lazyarray(self, interpretation=None, cache=None, basketcache=None, keycache=None, executor=None):
        self._tryrecover()
        interpretation = self._normalize_interpretation(interpretation)
        return self._LazyArray(self, interpretation, cache, basketcache, keycache, executor)

    class _LazyArray(object):
        def __init__(self, branch, interpretation, cache, basketcache, keycache, executor):
            if keycache is None:
                keycache = uproot.cache.memorycache.ThreadSafeDict()

            self._branch = branch
            self._interpretation = interpretation
            self._cache = cache
            self._basketcache = basketcache
            self._keycache = keycache
            self._executor = executor

            self._len = self._branch.numentries

            if hasattr(self._interpretation, "todtype"):
                self.dtype = self._interpretation.todtype

            if hasattr(self._interpretation, "todims"):
                self.shape = (len(self),) + self._interpretation.todims

        def __len__(self):
            return self._len

        def __getitem__(self, index):
            if isinstance(index, slice):
                start, stop, step = self._normalize_slice(index)
                if (start >= stop and step > 0) or (stop >= start and step < 0):
                    return self._interpretation.empty()
                else:
                    array = self._array(min(start, stop), max(start, stop))
                    if step == 1:
                        return array
                    else:
                        return array[::step]
            else:
                index = self._normalize_index(index, False, 1)
                array = self._array(index, index + 1)
                return array[0]

        def __getslice__(self, start, end):
            return self.__getitem__(slice(start, end))

        def cumsum(self, axis=None, dtype=None, out=None):
            return self._array(self._basket_entryoffset[0], self._basket_entryoffset[-1]).cumsum(axis=axis, dtype=dtype, out=out)

        def _array(self, entrystart, entrystop):
            return self._branch.array(interpretation=self._interpretation, entrystart=entrystart, entrystop=entrystop, cache=self._cache, basketcache=self._basketcache, keycache=self._keycache, executor=self._executor, blocking=True)

        def _normalize_index(self, i, clip, step):
            lenself = len(self)
            if i < 0:
                j = lenself + i
                if j < 0:
                    if clip:
                        return 0 if step > 0 else lenself
                    else:
                        raise IndexError("index out of range: {0} for length {1}".format(i, lenself))
                else:
                    return j
            elif i < lenself:
                return i
            elif clip:
                return lenself if step > 0 else 0
            else:
                raise IndexError("index out of range: {0} for length {1}".format(i, lenself))

        def _normalize_slice(self, s):
            lenself = len(self)
            if s.step is None:
                step = 1
            else:
                step = s.step
            if step == 0:
                raise ValueError("slice step cannot be zero")
            if s.start is None:
                if step > 0:
                    start = 0
                else:
                    start = lenself - 1
            else:
                start = self._normalize_index(s.start, True, step)
            if s.stop is None:
                if step > 0:
                    stop = lenself
                else:
                    stop = -1
            else:
                stop = self._normalize_index(s.stop, True, step)

            return start, stop, step

    class _BasketKey(object):
        def __init__(self, source, cursor, compression, complete):
            start = cursor.index
            self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir = cursor.fields(source, TBranchMethods._BasketKey._format_small)

            if self.fVersion > 1000:
                cursor.index = start
                self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle, self.fSeekKey, self.fSeekPdir = cursor.fields(source, TBranchMethods._BasketKey._format_big)

            if complete:
                cursor.index = start + self.fKeylen - TBranchMethods._BasketKey._format_complete.size - 1
                self.fVersion, self.fBufferSize, self.fNevBufSize, self.fNevBuf, self.fLast = cursor.fields(source, TBranchMethods._BasketKey._format_complete)

                self.border = self.fLast - self.fKeylen

                if source.size() - self.fSeekKey < self.fNbytes:
                    raise ValueError("TKey declares that object {0} has {1} bytes but only {2} remain in the file".format(repr(self.fName), self.fNbytes, source.size() - self.fSeekKey))

                if self.fObjlen != self.fNbytes - self.fKeylen:
                    self.source = uproot.source.compressed.CompressedSource(compression, source, Cursor(self.fSeekKey + self.fKeylen), self.fNbytes - self.fKeylen, self.fObjlen)
                    self.cursor = Cursor(0)
                else:
                    self.source = source
                    self.cursor = Cursor(self.fSeekKey + self.fKeylen)

        _format_small = struct.Struct(">ihiIhhii")
        _format_big = struct.Struct(">ihiIhhqq")
        _format_complete = struct.Struct(">Hiiii")

        def basketdata(self):
            datasource = self.source.threadlocal()
            try:
                return self.cursor.copied().bytes(datasource, self.fObjlen)
            finally:
                datasource.dismiss()
            
    class _RecoveredTBasket(uproot.rootio.ROOTObject):
        @classmethod
        def _readinto(cls, self, source, cursor, context):
            start = cursor.index
            self.fNbytes, self.fVersion, self.fObjlen, self.fDatime, self.fKeylen, self.fCycle = cursor.fields(source, cls._format1)

            # skip the class name, name, and title
            cursor.index = start + self.fKeylen - cls._format2.size - 1
            self.fVersion, self.fBufferSize, self.fNevBufSize, self.fNevBuf, self.fLast = cursor.fields(source, cls._format2)

            # one-byte terminator
            cursor.skip(1)

            # then if you have offsets data, read them in
            if self.fNevBufSize > 8:
                offsets = cursor.bytes(source, self.fNevBuf * 4 + 8)
                cursor.skip(-4)

            # there's a second TKey here, but it doesn't contain any new information (in fact, less)
            cursor.skip(self.fKeylen)

            size = self.border = self.fLast - self.fKeylen

            # the data (not including offsets)
            self.contents = cursor.bytes(source, size)

            # put the offsets back in, in the way that we expect it
            if self.fNevBufSize > 8:
                self.contents = numpy.concatenate((self.contents, offsets))
                size += offsets.nbytes

            self.fObjlen = size
            self.fNbytes = self.fObjlen + self.fKeylen

            return self

        _format1 = struct.Struct(">ihiIhh")
        _format2 = struct.Struct(">Hiiii")

        def basketdata(self):
            return self.contents

    def _recover(self):
        if self._recoveredbasket is None:
            recovered = [x for x in uproot.rootio.TObjArray.read(self._source, self.fBaskets._cursor, self._context, asclass=TBranchMethods._RecoveredTBasket) if x is not None]
            if len(recovered) == 1:
                self._recoveredbasket = recovered[0]
            else:
                raise ValueError("recovered {0} baskets, expected 1".format(len(recovered)))

    def _tryrecover(self):
        if not self._triedrecover and self.numentries != self.fBasketEntry[self.fWriteBasket]:
            try:
                self._recover()
            except Exception as err:
                warnings.warn("attempted to read missing baskets from incompletely written file, but encountered {0}: {1}".format(err.__class__.__name__, str(err)))
        self._triedrecover = True

    def _basketkey(self, source, i, complete):
        if 0 <= i < self.fWriteBasket:
            return self._BasketKey(source.parent(), Cursor(self.fBasketSeek[i]), uproot.source.compressed.Compression(self.fCompress), complete)

        elif self.fWriteBasket <= i < self.numbaskets:
            return self._recoveredbasket

        else:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

    def _format(self, foldnames, indent="", strip=""):
        name = self.fName.decode("ascii")
        if foldnames and name.startswith(strip + "."):
            name = name[len(strip) + 1:]

        if len(name) > 26:
            out = [indent + name, indent + "{0:26s} {1:26s} {2}".format("", "(no streamer)" if self._streamer is None else self._streamer.__class__.__name__, interpret(self))]
        else:
            out = [indent + "{0:26s} {1:26s} {2}".format(name, "(no streamer)" if self._streamer is None else self._streamer.__class__.__name__, interpret(self))]

        for branch in self.fBranches:
            out.extend(branch._format(foldnames, indent + "  " if foldnames else indent, self.fName))
        if len(self.fBranches) > 0 and out[-1] != "":
            out.append("")

        return out

    def show(self, foldnames=False, stream=sys.stdout):
        if stream is None:
            return "\n".join(self._format(foldnames))
        else:
            for line in self._format(foldnames):
                stream.write(line)
                stream.write("\n")

    def __len__(self):
        return self.numentries

    def __getitem__(self, name):
        return self.get(name)

    def __iter__(self):
        # prevent Python's attempt to interpret __len__ and __getitem__ as iteration
        raise TypeError("'TBranch' object is not iterable")

uproot.rootio.methods["TBranch"] = TBranchMethods
