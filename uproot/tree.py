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
import math
import numbers
import os.path
import re
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
from uproot.source.http import HTTPSource

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

def _filename_explode(x):
    parsed = urlparse(x)
    if _bytesid(parsed.scheme) == b"file" or len(parsed.scheme) == 0:
        pattern = os.path.expanduser(parsed.netloc + parsed.path)
        if "*" in pattern or "?" in pattern or "[" in pattern:
            out = sorted(glob.glob(pattern))
            if len(out) == 0:
                raise TypeError("no matches for filename {0}".format(repr(pattern)))
        else:
            out = [pattern]
        return out
    else:
        return [x]

################################################################ high-level interface

def iterate(path, treepath, branches=None, entrysteps=None, outputtype=dict, reportentries=False, cache=None, basketcache=None, keycache=None, executor=None, blocking=True, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, **options):
    for tree, newbranches, globalentrystart in _iterate(path, treepath, branches, localsource, xrootdsource, httpsource, **options):
        for start, stop, arrays in tree.iterate(branches=newbranches, entrysteps=entrysteps, outputtype=outputtype, reportentries=True, entrystart=0, entrystop=tree.numentries, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking):
            if reportentries:
                yield globalentrystart + start, globalentrystart + stop, arrays
            else:
                yield arrays

def _iterate(path, treepath, branches, localsource, xrootdsource, httpsource, **options):
    if isinstance(path, string_types):
        paths = _filename_explode(path)
    else:
        paths = [y for x in path for y in _filename_explode(x)]

    oldpath = None
    oldbranches = None
    holdover = None
    holdoverentries = 0
    outerstart = 0
    globalentrystart = 0
    for path in paths:
        tree = uproot.rootio.open(path, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, **options)[treepath]
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

    _vector_regex = re.compile(b"^vector<(.+)>$")

    def _attachstreamer(self, branch, streamer, streamerinfosmap):
        if streamer is None:
            m = re.match(self._vector_regex, getattr(branch, "fClassName", b""))
            if m is None or m.group(1) not in streamerinfosmap:
                return
            else:
                substreamer = streamerinfosmap[m.group(1)]
                if isinstance(substreamer, uproot.rootio.TStreamerInfo):
                    streamer = uproot.rootio.TStreamerSTL.vector(None, substreamer.fName)
                else:
                    streamer = uproot.rootio.TStreamerSTL.vector(substreamer.fType, substreamer.fTypeName)

        if isinstance(streamer, uproot.rootio.TStreamerInfo):
            if len(streamer.fElements) == 1 and isinstance(streamer.fElements[0], uproot.rootio.TStreamerBase) and streamer.fElements[0].fName == b"TObjArray":
                if streamer.fName == b"TClonesArray":
                    return self._attachstreamer(branch, streamerinfosmap.get(branch.fClonesName, None), streamerinfosmap)
                else:
                    # FIXME: can only determine streamer by reading some values?
                    return

            elif len(streamer.fElements) == 1 and isinstance(streamer.fElements[0], uproot.rootio.TStreamerSTL) and streamer.fElements[0].fName == b"This":
                return self._attachstreamer(branch, streamer.fElements[0], streamerinfosmap)

        branch._streamer = streamer
        if isinstance(streamer, uproot.rootio.TStreamerSTL) and streamer.fSTLtype == uproot.const.kSTLvector:
            branch._vecstreamer = streamerinfosmap.get(re.match(self._vector_regex, streamer.fTypeName).group(1), None)
        else:
            branch._vecstreamer = None

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

    def _postprocess(self, source, cursor, context, parent):
        self._context = context
        self._context.treename = self.name

        for branch in self.fBranches:
            self._attachstreamer(branch, context.streamerinfosmap.get(getattr(branch, "fClassName", None), None), context.streamerinfosmap)

        leaf2branch = {}
        for branch in self.itervalues(recursive=True):
            if len(branch.fLeaves) == 1:
                leaf2branch[id(branch.fLeaves[0])] = branch

        for branch in self.itervalues(recursive=True):
            if len(branch.fLeaves) > 0:
                if branch.fLeaves[0].fLeafCount is not None:
                    branch._countbranch = leaf2branch.get(id(branch.fLeaves[0].fLeafCount), None)

        if self.fAliases is None:
            self.aliases = {}
        else:
            self.aliases = dict((alias.fName, alias.fTitle) for alias in self.fAliases)

    @property
    def name(self):
        return self.fName

    @property
    def title(self):
        return self.fTitle

    @property
    def numentries(self):
        return self.fEntries

    @property
    def numbranches(self):
        count = 0
        for x in self.itervalues(recursive=True):
            count += 1
        return count

    def iterkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        for branch in self.itervalues(recursive, filtername, filtertitle):
            if aliases:
                for aliasname, branchname in self.aliases.items():
                    if branch.name == branchname:
                        yield aliasname
            yield branch.name

    def itervalues(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        for branch in self.fBranches:
            if filtername(branch.name) and filtertitle(branch.title):
                yield branch
            if recursive:
                for x in branch.itervalues(recursive, filtername, filtertitle):
                    yield x

    def iteritems(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        for branch in self.itervalues(recursive, filtername, filtertitle):
            if aliases:
                for aliasname, branchname in self.aliases.items():
                    if branch.name == branchname:
                        yield aliasname, branch
            yield branch.name, branch

    def keys(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        return list(self.iterkeys(recursive=recursive, filtername=filtername, filtertitle=filtertitle, aliases=aliases))

    def values(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.itervalues(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def items(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        return list(self.iteritems(recursive=recursive, filtername=filtername, filtertitle=filtertitle, aliases=aliases))

    def allkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        return self.keys(recursive=True, filtername=filtername, filtertitle=filtertitle, aliases=aliases)

    def allvalues(self, filtername=nofilter, filtertitle=nofilter):
        return self.values(recursive=True, filtername=filtername, filtertitle=filtertitle)

    def allitems(self, filtername=nofilter, filtertitle=nofilter, aliases=True):
        return self.items(recursive=True, filtername=filtername, filtertitle=filtertitle, aliases=aliases)

    def get(self, name, recursive=True, filtername=nofilter, filtertitle=nofilter, aliases=True):
        name = _bytesid(name)
        for n, b in self.iteritems(recursive=recursive, filtername=filtername, filtertitle=filtertitle, aliases=aliases):
            if n == name:
                return b
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

    def arrays(self, branches=None, outputtype=dict, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        branches = list(self._normalize_branches(branches))

        futures = [(branch.name, branch.array(interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=False)) for branch, interpretation in branches]

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])
            def wait():
                return outputtype(*[future() for name, future in futures])
        elif issubclass(outputtype, dict):
            def wait():
                return outputtype((name, future()) for name, future in futures)
        elif issubclass(outputtype, (list, tuple)):
            def wait():
                return outputtype(future() for name, future in futures)
        else:
            def wait():
                return outputtype(*[future() for name, future in futures])

        if blocking:
            return wait()
        else:
            return wait

    def lazyarray(self, branch, interpretation=None, limitbytes=1024**2, cache=None, basketcache=None, keycache=None, executor=None):
        return self.get(branch).lazyarray(interpretation=interpretation, limitbytes=limitbytes, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor)

    def lazyarrays(self, branches=None, outputtype=dict, limitbytes=1024**2, cache=None, basketcache=None, keycache=None, executor=None):
        branches = list(self._normalize_branches(branches))

        if basketcache is None:
            basketcache = uproot.cache.memorycache.ThreadSafeMemoryCache(limitbytes)
        if keycache is None:
            keycache = uproot.cache.memorycache.ThreadSafeDict()

        lazyarrays = [(branch.name, branch.lazyarray(interpretation=interpretation, limitbytes=limitbytes, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor)) for branch, interpretation in branches]

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])
            return outputtype(*[lazyarray for name, lazyarray in lazyarrays])
        elif issubclass(outputtype, dict):
            return outputtype(lazyarrays)
        elif issubclass(outputtype, (list, tuple)):
            return outputtype(lazyarray for name, lazyarray in lazyarrays)
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

        if keycache is None:
            keycache = uproot.cache.memorycache.ThreadSafeDict()

        if basketcache is None:
            basketcache = uproot.cache.memorycache.ThreadSafeDict()
            explicit_basketcache = False
        else:
            explicit_basketcache = True

        def evaluate(branch, interpretation, future, past, cachekey):
            if future is None:
                return past
            else:
                out = interpretation.finalize(future(), branch)
                if cache is not None:
                    cache[cachekey] = out
                return out

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])
            def wrap_for_python_scope(futures):
                return lambda: outputtype(*[evaluate(branch, interpretation, future, past, cachekey) for branch, interpretation, future, past, cachekey in futures])
        elif issubclass(outputtype, dict):
            def wrap_for_python_scope(futures):
                return lambda: outputtype((branch.name, evaluate(branch, interpretation, future, past, cachekey)) for branch, interpretation, future, past, cachekey in futures)
        elif issubclass(outputtype, (list, tuple)):
            def wrap_for_python_scope(futures):
                return lambda: outputtype(evaluate(branch, interpretation, future, past, cachekey) for branch, interpretation, future, past, cachekey in futures)
        else:
            def wrap_for_python_scope(futures):
                return lambda: outputtype(*[evaluate(branch, interpretation, future, past, cachekey) for branch, interpretation, future, past, cachekey in futures])

        for start, stop in entrysteps:
            start = max(start, entrystart)
            stop = min(stop, entrystop)
            if start > stop:
                continue

            futures = []
            for branch, interpretation in branches:
                basketstart, basketstop = branch._basketstartstop(start, stop)
                basket_itemoffset = branch._basket_itemoffset(interpretation, basketstart, basketstop, keycache)
                basket_entryoffset = branch._basket_entryoffset(basketstart, basketstop)

                cachekey = branch._cachekey(interpretation, start, stop)
                if cache is not None:
                    out = cache.get(cachekey, None)
                    if out is not None:
                        futures.append((branch, interpretation, None, out, cachekey))
                        continue
                future = branch._step_array(interpretation, basket_itemoffset, basket_entryoffset, start, stop, basketcache, keycache, executor, explicit_basketcache)
                futures.append((branch, interpretation, future, None, cachekey))

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

    def matches(self, branches):
        return [b.name for b, i in self._normalize_branches(branches, allownone=False, allowcallable=False, allowdict=False, allowstring=True)]

    _branch_regex = re.compile(b"^/(.*)/([iLmsux]*)$")

    @staticmethod
    def _branch_flags(flags):
        flagsbyte = 0
        for flag in flags:
            if flag == "i":
                flagsbyte += re.I
            elif flag == "L":
                flagsbyte += re.L
            elif flag == "m":
                flagsbyte += re.M
            elif flag == "s":
                flagsbyte += re.S
            elif flag == "u":
                flagsbyte += re.U
            elif flag == "x":
                flagsbyte += re.X
        return flagsbyte

    def _normalize_branches(self, arg, allownone=True, allowcallable=True, allowdict=True, allowstring=True, aliases=True):
        if allownone and arg is None:                      # no specification; read all branches
            for branch in self.allvalues():                # that have interpretations
                interpretation = interpret(branch)
                if interpretation is not None:
                    yield branch, interpretation

        elif allowcallable and callable(arg):
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

        elif allowdict and isinstance(arg, dict):
            for word, interpretation in arg.items():
                word = _bytesid(word)

                isregex = re.match(self._branch_regex, word)
                if isregex is not None:
                    regex, flags = isregex.groups()
                    for name, branch in self.iteritems(recursive=True, aliases=aliases):
                        if re.match(regex, name, self._branch_flags(flags)):
                            yield branch, branch._normalize_dtype(interpretation)

                elif b"*" in word or b"?" in word or b"[" in word:
                    for name, branch in self.iteritems(recursive=True, aliases=aliases):
                        if name == word or glob.fnmatch.fnmatchcase(name, word):
                            yield branch, branch._normalize_dtype(interpretation)

                else:
                    branch = self.get(word, aliases=aliases)
                    yield branch, branch._normalize_dtype(interpretation)

        elif allowstring and isinstance(arg, string_types):
            for x in self._normalize_branches([arg]):
                yield x

        else:
            try:
                words = iter(arg)                          # only way to check for iterable (in general)
            except:
                raise TypeError("'branches' argument not understood")
            else:
                for word in words:
                    word = _bytesid(word)

                    isregex = re.match(self._branch_regex, word)
                    if isregex is not None:
                        regex, flags = isregex.groups()
                        for name, branch in self.iteritems(recursive=True, aliases=aliases):
                            if re.match(regex, name, self._branch_flags(flags)):
                                interpretation = interpret(branch)
                                if interpretation is None:
                                    if name == word:
                                        raise ValueError("cannot interpret branch {0} as a Python type".format(repr(branch.name)))
                                else:
                                    yield branch, interpretation

                    elif b"*" in word or b"?" in word or b"[" in word:
                        for name, branch in self.iteritems(recursive=True, aliases=aliases):
                            if name == word or glob.fnmatch.fnmatchcase(name, word):
                                interpretation = interpret(branch)
                                if interpretation is None:
                                    if name == word:
                                        raise ValueError("cannot interpret branch {0} as a Python type".format(repr(branch.name)))
                                else:
                                    yield branch, interpretation

                    else:
                        branch = self.get(word, aliases=aliases)
                        interpretation = interpret(branch)
                        if interpretation is None:
                            raise ValueError("cannot interpret branch {0} as a Python type".format(repr(branch.name)))
                        else:
                            yield branch, interpretation

    def _normalize_entrystartstop(self, entrystart, entrystop):
        if entrystart is None:
            entrystart = 0
        elif entrystart < 0:
            entrystart += self.numentries
        entrystart = min(self.numentries, max(0, entrystart))

        if entrystop is None:
            entrystop = self.numentries
        elif entrystop < 0:
            entrystop += self.numentries
        entrystop = min(self.numentries, max(0, entrystop))

        if entrystop < entrystart:
            raise IndexError("entrystop must be greater than or equal to entrystart")

        return int(entrystart), int(entrystop)

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

    def _postprocess(self, source, cursor, context, parent):
        self._source = source
        self._context = context
        self._streamer = None
        self._recoveredbasket = None
        self._triedrecover = False
        self._countbranch = None
        self._tree_iofeatures = 0
        if hasattr(parent, "fIOFeatures"):
            self._tree_iofeatures = parent.fIOFeatures.fIOBits

    @property
    def name(self):
        return self.fName

    @property
    def title(self):
        return self.fTitle

    @property
    def interpretation(self):
        return interpret(self)

    @property
    def numentries(self):
        return self.fEntries   # or self.fEntryNumber?

    @property
    def numbranches(self):
        count = 0
        for x in self.itervalues(recursive=True):
            count += 1
        return count

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
            
    def get(self, name, recursive=True, filtername=nofilter, filtertitle=nofilter, aliases=True):
        name = _bytesid(name)
        for n, b in self.iteritems(recursive=recursive, filtername=filtername, filtertitle=filtertitle):
            if n == name:
                return b
        raise KeyError("not found: {0}".format(repr(name)))

    @property
    def numbaskets(self):
        if not self._triedrecover:
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
        if not self._triedrecover:
            self._tryrecover()
        interpretation = self._normalize_interpretation(interpretation)
        return sum(interpretation.numitems(key.border, self.basket_numentries(i)) for i, key in enumerate(_threadsafe_iterate_keys(keycache, True)))

    @property
    def compression(self):
        return uproot.source.compressed.Compression(self.fCompress)

    def basket_entrystart(self, i):
        if not self._triedrecover:
            self._tryrecover()

        if 0 <= i < self.numbaskets:
            return self.fBasketEntry[i]

        else:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

    def basket_entrystop(self, i):
        if not self._triedrecover:
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
        if not self._triedrecover:
            self._tryrecover()
        return self._threadsafe_key(i, keycache, False).fObjlen

    def basket_compressedbytes(self, i):
        if not self._triedrecover:
            self._tryrecover()
        key = self._threadsafe_key(i, keycache, False)
        return key.fNbytes - key.fKeylen

    def basket_numitems(self, i, interpretation=None, keycache=None):
        if not self._triedrecover:
            self._tryrecover()
        interpretation = self._normalize_interpretation(interpretation)
        key = self._threadsafe_key(i, keycache, True)
        return interpretation.numitems(key.border, self.basket_numentries(i))

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

            if self._countbranch is not None and numpy.uint8(self._tree_iofeatures) & numpy.uint8(uproot.const.kGenerateOffsetMap) != 0:
                counts = self._countbranch.array(entrystart=(local_entrystart + self.basket_entrystart(i)),
                                                 entrystop=(local_entrystop + self.basket_entrystart(i)))
                itemsize = 1
                if isinstance(interpretation, asjagged):
                    itemsize = interpretation.asdtype.fromdtype.itemsize
                numpy.multiply(counts, itemsize, counts)
                offsets = numpy.empty(len(counts) + 1, dtype=numpy.int32)
                offsets[0] = 0
                numpy.cumsum(counts, out=offsets[1:])

        else:
            data = basketdata[:key.border]
            offsets = numpy.empty((key.fObjlen - key.border - 4) // 4, dtype=numpy.int32)  # native endian
            offsets[:-1] = basketdata[key.border + 4 : -4].view(">i4")                     # read as big-endian and convert
            offsets[-1] = key.fLast
            numpy.subtract(offsets, key.fKeylen, offsets)

        return interpretation.fromroot(data, offsets, local_entrystart, local_entrystop)

    def basket(self, i, interpretation=None, entrystart=None, entrystop=None, cache=None, basketcache=None, keycache=None):
        if not self._triedrecover:
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
        out = interpretation.finalize(destination, self)

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
        if not self._triedrecover:
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
        if not self._triedrecover:
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
        if not self._triedrecover:
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

            out = interpretation.finalize(clipped, self)
            if cache is not None:
                cache[cachekey] = out
            return out

        if blocking:
            return wait()
        else:
            return wait

    def _step_array(self, interpretation, basket_itemoffset, basket_entryoffset, entrystart, entrystop, basketcache, keycache, executor, explicit_basketcache):
        if not self._triedrecover:
            self._tryrecover()

        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if basketstart is None:
            return lambda: interpretation.empty()

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

    def lazyarray(self, interpretation=None, limitbytes=1024**2, cache=None, basketcache=None, keycache=None, executor=None):
        if not self._triedrecover:
            self._tryrecover()

        if basketcache is None:
            basketcache = uproot.cache.memorycache.ThreadSafeMemoryCache(limitbytes)
        if keycache is None:
            keycache = uproot.cache.memorycache.ThreadSafeDict()

        interpretation = self._normalize_interpretation(interpretation)
        return LazyArray._frombranch(self, interpretation, cache, basketcache, keycache, executor)

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

                if source.size() is not None:
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
        def _readinto(cls, self, source, cursor, context, parent):
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
            recovered = [x for x in uproot.rootio.TObjArray.read(self._source, self.fBaskets._cursor, self._context, self, asclass=TBranchMethods._RecoveredTBasket) if x is not None]
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

################################################################ for quickly getting numentries

def numentries(path, treepath, total=True, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, executor=None, blocking=True):
    if isinstance(path, string_types):
        paths = _filename_explode(path)
    else:
        paths = [y for x in path for y in _filename_explode(x)]
    return _numentries(paths, treepath, total, localsource, xrootdsource, httpsource, executor, blocking, [])

def _numentries(paths, treepath, total, localsource, xrootdsource, httpsource, executor, blocking, uuids):
    class _TTreeForNumEntries(uproot.rootio.ROOTStreamedObject):
        @classmethod
        def _readinto(cls, self, source, cursor, context, parent):
            start, cnt, classversion = uproot.rootio._startcheck(source, cursor)
            tnamed = uproot.rootio.Undefined.read(source, cursor, context, parent)
            tattline = uproot.rootio.Undefined.read(source, cursor, context, parent)
            tattfill = uproot.rootio.Undefined.read(source, cursor, context, parent)
            tattmarker = uproot.rootio.Undefined.read(source, cursor, context, parent)
            self.fEntries, = cursor.fields(source, _TTreeForNumEntries._format1)
            return self
        _format1 = struct.Struct('>q')
    
    out = [None] * len(paths)

    def fill(i):
        try:
            file = uproot.rootio.open(paths[i], localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, read_streamers=False, keep_source=True)
        except:
            return sys.exc_info()
        else:
            try:
                source = file._context.source
                file._context.classes["TTree"] = _TTreeForNumEntries
                out[i] = file[treepath].fEntries
                uuids[i] = file._context.uuid
            except:
                return sys.exc_info()
            else:
                return None
            finally:
                source._source._mmap.close()

    if executor is None:
        for i in range(len(paths)):
            _delayedraise(fill(i))
        excinfos = ()
    else:
        excinfos = executor.map(fill, range(len(paths)))

    def wait():
        for excinfo in excinfos:
            _delayedraise(excinfo)
        if total:
            return sum(out)
        else:
            return dict(zip(paths, out))
        
    if blocking:
        return wait()
    else:
        return wait

def lazyarrays(path, treepath, branches=None, outputtype=dict, limitbytes=1024**2, cache=None, basketcache=None, keycache=None, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, executor=None):
    if isinstance(path, string_types):
        paths = _filename_explode(path)
    else:
        paths = [y for x in path for y in _filename_explode(x)]

    uuids = [None] * len(paths)
    path2numentries = _numentries(paths, treepath, False, localsource, xrootdsource, httpsource, executor, True, uuids)
    globalentryoffset = numpy.empty(len(paths) + 1, dtype=numpy.int64)
    globalentryoffset[0] = 0
    for i in range(len(paths)):
        globalentryoffset[i + 1] = globalentryoffset[i] + path2numentries[paths[i]]

    tree = uproot.rootio.open(paths[0], localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource)[treepath]
    branches = list(tree._normalize_branches(branches))

    if cache is None:
        cache = uproot.cache.memorycache.ThreadSafeMemoryCache(limitbytes)
    if basketcache is None:
        basketcache = cache
    if keycache is None:
        keycache = cache
    cache[LazyArray._cachekey(uuids[0], treepath)] = tree

    def chunksize(branch):
        return (branch.fBasketEntry[1:] - branch.fBasketEntry[:-1]).max()

    if outputtype == namedtuple:
        outputtype = namedtuple("Arrays", [branch.name.decode("ascii") for branch, interpretation in branches])
        return outputtype(*[LazyArray._frompaths(paths, uuids, treepath, branch.name, chunksize(branch), interpretation, globalentryoffset, cache, basketcache, keycache, localsource, xrootdsource, httpsource, executor) for branch, interpretation in branches])
    elif issubclass(outputtype, dict):
        return outputtype((branch.name, LazyArray._frompaths(paths, uuids, treepath, branch.name, chunksize(branch), interpretation, globalentryoffset, cache, basketcache, keycache, localsource, xrootdsource, httpsource, executor)) for branch, interpretation in branches)
    elif issubclass(outputtype, (list, tuple)):
        return outputtype(LazyArray._frompaths(paths, uuids, treepath, branch.name, chunksize(branch), interpretation, globalentryoffset, cache, basketcache, keycache, localsource, xrootdsource, httpsource, executor) for branch, interpretation in branches)
    else:
        return outputtype(*[LazyArray._frompaths(paths, uuids, treepath, branch.name, chunksize(branch), interpretation, globalentryoffset, cache, basketcache, keycache, localsource, xrootdsource, httpsource, executor) for branch, interpretation in branches])

def lazyarray(path, treepath, branchname, interpretation=None, outputtype=dict, limitbytes=1024**2, cache=None, basketcache=None, keycache=None, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, executor=None):
    if interpretation is None:
        branches = branchname
    else:
        branches = {branchname: interpretation}
    return lazyarrays(path, treepath, branches=branches, outputtype=tuple, limitbytes=limitbytes, cache=cache, basketcache=basketcache, keycache=keycache, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, executor=executor)[0]

class LazyArray(object):
    def __init__(self):
        raise TypeError("LazyArrays should be created with uproot.lazyarrays or TTreeMethods.lazyarrays")

    @classmethod
    def _frombranch(cls, onlybranch, interpretation, cache, basketcache, keycache, executor):
        self = cls.__new__(cls)
        self._onlybranch = onlybranch
        self._paths = (None,)
        self._uuids = (None,)
        self._treepath = None
        self._branchname = onlybranch.name
        self._chunksize = (onlybranch.fBasketEntry[1:] - onlybranch.fBasketEntry[:-1]).max()
        self._interpretation = interpretation
        self._globalentryoffset = numpy.array([0, onlybranch.numentries], dtype=numpy.int64)
        self._cache = cache
        self._basketcache = basketcache
        self._keycache = keycache
        self._localsource = None
        self._xrootdsource = None
        self._httpsource = None
        self._executor = executor
        return self

    @classmethod
    def _frompaths(cls, paths, uuids, treepath, branchname, chunksize, interpretation, globalentryoffset, cache, basketcache, keycache, localsource, xrootdsource, httpsource, executor):
        self = cls.__new__(cls)
        self._onlybranch = None
        self._paths = paths
        self._uuids = uuids
        self._treepath = treepath
        self._branchname = branchname
        self._chunksize = chunksize
        self._interpretation = interpretation
        self._globalentryoffset = globalentryoffset
        self._cache = cache
        self._basketcache = basketcache
        self._keycache = keycache
        self._localsource = localsource
        self._xrootdsource = xrootdsource
        self._httpsource = httpsource
        self._executor = executor
        return self

    def __repr__(self):
        if isinstance(self._branchname, str):
            branchname = self._branchname
        else:
            branchname = self._branchname.decode("ascii")
        return "<LazyArray {0} at {1:012x}>".format(repr(branchname), id(self))

    def __str__(self):
        if len(self) > 6:
            return numpy.array_str(self[:3], max_line_width=numpy.inf).rstrip("]") + " ... " + numpy.array_str(self[-3:], max_line_width=numpy.inf).lstrip("[")
        else:
            return numpy.array_str(str, max_line_width=numpy.inf)

    def __len__(self):
        return int(self._globalentryoffset[-1])

    @property
    def shape(self):
        if isinstance(self._interpretation, asdtype):
            return (len(self),) + self._interpretation.todims
        else:
            return (len(self),)

    @property
    def dtype(self):
        if isinstance(self._interpretation, asdtype):
            return self._interpretation.todtype
        else:
            return numpy.dtype(numpy.object_)

    @staticmethod
    def _cachekey(uuid, treepath):
        return "{0};{1}".format(base64.b64encode(uuid).decode("ascii"), _bytesid(treepath).decode("ascii"))

    def _tree(self, filenum):
        cachekey = LazyArray._cachekey(self._uuids[filenum], self._treepath)
        tree = self._cache.get(cachekey, None)
        if tree is None:
            tree = uproot.rootio.open(self._paths[filenum], localsource=self._localsource, xrootdsource=self._xrootdsource, httpsource=self._httpsource)[self._treepath]
            self._cache[cachekey] = tree
        return tree

    def _piece(self, filenum, start, stop, step):
        if step > 0:
            entrystart = start
            entrystop = stop
        elif stop is None:
            entrystart = 0
            entrystop = start + 1
        else:
            entrystart = stop + 1
            entrystop = start + 1

        if self._onlybranch is None:
            tree = self._tree(filenum)
            array = tree[self._branchname].array(interpretation=self._interpretation, entrystart=entrystart, entrystop=entrystop, cache=None, basketcache=self._basketcache, keycache=self._keycache, executor=self._executor, blocking=True)
        else:
            array = self._onlybranch.array(interpretation=self._interpretation, entrystart=entrystart, entrystop=entrystop, cache=None, basketcache=self._basketcache, keycache=self._keycache, executor=self._executor, blocking=True)

        if step < 0:
            array = array[::step]
        return array

    def __getslice__(self, start, end):
        return self.__getitem__(slice(start, end))

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(self._globalentryoffset[-1])
            if step > 0:
                step_filenum = 1
                start_filenum = self._globalentryoffset.searchsorted(start, side="right") - 1
                stop_filenum = self._globalentryoffset.searchsorted(stop, side="right")
            else:
                step_filenum = -1
                start_filenum = self._globalentryoffset.searchsorted(start, side="right") - 1
                stop_filenum = self._globalentryoffset.searchsorted(stop, side="right") - 2
                if stop_filenum < 0:
                    stop_filenum = None

            shape = (max(0, (stop - start + (step - (1 if step > 0 else -1))) // step),)
            if isinstance(self._interpretation, asdtype):
                shape = shape + self._interpretation.todims

            out = numpy.empty(shape, dtype=self.dtype)
            pointer = 0

            skip = 0
            if start_filenum >= 0:
                for filenum in range(*slice(start_filenum, stop_filenum, step_filenum).indices(len(self._paths))):
                    filestart = self._globalentryoffset[filenum]
                    filestop = self._globalentryoffset[filenum + 1]

                    if step_filenum == 1:
                        if start > filestart:
                            local_start = start - filestart
                        else:
                            local_start = skip

                        if stop < filestop:
                            local_stop = stop - filestart
                        else:
                            local_stop = filestop - filestart

                        size = local_stop - local_start

                    else:
                        if start < filestop:
                            local_start = start - filestart
                        else:
                            local_start = filestop - filestart - 1 - skip

                        if stop >= filestart:
                            local_stop = stop - filestart
                            size = local_start + 1 - local_stop
                        else:
                            local_stop = None
                            size = local_start + 1
                    
                    piece = self._piece(filenum, local_start, local_stop, step)
                    skip = int(math.ceil(size / float(abs(step)))) * abs(step) - size

                    tmp = pointer

                    if isinstance(piece, numpy.ndarray):
                        out[pointer : pointer + len(piece)] = piece
                        pointer += len(piece)
                    else:
                        for x in piece:
                            out[pointer] = x
                            pointer += 1

            assert pointer == len(out)
            return out

        elif isinstance(index, numbers.Integral):
            lenself = self._globalentryoffset[-1]
            if index < 0:
                normindex = index + lenself
            else:
                normindex = index
            if normindex >= lenself:
                raise IndexError("index {0} out of range for LazyArray of length {1}".format(index, lenself))

            filenum = self._globalentryoffset.searchsorted(normindex, side="right") - 1
            localindex = normindex - self._globalentryoffset[filenum]

            return self._piece(filenum, localindex, localindex + 1, 1)[0]

        else:
            out = self.__getitem__(index[0])
            if len(index) > 1:
                for i in range(len(out)):
                    out[i] = out[i][index[1:]]
            return out

    @property
    def dask(self):
        import uproot._connect.to_dask
        return uproot._connect.to_dask.LazyArray_dask(self)
