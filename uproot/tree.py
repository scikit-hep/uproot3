#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from __future__ import absolute_import

import base64
import codecs
import glob
import importlib
import inspect
import itertools
import math
import numbers
import os
import re
import struct
import sys
import threading
from collections import namedtuple
from collections import OrderedDict
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import numpy
import cachetools

import awkward
import uproot_methods.profiles

import uproot.rootio
from uproot.rootio import _bytesid
from uproot.rootio import _memsize
from uproot.rootio import nofilter
from uproot.interp.auto import interpret
from uproot.interp.numerical import asdtype
from uproot.interp.jagged import asjagged
from uproot.interp.objects import asobj
from uproot.interp.objects import asgenobj
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
    if isinstance(x, getattr(os, "PathLike", ())):
        x = os.fspath(x)
    elif hasattr(x, "__fspath__"):
        x = x.__fspath__()
    elif x.__class__.__module__ == "pathlib":
        import pathlib
        if isinstance(x, pathlib.Path):
             x = str(x)
    parsed = urlparse(x)
    if _bytesid(parsed.scheme) == b"file" or len(parsed.scheme) == 0 or (os.name == "nt" and open._windows_absolute.match(x) is not None):
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

_filename_explode._windows_absolute = re.compile(r"^[A-Za-z]:\\")

def _normalize_awkwardlib(awkwardlib):
    if awkwardlib is None:
        return awkward
    elif isinstance(awkwardlib, str):
        return importlib.import_module(awkwardlib)
    else:
        return awkwardlib

def _normalize_entrystartstop(numentries, entrystart, entrystop):
    if entrystart is None:
        entrystart = 0
    elif entrystart < 0:
        entrystart += numentries
    entrystart = min(numentries, max(0, entrystart))

    if entrystop is None:
        entrystop = numentries
    elif entrystop < 0:
        entrystop += numentries
    entrystop = min(numentries, max(0, entrystop))

    if entrystop < entrystart:
        raise IndexError("entrystop must be greater than or equal to entrystart")

    return int(entrystart), int(entrystop)

################################################################ high-level interface

def iterate(path, treepath, branches=None, entrysteps=float("inf"), outputtype=dict, namedecode=None, reportpath=False, reportfile=False, reportentries=False, flatten=False, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, **options):
    awkward = _normalize_awkwardlib(awkwardlib)
    for tree, newbranches, globalentrystart, thispath, thisfile in _iterate(path, treepath, branches, awkward, localsource, xrootdsource, httpsource, **options):
        for start, stop, arrays in tree.iterate(branches=newbranches, entrysteps=entrysteps, outputtype=outputtype, namedecode=namedecode, reportentries=True, entrystart=0, entrystop=tree.numentries, flatten=flatten, flatname=flatname, awkwardlib=awkward, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking):

            if getattr(outputtype, "__name__", None) == "DataFrame" and getattr(outputtype, "__module__", None) == "pandas.core.frame":
                if type(arrays.index).__name__ == "MultiIndex":
                    if hasattr(arrays.index.levels[0], "array"):
                        index = arrays.index.levels[0].array   # pandas>=0.24.0
                    else:
                        index = arrays.index.levels[0].values  # pandas<0.24.0
                    awkward.numpy.add(index, globalentrystart, out=index)

                elif type(arrays.index).__name__ == "RangeIndex":
                    arrays.index._start += globalentrystart
                    arrays.index._stop += globalentrystart

                else:
                    if hasattr(arrays.index, "array"):
                        index = arrays.index.array             # pandas>=0.24.0
                    else:
                        index = arrays.index.values            # pandas<0.24.0
                    awkward.numpy.add(index, globalentrystart, out=index)

            out = (arrays,)
            if reportentries:
                out = (globalentrystart + start, globalentrystart + stop) + out
            if reportfile:
                out = (thisfile,) + out
            if reportpath:
                out = (thispath,) + out
            if len(out) == 1:
                yield out[0]
            else:
                yield out

def _iterate(path, treepath, branches, awkward, localsource, xrootdsource, httpsource, **options):
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
        file = uproot.rootio.open(path, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, **options)
        try:
            tree = file[treepath]
        except KeyError:
            continue
        listbranches = list(tree._normalize_branches(branches, awkward))

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

        yield tree, newbranches, globalentrystart, path, file
        globalentrystart += tree.numentries

################################################################ methods for TTree

class TTreeMethods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    _copycontext = True

    _vector_regex = re.compile(b"^vector<(.+)>$")
    _objectpointer_regex = re.compile(b"\((.*)\)")

    def _attachstreamer(self, branch, streamer, streamerinfosmap, isTClonesArray):
        if streamer is None:
            m = re.match(self._vector_regex, getattr(branch, "_fClassName", b""))

            if m is None:
                if branch.name in streamerinfosmap:
                    streamer = streamerinfosmap[branch.name]
                else:
                    return

            else:
                if m.group(1) in streamerinfosmap:
                    substreamer = streamerinfosmap[m.group(1)]
                    if isinstance(substreamer, uproot.rootio.TStreamerInfo):
                        streamer = uproot.rootio.TStreamerSTL.vector(None, substreamer._fName)
                    else:
                        streamer = uproot.rootio.TStreamerSTL.vector(substreamer._fType, substreamer._fTypeName)
                else:
                    return

        if isinstance(streamer, uproot.rootio.TStreamerInfo):
            if len(streamer._fElements) == 1 and isinstance(streamer._fElements[0], uproot.rootio.TStreamerBase) and streamer._fElements[0]._fName == b"TObjArray":
                if streamer._fName == b"TClonesArray":
                    return self._attachstreamer(branch, streamerinfosmap.get(branch._fClonesName, None), streamerinfosmap, True)
                else:
                    # FIXME: can only determine streamer by reading some values?
                    return

            elif len(streamer._fElements) == 1 and isinstance(streamer._fElements[0], uproot.rootio.TStreamerSTL) and streamer._fElements[0]._fName == b"This":
                return self._attachstreamer(branch, streamer._fElements[0], streamerinfosmap, isTClonesArray)

        if isinstance(streamer, uproot.rootio.TStreamerObject):
            if streamer._fTypeName == b"TClonesArray":
                return self._attachstreamer(branch, streamerinfosmap.get(branch._fClonesName, None), streamerinfosmap, True)
            else:
                return self._attachstreamer(branch, streamerinfosmap.get(streamer._fTypeName, None), streamerinfosmap, True)

        branch._streamer = streamer
        branch._isTClonesArray = isTClonesArray
        if isinstance(streamer, uproot.rootio.TStreamerSTL) and streamer._fSTLtype == uproot.const.kSTLvector:
            branch._vecstreamer = streamerinfosmap.get(re.match(self._vector_regex, streamer._fTypeName).group(1), None)
        else:
            branch._vecstreamer = None

        digDeeperTypes = (uproot.rootio.TStreamerObject, uproot.rootio.TStreamerObjectAny, uproot.rootio.TStreamerObjectPointer, uproot.rootio.TStreamerObjectAnyPointer)

        members = None
        if isinstance(streamer, uproot.rootio.TStreamerInfo):
            members = streamer.members
        elif isinstance(streamer, digDeeperTypes):
            typename = streamer._fTypeName.rstrip(b"*")
            if typename in streamerinfosmap:
                m = self._objectpointer_regex.search(streamer._fTitle)
                if typename == b'TClonesArray' and m is not None:
                    typename = m.group(1)
                members = streamerinfosmap[typename].members
        elif isinstance(streamer, uproot.rootio.TStreamerSTL):
            try:
                # FIXME: string manipulation only works for one-parameter templates
                typename = streamer._fTypeName[streamer._fTypeName.index(b"<") + 1 : streamer._fTypeName.rindex(b">")].rstrip(b"*")
            except ValueError:
                pass
            else:
                if typename in streamerinfosmap:
                    members = streamerinfosmap[typename].members

        if members is not None:
            for subbranch in branch._fBranches:
                name = subbranch._fName
                if name.startswith(branch._fName + b"."):           # drop parent branch's name
                    name = name[len(branch._fName) + 1:]

                submembers = members
                while True:                                        # drop nested struct names one at a time
                    try:
                        index = name.index(b".")
                    except ValueError:
                        break
                    else:
                        base, name = name[:index], name[index + 1:]
                        if base in submembers and isinstance(submembers[base], digDeeperTypes):
                            submembers = streamerinfosmap[submembers[base]._fTypeName.rstrip(b"*")].members

                try:
                    name = name[:name.index(b"[")]
                except ValueError:
                    pass

                self._attachstreamer(subbranch, submembers.get(name, None), streamerinfosmap, isTClonesArray)

    def _postprocess(self, source, cursor, context, parent):
        self._context = context
        self._context.treename = self.name
        self._context.speedbump = True

        for branch in self._fBranches:
            self._attachstreamer(branch, context.streamerinfosmap.get(getattr(branch, "_fClassName", None), None), context.streamerinfosmap, False)

        self._branchlookup = {}
        self._fill_branchlookup(self._branchlookup)

        leaf2branch = {}
        for branch in self.itervalues(recursive=True):
            if len(branch._fLeaves) == 1:
                leaf2branch[id(branch._fLeaves[0])] = branch

        for branch in self.itervalues(recursive=True):
            if len(branch._fLeaves) > 0:
                branch._countleaf = branch._fLeaves[0]._fLeafCount
                if branch._countleaf is not None:
                    branch._countbranch = leaf2branch.get(id(branch._countleaf), None)

        if getattr(self, "_fAliases", None) is None:
            self.aliases = {}
        else:
            self.aliases = dict((alias._fName, alias._fTitle) for alias in self._fAliases)

    def _fill_branchlookup(self, branchlookup):
        for subbranch in self._fBranches:
            subbranch._fill_branchlookup(branchlookup)
            branchlookup[subbranch.name] = subbranch

    @property
    def name(self):
        return self._fName

    @property
    def title(self):
        return self._fTitle

    @property
    def numentries(self):
        return int(self._fEntries)

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
        for branch in self._fBranches:
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

    def _ipython_key_completions_(self):
        "Support for completion of keys in an IPython kernel"
        return [item.decode("ascii") for item in self.iterkeys()]

    def values(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.itervalues(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def items(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        return list(self.iteritems(recursive=recursive, filtername=filtername, filtertitle=filtertitle, aliases=aliases))

    def allkeys(self, filtername=nofilter, filtertitle=nofilter, aliases=True):
        return self.keys(recursive=True, filtername=filtername, filtertitle=filtertitle, aliases=aliases)

    def allvalues(self, filtername=nofilter, filtertitle=nofilter):
        return self.values(recursive=True, filtername=filtername, filtertitle=filtertitle)

    def allitems(self, filtername=nofilter, filtertitle=nofilter, aliases=True):
        return self.items(recursive=True, filtername=filtername, filtertitle=filtertitle, aliases=aliases)

    def get(self, name, recursive=True, filtername=nofilter, filtertitle=nofilter, aliases=True):
        name = _bytesid(name)
        try:
            return self._branchlookup[name]
        except KeyError:
            for n, b in self.iteritems(recursive=recursive, filtername=filtername, filtertitle=filtertitle, aliases=aliases):
                if n == name:
                    self._branchlookup[name] = b
                    return b
            raise uproot.rootio._KeyError("not found: {0}\n in file: {1}".format(repr(name), self._context.sourcepath))

    def __contains__(self, name):
        try:
            self.get(name)
        except KeyError:
            return False
        else:
            return True

    def mempartitions(self, numbytes, branches=None, entrystart=None, entrystop=None, keycache=None, linear=True):
        m = _memsize(numbytes)
        if m is not None:
            numbytes = m

        if numbytes <= 0:
            raise ValueError("target numbytes must be positive")

        awkward = _normalize_awkwardlib(None)
        branches = list(self._normalize_branches(branches, awkward))
        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)

        if not linear:
            raise NotImplementedError("non-linear mempartition has not been implemented")

        relevant_numbytes = 0.0
        for branch, interpretation in branches:
            if branch._recoveredbaskets is None:
                branch._tryrecover()
            for i, key in enumerate(branch._threadsafe_iterate_keys(keycache, False)):
                start, stop = branch._entryoffsets[i], branch._entryoffsets[i + 1]
                if entrystart < stop and start < entrystop:
                    this_numbytes = key._fObjlen * (min(stop, entrystop) - max(start, entrystart)) / float(stop - start)
                    assert this_numbytes >= 0.0
                    relevant_numbytes += this_numbytes

        entrysteps = max(1, int(round(math.ceil((entrystop - entrystart) * numbytes / relevant_numbytes))))

        start, stop = entrystart, entrystart
        while stop < entrystop:
            stop = min(stop + entrysteps, entrystop)
            if stop > start:
                yield start, stop
            start = stop

    def clusters(self, branches=None, entrystart=None, entrystop=None, strict=False):
        awkward = _normalize_awkwardlib(None)
        branches = list(self._normalize_branches(branches, awkward))

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

        cursors = [BranchCursor(branch) for branch, interpretation in branches if branch.numbaskets > 0]

        if len(cursors) == 0:
            yield _normalize_entrystartstop(self.numentries, entrystart, entrystop)

        else:
            # everybody starts at the same entry number; if there is no such place before someone runs out of baskets, there will be an exception
            leadingstart = max(cursor.entrystart for cursor in cursors)
            while not all(cursor.entrystart == leadingstart for cursor in cursors):
                for cursor in cursors:
                    while cursor.entrystart < leadingstart:
                        cursor.basketstart += 1
                        cursor.basketstop += 1
                leadingstart = max(cursor.entrystart for cursor in cursors)

            entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)

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

    def array(self, branch, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        return self.get(branch).array(interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, flatten=flatten, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=blocking)

    def arrays(self, branches=None, outputtype=dict, namedecode=None, entrystart=None, entrystop=None, flatten=False, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        awkward = _normalize_awkwardlib(awkwardlib)
        branches = list(self._normalize_branches(branches, awkward))
        if flatten is None:
            branches = [(branch, interpretation) for branch, interpretation in branches if not isinstance(interpretation, asjagged)]
            flatten = False

        # for the case of outputtype == pandas.DataFrame, do some preparation to fill DataFrames efficiently
        ispandas = getattr(outputtype, "__name__", None) == "DataFrame" and getattr(outputtype, "__module__", None) == "pandas.core.frame"
        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)

        # start the job of filling the arrays
        futures = [(branch.name if namedecode is None else branch.name.decode(namedecode), interpretation, branch.array(interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, flatten=(flatten and not ispandas), awkwardlib=awkward, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, blocking=False)) for branch, interpretation in branches]

        # make functions that wait for the filling job to be done and return the right outputtype
        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [codecs.ascii_decode(branch.name, "replace")[0] if namedecode is None else branch.name.decode(namedecode) for branch, interpretation in branches])
            def wait():
                return outputtype(*[future() for name, interpretation, future in futures])

        elif ispandas:
            import uproot._connect._pandas
            def wait():
                return uproot._connect._pandas.futures2df(futures, outputtype, entrystart, entrystop, flatten, flatname, awkward)

        elif isinstance(outputtype, type) and issubclass(outputtype, dict):
            def wait():
                return outputtype((name, future()) for name, interpretation, future in futures)

        elif isinstance(outputtype, type) and issubclass(outputtype, (list, tuple)):
            def wait():
                return outputtype(future() for name, interpretation, future in futures)

        else:
            def wait():
                return outputtype(*[future() for name, interpretation, future in futures])

        # if blocking, return the result of that function; otherwise, the function itself
        if blocking:
            return wait()
        else:
            return wait

    def lazyarray(self, branch, interpretation=None, entrysteps=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, persistvirtual=False):
        return self.get(branch).lazyarray(interpretation=interpretation, entrysteps=entrysteps, entrystart=entrystart, entrystop=entrystop, flatten=flatten, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, persistvirtual=persistvirtual)

    def lazyarrays(self, branches=None, namedecode="utf-8", entrysteps=None, entrystart=None, entrystop=None, flatten=False, profile=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, persistvirtual=False):
        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)
        entrysteps = list(self._normalize_entrysteps(entrysteps, branches, entrystart, entrystop, keycache))
        awkward = _normalize_awkwardlib(awkwardlib)
        branches = list(self._normalize_branches(branches, awkward))

        lazytree = _LazyTree(self._context.sourcepath, self._context.treename, self, dict((b.name, x) for b, x in branches), flatten, awkward.__name__, basketcache, keycache, executor)

        out = awkward.Table()
        for branch, interpretation in branches:
            inner = interpretation
            while isinstance(inner, asjagged):
                inner = inner.content
            if isinstance(inner, asobj) and getattr(inner.cls, "_arraymethods", None) is not None:
                VirtualArray = awkward.Methods.mixin(inner.cls._arraymethods, awkward.VirtualArray)
            elif isinstance(inner, asgenobj) and getattr(inner.generator.cls, "_arraymethods", None) is not None:
                VirtualArray = awkward.Methods.mixin(inner.generator.cls._arraymethods, awkward.VirtualArray)
            else:
                VirtualArray = awkward.VirtualArray

            chunks = []
            counts = []
            for start, stop in entrysteps:
                chunks.append(VirtualArray(lazytree, (branch.name, start, stop), cache=cache, type=awkward.type.ArrayType(stop - start, interpretation.type), persistvirtual=persistvirtual))
                counts.append(stop - start)
            name = branch.name.decode("ascii") if namedecode is None else branch.name.decode(namedecode)
            out[name] = awkward.ChunkedArray(chunks, counts)

        if profile is not None:
            out = uproot_methods.profiles.transformer(profile)(out)
        return out

    def _normalize_entrysteps(self, entrysteps, branches, entrystart, entrystop, keycache):
        numbytes = _memsize(entrysteps)
        if numbytes is not None:
            return self.mempartitions(numbytes, branches=branches, entrystart=entrystart, entrystop=entrystop, keycache=keycache, linear=True)
        if isinstance(entrysteps, string_types):
            raise ValueError("string {0} does not match the memory size pattern (number followed by B/kB/MB/GB/etc.)".format(repr(entrysteps)))

        if entrysteps is None:
            return self.clusters(branches, entrystart=entrystart, entrystop=entrystop, strict=False)

        elif entrysteps == float("inf"):
            return [(entrystart, min(entrystop, self.numentries))]

        elif isinstance(entrysteps, (numbers.Integral, numpy.integer)):
            entrystepsize = entrysteps
            if entrystepsize <= 0:
                raise ValueError("if an integer, entrysteps must be positive")

            effectivestop = min(entrystop, self.numentries)
            starts = numpy.arange(entrystart, effectivestop, entrystepsize)
            stops = numpy.append(starts[1:], effectivestop)
            return zip(starts, stops)
                    
        else:
            try:
                iter(entrysteps)
            except TypeError:
                raise TypeError("entrysteps must be None for cluster iteration, a positive integer for equal steps in number of entries (inf for maximal), a memory size string (number followed by B/kB/MB/GB/etc.), or an iterable of 2-tuples for explicit entry starts (inclusive) and stops (exclusive)")
            return entrysteps

    def iterate(self, branches=None, entrysteps=None, outputtype=dict, namedecode=None, reportentries=False, entrystart=None, entrystop=None, flatten=False, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        if keycache is None:
            keycache = {}

        if basketcache is None:
            basketcache = {}
            explicit_basketcache = False
        else:
            explicit_basketcache = True

        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)
        entrysteps = self._normalize_entrysteps(entrysteps, branches, entrystart, entrystop, keycache)
        awkward = _normalize_awkwardlib(awkwardlib)
        branches = list(self._normalize_branches(branches, awkward))

        # for the case of outputtype == pandas.DataFrame, do some preparation to fill DataFrames efficiently
        ispandas = getattr(outputtype, "__name__", None) == "DataFrame" and getattr(outputtype, "__module__", None) == "pandas.core.frame"
            
        def evaluate(branch, interpretation, future, past, cachekey, pythonize):
            if future is None:
                return past
            else:
                out = interpretation.finalize(future(), branch)
                if cache is not None:
                    cache[cachekey] = out
                if flatten and isinstance(interpretation, asjagged):
                    return out.flatten()
                elif pythonize:
                    return list(out)
                else:
                    return out

        if outputtype == namedtuple:
            outputtype = namedtuple("Arrays", [codecs.ascii_decode(branch.name, "replace")[0] if namedecode is None else branch.name.decode(namedecode) for branch, interpretation in branches])
            def wrap_for_python_scope(futures, start, stop):
                return lambda: outputtype(*[evaluate(branch, interpretation, future, past, cachekey, False) for branch, interpretation, future, past, cachekey in futures])

        elif ispandas:
            import uproot._connect._pandas
            def wrap_for_python_scope(futures, start, stop):
                def wrap_again(branch, interpretation, future):
                    return lambda: interpretation.finalize(future(), branch)
                return lambda: uproot._connect._pandas.futures2df([(branch.name, interpretation, wrap_again(branch, interpretation, future)) for branch, interpretation, future, past, cachekey in futures], outputtype, start, stop, flatten, flatname, awkward)

        elif isinstance(outputtype, type) and issubclass(outputtype, dict):
            def wrap_for_python_scope(futures, start, stop):
                return lambda: outputtype((branch.name if namedecode is None else branch.name.decode(namedecode), evaluate(branch, interpretation, future, past, cachekey, False)) for branch, interpretation, future, past, cachekey in futures)

        elif isinstance(outputtype, type) and issubclass(outputtype, (list, tuple)):
            def wrap_for_python_scope(futures, start, stop):
                return lambda: outputtype(evaluate(branch, interpretation, future, past, cachekey, False) for branch, interpretation, future, past, cachekey in futures)

        else:
            def wrap_for_python_scope(futures, start, stop):
                return lambda: outputtype(*[evaluate(branch, interpretation, future, past, cachekey, False) for branch, interpretation, future, past, cachekey in futures])

        for start, stop in entrysteps:
            start = max(start, entrystart)
            stop = min(stop, entrystop)
            if start > stop:
                continue

            futures = []
            for branch, interpretation in branches:
                cachekey = branch._cachekey(interpretation, start, stop)

                if branch.numbaskets == 0:
                    futures.append((branch, interpretation, interpretation.empty, None, cachekey))

                else:
                    basketstart, basketstop = branch._basketstartstop(start, stop)
                    basket_itemoffset = branch._basket_itemoffset(interpretation, basketstart, basketstop, keycache)
                    basket_entryoffset = branch._basket_entryoffset(basketstart, basketstop)

                    if cache is not None:
                        out = cache.get(cachekey, None)
                        if out is not None:
                            futures.append((branch, interpretation, None, out, cachekey))
                            continue
                    future = branch._step_array(interpretation, basket_itemoffset, basket_entryoffset, start, stop, awkward, basketcache, keycache, executor, explicit_basketcache)
                    futures.append((branch, interpretation, future, None, cachekey))

            out = wrap_for_python_scope(futures, start, stop)

            if blocking:
                out = out()

            if reportentries:
                yield start, stop, out
            else:
                yield out

    def _format(self, indent=""):
        # TODO: add TTree data to the bottom of this
        out = []
        for branch in self._fBranches:
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
        awkward = _normalize_awkwardlib(None)
        return [b.name for b, i in self._normalize_branches(branches, awkward, allownone=False, allowcallable=False, allowdict=False, allowstring=True)]

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

    def _normalize_branches(self, arg, awkward, allownone=True, allowcallable=True, allowdict=True, allowstring=True, aliases=True):
        if allownone and arg is None:                      # no specification; read all branches
            for branch in self.allvalues():                # that have interpretations
                interpretation = interpret(branch, awkward)
                if interpretation is not None:
                    yield branch, interpretation

        elif allowcallable and callable(arg):
            for branch in self.allvalues():
                result = arg(branch)
                if result is None or result is False:
                    pass
                elif result is True:                       # function is a filter
                    interpretation = interpret(branch, awkward)
                    if interpretation is not None:
                        yield branch, interpretation
                else:                                      # function is giving interpretations
                    yield branch, branch._normalize_dtype(result, awkward)

        elif allowdict and isinstance(arg, dict):
            for word, interpretation in arg.items():
                word = _bytesid(word)

                isregex = re.match(self._branch_regex, word)
                if isregex is not None:
                    regex, flags = isregex.groups()
                    for name, branch in self.iteritems(recursive=True, aliases=aliases):
                        if re.match(regex, name, self._branch_flags(flags)):
                            yield branch, branch._normalize_dtype(interpretation, awkward)

                elif b"*" in word or b"?" in word or b"[" in word:
                    for name, branch in self.iteritems(recursive=True, aliases=aliases):
                        if name == word or glob.fnmatch.fnmatchcase(name, word):
                            yield branch, branch._normalize_dtype(interpretation, awkward)

                else:
                    branch = self.get(word, aliases=aliases)
                    yield branch, branch._normalize_dtype(interpretation, awkward)

        elif allowstring and isinstance(arg, string_types):
            for x in self._normalize_branches([arg], awkward):
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
                                interpretation = interpret(branch, awkward)
                                if interpretation is None:
                                    if name == word:
                                        raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(branch.name), self._context.sourcepath))
                                else:
                                    yield branch, interpretation

                    elif b"*" in word or b"?" in word or b"[" in word:
                        for name, branch in self.iteritems(recursive=True, aliases=aliases):
                            if name == word or glob.fnmatch.fnmatchcase(name, word):
                                interpretation = interpret(branch, awkward)
                                if interpretation is None:
                                    if name == word:
                                        raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(branch.name), self._context.sourcepath))
                                else:
                                    yield branch, interpretation

                    else:
                        branch = self.get(word, aliases=aliases)
                        interpretation = interpret(branch, awkward)
                        if interpretation is None:
                            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(branch.name), self._context.sourcepath))
                        else:
                            yield branch, interpretation

    def __len__(self):
        return self.numentries

    def __getitem__(self, name):
        return self.get(name)

    def __iter__(self):
        # prevent Python's attempt to interpret __len__ and __getitem__ as iteration
        raise TypeError("'TTree' object is not iterable")

    @property
    def pandas(self):
        import uproot._connect._pandas
        return uproot._connect._pandas.TTreeMethods_pandas(self)

################################################################ methods for TBranch

class TBranchMethods(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.rootio.ROOTObject.__metaclass__,), {})

    def _postprocess(self, source, cursor, context, parent):
        self._source = source
        self._context = context
        self._streamer = None
        self._interpretation = None

        self._numgoodbaskets = 0
        for i, x in enumerate(self._fBasketSeek):
            if x == 0 or i == self._fWriteBasket:
                break
            self._numgoodbaskets += 1

        if self.numentries == self._fBasketEntry[self._numgoodbaskets]:
            self._recoveredbaskets = []
            self._entryoffsets = self._fBasketEntry[: self._numgoodbaskets + 1].tolist()
            self._recoverylock = None
        else:
            self._recoveredbaskets = None
            self._entryoffsets = None
            self._recoverylock = threading.Lock()

        self._countbranch = None
        self._tree_iofeatures = 0
        if hasattr(parent, "_fIOFeatures"):
            self._tree_iofeatures = parent._fIOFeatures._fIOBits

    def _fill_branchlookup(self, branchlookup):
        for subbranch in self._fBranches:
            subbranch._fill_branchlookup(branchlookup)
            branchlookup[subbranch.name] = subbranch

    @property
    def name(self):
        return self._fName

    @property
    def title(self):
        return self._fTitle

    @property
    def interpretation(self):
        awkward = _normalize_awkwardlib(None)
        if self._interpretation is None:
            self._interpretation = interpret(self, awkward)
        return self._interpretation

    @property
    def countbranch(self):
        return self._countbranch

    @property
    def countleaf(self):
        return self._countleaf

    @property
    def numentries(self):
        return int(self._fEntries)   # or self._fEntryNumber?

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
        for branch in self._fBranches:
            if filtername(branch.name) and filtertitle(branch.title):
                yield branch
            if recursive:
                for x in branch.itervalues(recursive, filtername, filtertitle):
                    yield x

    def iteritems(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        for branch in self._fBranches:
            if filtername(branch.name) and filtertitle(branch.title):
                yield branch.name, branch
            if recursive:
                for x in branch.iteritems(recursive, filtername, filtertitle):
                    yield x

    def keys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        return list(self.iterkeys(recursive=recursive, filtername=filtername, filtertitle=filtertitle))

    def _ipython_key_completions_(self):
        "Support for completion of keys in an IPython kernel"
        return [item.decode("ascii") for item in self.iterkeys()]

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
        raise uproot.rootio._KeyError("not found: {0}\n in file: {1}".format(repr(name), self._context.sourcepath))

    @property
    def numbaskets(self):
        if self._recoveredbaskets is None:
            self._tryrecover()
        return self._numgoodbaskets + len(self._recoveredbaskets)

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
                if not complete or all(hasattr(x, "border") for x in keys):
                    for key in keys:
                        yield key
                    done = True

        if not done:
            keysource = self._source.threadlocal()
            try:
                for i in range(basketstart, basketstop):
                    key = None if keycache is None else keycache.get(self._keycachekey(i), None)
                    if key is None or (complete and not hasattr(key, "border")):
                        key = self._basketkey(keysource, i, complete)
                        if keycache is not None:
                            keycache[self._keycachekey(i)] = key
                        yield key
                    else:
                        yield key
            finally:
                keysource.dismiss()

    def uncompressedbytes(self, keycache=None):
        return sum(key._fObjlen for key in self._threadsafe_iterate_keys(keycache, False))

    def compressedbytes(self, keycache=None):
        return sum(key._fNbytes - key._fKeylen for key in self._threadsafe_iterate_keys(keycache, False))

    def compressionratio(self, keycache=None):
        numer, denom = 0, 0
        for key in self._threadsafe_iterate_keys(keycache, False):
            numer += key._fObjlen
            denom += key._fNbytes - key._fKeylen
        return float(numer) / float(denom)

    def _normalize_dtype(self, interpretation, awkward):
        if inspect.isclass(interpretation) and issubclass(interpretation, awkward.numpy.generic):
            return self._normalize_dtype(awkward.numpy.dtype(interpretation), awkward)

        elif isinstance(interpretation, awkward.numpy.dtype):      # user specified a Numpy dtype
            default = interpret(self, awkward)
            if isinstance(default, (asdtype, asjagged)):
                return default.to(interpretation)
            else:
                raise ValueError("cannot cast branch {0} (default interpretation {1}) as dtype {2}".format(repr(self.name), default, interpretation))

        elif isinstance(interpretation, awkward.numpy.ndarray):    # user specified a Numpy array
            default = interpret(self, awkward)
            if isinstance(default, asdtype):
                return default.toarray(interpretation)
            else:
                raise ValueError("cannot cast branch {0} (default interpretation {1}) as dtype {2}".format(repr(self.name), default, interpretation))

        elif not isinstance(interpretation, uproot.interp.interp.Interpretation):
            raise TypeError("branch interpretation must be an Interpretation, not {0} (type {1})".format(interpretation, type(interpretation)))

        else:
            return interpretation

    def _normalize_interpretation(self, interpretation, awkward):
        if interpretation is None:
            interpretation = interpret(self, awkward)
        else:
            interpretation = self._normalize_dtype(interpretation, awkward)

        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(self.name), self._context.sourcepath))

        if interpretation.awkward is not awkward:
            interpretation = interpretation.awkwardlib(awkward)

        return interpretation

    def numitems(self, interpretation=None, keycache=None):
        awkward = _normalize_awkwardlib(None)
        interpretation = self._normalize_interpretation(interpretation, awkward)
        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(self.name), self._context.sourcepath))
        if self._recoveredbaskets is None:
            self._tryrecover()
        return sum(interpretation.numitems(key.border, self.basket_numentries(i)) for i, key in enumerate(self._threadsafe_iterate_keys(keycache, True)))

    @property
    def compression(self):
        try:
            return uproot.source.compressed.Compression(self._fCompress)
        except ValueError:
            return self._context.compression

    def basket_entrystart(self, i):
        if self._recoveredbaskets is None:
            self._tryrecover()
        if 0 <= i < self.numbaskets:
            return self._entryoffsets[i]
        else:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

    def basket_entrystop(self, i):
        if self._recoveredbaskets is None:
            self._tryrecover()
        if 0 <= i < self.numbaskets:
            return self._entryoffsets[i + 1]
        else:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

    def basket_numentries(self, i):
        if self._recoveredbaskets is None:
            self._tryrecover()
        if 0 <= i < self.numbaskets:
            return self._entryoffsets[i + 1] - self._entryoffsets[i]
        else:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

    def basket_uncompressedbytes(self, i, keycache=None):
        if self._recoveredbaskets is None:
            self._tryrecover()
        return self._threadsafe_key(i, keycache, False)._fObjlen

    def basket_compressedbytes(self, i):
        if self._recoveredbaskets is None:
            self._tryrecover()
        key = self._threadsafe_key(i, keycache, False)
        return key._fNbytes - key._fKeylen

    def basket_numitems(self, i, interpretation=None, keycache=None):
        if self._recoveredbaskets is None:
            self._tryrecover()
        awkward = _normalize_awkwardlib(None)
        interpretation = self._normalize_interpretation(interpretation, awkward)
        key = self._threadsafe_key(i, keycache, True)
        return interpretation.numitems(key.border, self.basket_numentries(i))

    def _localentries(self, i, entrystart, entrystop):
        local_entrystart = max(0, entrystart - self.basket_entrystart(i))
        local_entrystop  = max(0, min(entrystop - self.basket_entrystart(i), self.basket_entrystop(i) - self.basket_entrystart(i)))
        return local_entrystart, local_entrystop

    def _basket(self, i, interpretation, local_entrystart, local_entrystop, awkward, basketcache, keycache):
        basketdata = None
        if basketcache is not None:
            basketcachekey = self._basketcachekey(i)
            basketdata = basketcache.get(basketcachekey, None)

        key = self._threadsafe_key(i, keycache, True)

        if basketdata is None:
            basketdata = key.basketdata()

        if basketcache is not None:
            basketcache[basketcachekey] = basketdata

        if key._fObjlen == key.border:
            data, byteoffsets = basketdata, None

            if self._countbranch is not None and awkward.numpy.uint8(self._tree_iofeatures) & awkward.numpy.uint8(uproot.const.kGenerateOffsetMap) != 0:
                counts = self._countbranch.array(entrystart=(local_entrystart + self.basket_entrystart(i)),
                                                 entrystop=(local_entrystop + self.basket_entrystart(i)))
                itemsize = 1
                if isinstance(interpretation, asjagged):
                    itemsize = interpretation.content.fromdtype.itemsize
                awkward.numpy.multiply(counts, itemsize, counts)
                byteoffsets = awkward.numpy.empty(len(counts) + 1, dtype=awkward.numpy.int32)
                byteoffsets[0] = 0
                awkward.numpy.cumsum(counts, out=byteoffsets[1:])

        else:
            data = basketdata[:key.border]
            byteoffsets = awkward.numpy.empty((key._fObjlen - key.border - 4) // 4, dtype=awkward.numpy.int32)  # native endian
            byteoffsets[:-1] = basketdata[key.border + 4 : -4].view(">i4")                     # read as big-endian and convert
            byteoffsets[-1] = key._fLast
            awkward.numpy.subtract(byteoffsets, key._fKeylen, byteoffsets)

        return interpretation.fromroot(data, byteoffsets, local_entrystart, local_entrystop)

    def basket(self, i, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None):
        awkward = _normalize_awkwardlib(awkwardlib)
        interpretation = self._normalize_interpretation(interpretation, awkward)
        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(self.name), self._context.sourcepath))
        if self._recoveredbaskets is None:
            self._tryrecover()

        if not 0 <= i < self.numbaskets:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)
        local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)
        entrystart = self.basket_entrystart(i) + local_entrystart
        entrystop = self.basket_entrystart(i) + local_entrystop
        numentries = local_entrystop - local_entrystart

        if cache is not None:
            cachekey = self._cachekey(interpretation, entrystart, entrystop)
            out = cache.get(cachekey, None)
            if out is not None:
                if flatten and isinstance(interpretation, asjagged):
                    return out.content
                else:
                    return out

        source = self._basket(i, interpretation, local_entrystart, local_entrystop, awkward, basketcache, keycache)
        numitems = interpretation.source_numitems(source)

        destination = interpretation.destination(numitems, numentries)
        interpretation.fill(source, destination, 0, numitems, 0, numentries)
        out = interpretation.finalize(destination, self)

        if cache is not None:
            cache[cachekey] = out
        if flatten and isinstance(interpretation, asjagged):
            return out.content
        else:
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

    def baskets(self, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, reportentries=False, executor=None, blocking=True):
        awkward = _normalize_awkwardlib(awkwardlib)
        interpretation = self._normalize_interpretation(interpretation, awkward)
        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(self.name), self._context.sourcepath))
        if self._recoveredbaskets is None:
            self._tryrecover()

        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)
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
                basket = self.basket(j + basketstart, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, flatten=flatten, awkwardlib=awkward, cache=cache, basketcache=basketcache, keycache=keycache)
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

    def iterate_baskets(self, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, reportentries=False):
        awkward = _normalize_awkwardlib(awkwardlib)
        interpretation = self._normalize_interpretation(interpretation, awkward)
        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(self.name), self._context.sourcepath))
        if self._recoveredbaskets is None:
            self._tryrecover()

        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)

        for i in range(self.numbaskets):
            if entrystart < self.basket_entrystop(i) and self.basket_entrystart(i) < entrystop:
                local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)

                if local_entrystop > local_entrystart:
                    if reportentries:
                        yield (local_entrystart + self.basket_entrystart(i),
                               local_entrystop + self.basket_entrystart(i),
                               self.basket(i, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, flatten=flatten, awkwardlib=awkward, cache=cache, basketcache=basketcache, keycache=keycache))
                    else:
                        yield self.basket(i, interpretation=interpretation, entrystart=entrystart, entrystop=entrystop, flatten=flatten, awkwardlib=awkward, cache=cache, basketcache=basketcache, keycache=keycache)

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

    def array(self, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        if self._recoveredbaskets is None:
            self._tryrecover()
        awkward = _normalize_awkwardlib(awkwardlib)
        interpretation = self._normalize_interpretation(interpretation, awkward)
        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(self.name), self._context.sourcepath))
        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)
        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if basketstart is not None and basketstop is not None and self._source.parent() is not None:
            self._source.parent().preload([self._fBasketSeek[i] for i in range(basketstart, basketstop)])

        if cache is not None:
            cachekey = self._cachekey(interpretation, entrystart, entrystop)
            out = cache.get(cachekey, None)
            if out is not None:
                if flatten and isinstance(interpretation, asjagged):
                    out = out.content
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
            keycache = {}

        basket_itemoffset = self._basket_itemoffset(interpretation, basketstart, basketstop, keycache)
        basket_entryoffset = self._basket_entryoffset(basketstart, basketstop)

        destination = interpretation.destination(basket_itemoffset[-1], basket_entryoffset[-1])

        def fill(j):
            try:
                i = j + basketstart
                local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)
                source = self._basket(i, interpretation, local_entrystart, local_entrystop, awkward, basketcache, keycache)

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
            if flatten and isinstance(interpretation, asjagged):
                return out.content
            else:
                return out

        if blocking:
            return wait()
        else:
            return wait

    def _step_array(self, interpretation, basket_itemoffset, basket_entryoffset, entrystart, entrystop, awkward, basketcache, keycache, executor, explicit_basketcache):
        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(self.name), self._context.sourcepath))
        if self._recoveredbaskets is None:
            self._tryrecover()

        basketstart, basketstop = self._basketstartstop(entrystart, entrystop)

        if basketstart is None:
            return lambda: interpretation.empty()

        destination = interpretation.destination(basket_itemoffset[-1], basket_entryoffset[-1])

        def fill(j):
            try:
                i = j + basketstart
                local_entrystart, local_entrystop = self._localentries(i, entrystart, entrystop)
                source = self._basket(i, interpretation, local_entrystart, local_entrystop, awkward, basketcache, keycache)

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

    def mempartitions(self, numbytes, entrystart=None, entrystop=None, keycache=None, linear=True):
        m = _memsize(numbytes)
        if m is not None:
            numbytes = m

        if numbytes <= 0:
            raise ValueError("target numbytes must be positive")

        awkward = _normalize_awkwardlib(None)
        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)

        if not linear:
            raise NotImplementedError("non-linear mempartition has not been implemented")

        relevant_numbytes = 0.0
        if self._recoveredbaskets is None:
            self._tryrecover()
        for i, key in enumerate(self._threadsafe_iterate_keys(keycache, False)):
            start, stop = self._entryoffsets[i], self._entryoffsets[i + 1]
            if entrystart < stop and start < entrystop:
                this_numbytes = key._fObjlen * (min(stop, entrystop) - max(start, entrystart)) / float(stop - start)
                assert this_numbytes >= 0.0
                relevant_numbytes += this_numbytes

        entrysteps = max(1, round(math.ceil((entrystop - entrystart) * numbytes / relevant_numbytes)))

        start, stop = entrystart, entrystart
        while stop < entrystop:
            stop = min(stop + entrysteps, entrystop)
            if stop > start:
                yield start, stop
            start = stop

    def _normalize_entrysteps(self, entrysteps, entrystart, entrystop, keycache):
        numbytes = _memsize(entrysteps)
        if numbytes is not None:
            return self.mempartitions(numbytes, entrystart=entrystart, entrystop=entrystop, keycache=keycache, linear=True)
        if isinstance(entrysteps, string_types):
            raise ValueError("string {0} does not match the memory size pattern (number followed by B/kB/MB/GB/etc.)".format(repr(entrysteps)))

        if entrysteps is None:
            if self._recoveredbaskets is None:
                self._tryrecover()
            return [(self._entryoffsets[i], self._entryoffsets[i + 1]) for i in range(self.numbaskets) if entrystart < self._entryoffsets[i + 1] and entrystop >= self._entryoffsets[i]]

        elif entrysteps == float("inf"):
            return [(entrystart, min(entrystop, self.numentries))]

        elif isinstance(entrysteps, (numbers.Integral, numpy.integer)):
            entrystepsize = entrysteps
            if entrystepsize <= 0:
                raise ValueError("if an integer, entrysteps must be positive")

            effectivestop = min(entrystop, self.numentries)
            starts = numpy.arange(entrystart, effectivestop, entrystepsize)
            stops = numpy.append(starts[1:], effectivestop)
            return zip(starts, stops)

        else:
            try:
                iter(entrysteps)
            except TypeError:
                raise TypeError("entrysteps must be None for cluster iteration, a positive integer for equal steps in number of entries (inf for maximal), a memory size string (number followed by B/kB/MB/GB/etc.), or an iterable of 2-tuples for explicit entry starts (inclusive) and stops (exclusive)")
            return entrysteps

    def lazyarray(self, interpretation=None, entrysteps=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, persistvirtual=False):
        if self._recoveredbaskets is None:
            self._tryrecover()
        awkward = _normalize_awkwardlib(awkwardlib)
        interpretation = self._normalize_interpretation(interpretation, awkward)
        if interpretation is None:
            raise ValueError("cannot interpret branch {0} as a Python type\n   in file: {1}".format(repr(self.name), self._context.sourcepath))
        entrystart, entrystop = _normalize_entrystartstop(self.numentries, entrystart, entrystop)
        entrysteps = self._normalize_entrysteps(entrysteps, entrystart, entrystop, keycache)

        inner = interpretation
        while isinstance(inner, asjagged):
            inner = inner.content
        if isinstance(inner, asobj) and getattr(inner.cls, "_arraymethods", None) is not None:
            VirtualArray = awkward.Methods.mixin(inner.cls._arraymethods, awkward.VirtualArray)
            chunkedarray = awkward.Methods.mixin(inner.cls._arraymethods, awkward.ChunkedArray)
        elif isinstance(inner, asgenobj) and getattr(inner.generator.cls, "_arraymethods", None) is not None:
            VirtualArray = awkward.Methods.mixin(inner.generator.cls._arraymethods, awkward.VirtualArray)
            chunkedarray = awkward.Methods.mixin(inner.generator.cls._arraymethods, awkward.ChunkedArray)
        else:
            VirtualArray = awkward.VirtualArray
            chunkedarray = awkward.ChunkedArray

        lazybranch = _LazyBranch(self._context.sourcepath, self._context.treename, self.name, self, interpretation, flatten, awkward.__name__, basketcache, keycache, executor)

        chunks = []
        counts = []
        for start, stop in entrysteps:
            numentries = stop - start
            chunks.append(VirtualArray(lazybranch, (start, stop), cache=cache, type=awkward.type.ArrayType(numentries, interpretation.type), persistvirtual=persistvirtual))
            counts.append(numentries)

        return chunkedarray(chunks, counts)

    class _BasketKey(object):
        def __init__(self, source, cursor, compression, complete):
            start = cursor.index
            self._fNbytes, self._fVersion, self._fObjlen, self._fDatime, self._fKeylen, self._fCycle, self._fSeekKey, self._fSeekPdir = cursor.fields(source, TBranchMethods._BasketKey._format_small)

            if self._fVersion > 1000:
                cursor.index = start
                self._fNbytes, self._fVersion, self._fObjlen, self._fDatime, self._fKeylen, self._fCycle, self._fSeekKey, self._fSeekPdir = cursor.fields(source, TBranchMethods._BasketKey._format_big)

            if complete:
                cursor.index = start + self._fKeylen - TBranchMethods._BasketKey._format_complete.size - 1
                self._fVersion, self._fBufferSize, self._fNevBufSize, self._fNevBuf, self._fLast = cursor.fields(source, TBranchMethods._BasketKey._format_complete)

                self.border = self._fLast - self._fKeylen

                if source.size() is not None:
                    if source.size() - self._fSeekKey < self._fNbytes:
                        s = source
                        while s.parent() is not None and s.parent() is not s:
                            s = s.parent()
                        raise ValueError("TKey declares that object has {0} bytes but only {1} remain in the file\n   in file: {2}".format(self._fNbytes, source.size() - self._fSeekKey, s.path))

                if self._fObjlen != self._fNbytes - self._fKeylen:
                    self.source = uproot.source.compressed.CompressedSource(compression, source, Cursor(self._fSeekKey + self._fKeylen), self._fNbytes - self._fKeylen, self._fObjlen)
                    self.cursor = Cursor(0)
                else:
                    self.source = source
                    self.cursor = Cursor(self._fSeekKey + self._fKeylen)

        _format_small = struct.Struct(">ihiIhhii")
        _format_big = struct.Struct(">ihiIhhqq")
        _format_complete = struct.Struct(">Hiiii")

        @property
        def fName(self):
            return "TBranchMethods._BasketKey"

        @property
        def fTitle(self):
            return "TBranchMethods._BasketKey"

        @property
        def fClassName(self):
            return "TBasket"

        def basketdata(self):
            datasource = self.source.threadlocal()
            try:
                return self.cursor.copied().bytes(datasource, self._fObjlen)
            finally:
                datasource.dismiss()

    class _RecoveredTBasket(uproot.rootio.ROOTObject):
        @classmethod
        def _readinto(cls, self, source, cursor, context, parent):
            start = cursor.index
            self._fNbytes, self._fVersion, self._fObjlen, self._fDatime, self._fKeylen, self._fCycle = cursor.fields(source, cls._format1)

            # skip the class name, name, and title
            cursor.index = start + self._fKeylen - cls._format2.size - 1
            self._fVersion, self._fBufferSize, self._fNevBufSize, self._fNevBuf, self._fLast = cursor.fields(source, cls._format2)

            # one-byte terminator
            cursor.skip(1)

            # then if you have offsets data, read them in
            if self._fNevBufSize > 8:
                byteoffsets = cursor.bytes(source, self._fNevBuf * 4 + 8)
                cursor.skip(-4)

            # there's a second TKey here, but it doesn't contain any new information (in fact, less)
            cursor.skip(self._fKeylen)

            size = self.border = self._fLast - self._fKeylen

            # the data (not including offsets)
            self.contents = cursor.bytes(source, size)

            # put the offsets back in, in the way that we expect it
            if self._fNevBufSize > 8:
                self.contents = numpy.concatenate((self.contents, byteoffsets))
                size += byteoffsets.nbytes

            self._fObjlen = size
            self._fNbytes = self._fObjlen + self._fKeylen

            return self

        _format1 = struct.Struct(">ihiIhh")
        _format2 = struct.Struct(">Hiiii")

        def basketdata(self):
            return self.contents

        @property
        def numentries(self):
            return self._fNevBuf

    def _recover(self):
        recoveredbaskets = [x for x in uproot.rootio.TObjArray.read(self._source, self._fBaskets._cursor, self._context, self, asclass=TBranchMethods._RecoveredTBasket) if x is not None]

        if self._numgoodbaskets == 0:
            entryoffsets = [0]
        else:
            entryoffsets = self._fBasketEntry[:self._numgoodbaskets + 1].tolist()

        for basket in recoveredbaskets:
            entryoffsets.append(entryoffsets[-1] + basket.numentries)

        if entryoffsets[-1] == self.numentries:
            with self._recoverylock:
                self._recoveredbaskets = recoveredbaskets
                self._entryoffsets = entryoffsets
        else:
            raise ValueError("entries in recovered baskets (offsets {0}) don't add up to total number of entries ({1})\n   in file: {2}".format(entryoffsets, self.numentries, self._context.sourcepath))

    def _tryrecover(self):
        if self._recoveredbaskets is None:
            self._recover()

    def _basketkey(self, source, i, complete):
        if 0 <= i < self._numgoodbaskets:
            return self._BasketKey(source.parent(), Cursor(self._fBasketSeek[i]), self.compression, complete)

        elif self._numgoodbaskets <= i < self.numbaskets:
            return self._recoveredbaskets[i - self._numgoodbaskets]

        else:
            raise IndexError("index {0} out of range for branch with {1} baskets".format(i, self.numbaskets))

    def _format(self, foldnames, indent="", strip=""):
        name = self._fName.decode("ascii")
        if foldnames and name.startswith(strip + "."):
            name = name[len(strip) + 1:]

        if len(name) > 26:
            out = [indent + name, indent + "{0:26s} {1:26s} {2}".format("", "(no streamer)" if self._streamer is None else self._streamer.__class__.__name__, self.interpretation)]
        else:
            out = [indent + "{0:26s} {1:26s} {2}".format(name, "(no streamer)" if self._streamer is None else self._streamer.__class__.__name__, self.interpretation)]

        for branch in self._fBranches:
            out.extend(branch._format(foldnames, indent + "  " if foldnames else indent, self._fName))
        if len(self._fBranches) > 0 and out[-1] != "":
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

################################################################ for lazy arrays

class _LazyFiles(object):
    def __init__(self, paths, treepath, branches, entrysteps, flatten, awkwardlib, basketcache, keycache, executor, persistvirtual, localsource, xrootdsource, httpsource, options):
        self.paths = paths
        self.treepath = treepath
        self.branches = branches
        self.entrysteps = entrysteps
        self.flatten = flatten
        self.awkwardlib = awkwardlib
        self.basketcache = basketcache
        self.keycache = keycache
        self.executor = executor
        self.persistvirtual = persistvirtual
        self.localsource = localsource
        self.xrootdsource = xrootdsource
        self.httpsource = httpsource
        self.options = options
        self._init()

    def _init(self):
        self.trees = cachetools.LRUCache(5)                                 # last 5 TTrees
        if self.basketcache is None:
            self.basketcache = uproot.cache.ThreadSafeArrayCache(1024**2)   # 1 MB
        if self.keycache is None:
            self.keycache = cachetools.LRUCache(10000)                      # last 10000 TKeys

    def __getstate__(self):
        return {"paths": paths,
                "treepath": treepath,
                "branches": branches,
                "entrysteps": entrysteps,
                "flatten": flatten,
                "awkwardlib": awkwardlib,
                "persistvirtual": persistvirtual,
                "localsource": localsource,
                "xrootdsource": xrootdsource,
                "httpsource": httpsource,
                "options": options}
                
    def __setstate__(self, state):
        self.paths = state["paths"]
        self.treepath = state["treepath"]
        self.branches = state["branches"]
        self.entrysteps = state["entrysteps"]
        self.flatten = state["flatten"]
        self.awkwardlib = state["awkwardlib"]
        self.basketcache = None
        self.keycache = None
        self.executor = None
        self.persistvirtual = state["persistvirtual"]
        self.localsource = state["localsource"]
        self.xrootdsource = state["xrootdsource"]
        self.httpsource = state["httpsource"]
        self.options = state["options"]
        self._init()

    def __call__(self, pathi, branchname):
        awkward = _normalize_awkwardlib(self.awkwardlib)
        tree = self.trees.get(self.paths[pathi], None)
        if tree is None:
            tree = self.trees[self.paths[pathi]] = uproot.rootio.open(self.paths[pathi])[self.treepath]
            tree.interpretations = dict((b.name, x) for b, x in tree._normalize_branches(self.branches, awkward))
        return tree[branchname].lazyarray(interpretation=tree.interpretations[branchname], entrysteps=self.entrysteps, entrystart=None, entrystop=None, flatten=self.flatten, awkwardlib=awkward, cache=None, basketcache=self.basketcache, keycache=self.keycache, executor=self.executor, persistvirtual=self.persistvirtual)

class _LazyTree(object):
    def __init__(self, path, treepath, tree, interpretation, flatten, awkwardlib, basketcache, keycache, executor):
        self.path = path
        self.treepath = treepath
        self.tree = tree
        self.interpretation = interpretation
        self.flatten = flatten
        self.awkwardlib = awkwardlib
        self.basketcache = basketcache
        self.keycache = keycache
        self.executor = executor
        self._init()

    def _init(self):
        if self.tree is None:
            self.tree = uproot.rootio.open(self.path)[self.treepath]
        if self.basketcache is None:
            self.basketcache = uproot.cache.ThreadSafeArrayCache(1024**2)   # 1 MB
        if self.keycache is None:
            self.keycache = {}                                              # unlimited

    def __getstate__(self):
        return {"path": self.path,
                "treepath": self.treepath,
                "interpretation": self.interpretation,
                "flatten": self.flatten,
                "awkwardlib": self.awkwardlib}

    def __setstate__(self, state):
        self.path = state["path"]
        self.treepath = state["treepath"]
        self.tree = None
        self.interpretation = state["interpretation"]
        self.flatten = state["flatten"]
        self.awkwardlib = state["awkwardlib"]
        self.basketcache = None
        self.keycache = None
        self.executor = None
        self._init()

    def __call__(self, branch, entrystart, entrystop):
        return self.tree[branch].array(interpretation=self.interpretation[branch], entrystart=entrystart, entrystop=entrystop, flatten=self.flatten, awkwardlib=self.awkwardlib, cache=None, basketcache=self.basketcache, keycache=self.keycache, executor=self.executor)
        
class _LazyBranch(object):
    def __init__(self, path, treepath, branchname, branch, interpretation, flatten, awkwardlib, basketcache, keycache, executor):
        self.path = path
        self.treepath = treepath
        self.branchname = branchname
        self.branch = branch
        self.interpretation = interpretation
        self.flatten = flatten
        self.awkwardlib = awkwardlib
        self.basketcache = basketcache
        self.keycache = keycache
        self.executor = executor
        self._init()

    def _init(self):
        if self.branch is None:
            self.branch = uproot.rootio.open(self.path)[self.treepath][self.branchname]
        if self.basketcache is None:
            self.basketcache = uproot.cache.ThreadSafeArrayCache(1024**2)   # 1 MB
        if self.keycache is None:
            self.keycache = {}                                              # unlimited

    def __getstate__(self):
        return {"path": self.path,
                "treepath": self.treepath,
                "branchname": self.branchname,
                "interpretation": self.interpretation,
                "flatten": self.flatten,
                "awkwardlib": self.awkwardlib}

    def __setstate__(self, state):
        self.path = state["path"]
        self.treepath = state["treepath"]
        self.branchname = state["branchname"]
        self.branch = None
        self.interpretation = state["interpretation"]
        self.flatten = state["flatten"]
        self.awkwardlib = state["awkwardlib"]
        self.basketcache = None
        self.keycache = None
        self.executor = None
        self._init()

    def __call__(self, entrystart, entrystop):
        return self.branch.array(interpretation=self.interpretation, entrystart=entrystart, entrystop=entrystop, flatten=self.flatten, awkwardlib=self.awkwardlib, cache=None, basketcache=self.basketcache, keycache=self.keycache, executor=self.executor, blocking=True)

def lazyarray(path, treepath, branchname, interpretation=None, namedecode="utf-8", entrysteps=float("inf"), flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, persistvirtual=False, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, **options):
    if interpretation is None:
        branches = branchname
    else:
        branches = {branchname: interpretation}
    out = lazyarrays(path, treepath, branches=branches, namedecode=namedecode, entrysteps=entrysteps, flatten=flatten, profile=None, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, persistvirtual=persistvirtual, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, **options)
    return out[out.columns[0]]

def lazyarrays(path, treepath, branches=None, namedecode="utf-8", entrysteps=float("inf"), flatten=False, profile=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, persistvirtual=False, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, **options):
    awkward = _normalize_awkwardlib(awkwardlib)
    if isinstance(path, string_types):
        paths = _filename_explode(path)
    else:
        paths = [y for x in path for y in _filename_explode(x)]

    path2count = numentries(path, treepath, total=False, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, executor=executor, blocking=True)

    lazyfiles = _LazyFiles(paths, treepath, branches, entrysteps, flatten, awkward.__name__, basketcache, keycache, executor, persistvirtual, localsource, xrootdsource, httpsource, options)

    for path in paths:
        file = uproot.rootio.open(path, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, **options)
        try:
            tree = file[treepath]
        except KeyError:
            continue
        branches = list(tree._normalize_branches(branches, awkward))
        break

    if branches is None:
        raise ValueError("no matching paths contained a tree named {0}".format(repr(treepath)))

    out = awkward.Table()
    for branch, interpretation in branches:
        inner = interpretation
        while isinstance(inner, asjagged):
            inner = inner.content
        if isinstance(inner, asobj) and getattr(inner.cls, "_arraymethods", None) is not None:
            VirtualArray = awkward.Methods.mixin(inner.cls._arraymethods, awkward.VirtualArray)
        elif isinstance(inner, asgenobj) and getattr(inner.generator.cls, "_arraymethods", None) is not None:
            VirtualArray = awkward.Methods.mixin(inner.generator.cls._arraymethods, awkward.VirtualArray)
        else:
            VirtualArray = awkward.VirtualArray

        chunks = []
        counts = []
        for pathi, path in enumerate(paths):
            chunks.append(VirtualArray(lazyfiles, (pathi, branch.name), cache=cache, type=awkward.type.ArrayType(path2count[path], interpretation.type), persistvirtual=persistvirtual))
            counts.append(path2count[path])
        name = branch.name.decode("ascii") if namedecode is None else branch.name.decode(namedecode)
        out[name] = awkward.ChunkedArray(chunks, counts)

    if profile is not None:
        out = uproot_methods.profiles.transformer(profile)(out)
    return out

def daskarray(path, treepath, branchname, interpretation=None, namedecode="utf-8", entrysteps=float("inf"), flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, **options):
    out = lazyarray(path, treepath, branchname, interpretation=interpretation, namedecode=namedecode, entrysteps=entrysteps, flatten=flatten, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, persistvirtual=False, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, **options)
    import dask.array
    if len(out.shape) == 1:
        return dask.array.from_array(out, out.shape, fancy=True)
    else:
        raise NotImplementedError("TODO: len(shape) > 1")

def daskframe(path, treepath, branches=None, namedecode="utf-8", entrysteps=float("inf"), flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, **options):
    import dask.array
    import dask.dataframe
    out = lazyarrays(path, treepath, branches=branches, namedecode=namedecode, entrysteps=entrysteps, flatten=flatten, profile=None, awkwardlib=awkwardlib, cache=cache, basketcache=basketcache, keycache=keycache, executor=executor, persistvirtual=False, localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, **options)
    series = []
    for n in out.columns:
        x = out[n]
        if len(x.shape) == 1:
            array = dask.array.from_array(x, x.shape, fancy=True)
            series.append(dask.dataframe.from_dask_array(array, columns=n))
        else:
            raise NotImplementedError("TODO: len(shape) > 1")
    return dask.dataframe.concat(series, axis=1)

################################################################ for quickly getting numentries

def numentries(path, treepath, total=True, localsource=MemmapSource.defaults, xrootdsource=XRootDSource.defaults, httpsource=HTTPSource.defaults, executor=None, blocking=True, **options):
    if isinstance(path, string_types):
        paths = _filename_explode(path)
    else:
        paths = [y for x in path for y in _filename_explode(x)]
    return _numentries(paths, treepath, total, localsource, xrootdsource, httpsource, executor, blocking, [None] * len(paths), options)

def _numentries(paths, treepath, total, localsource, xrootdsource, httpsource, executor, blocking, uuids, options):
    class _TTreeForNumEntries(uproot.rootio.ROOTStreamedObject):
        @classmethod
        def _readinto(cls, self, source, cursor, context, parent):
            start, cnt, classversion = uproot.rootio._startcheck(source, cursor)
            tnamed = uproot.rootio.Undefined.read(source, cursor, context, parent)
            tattline = uproot.rootio.Undefined.read(source, cursor, context, parent)
            tattfill = uproot.rootio.Undefined.read(source, cursor, context, parent)
            tattmarker = uproot.rootio.Undefined.read(source, cursor, context, parent)
            self._fEntries, = cursor.fields(source, _TTreeForNumEntries._format1)
            return self
        _format1 = struct.Struct('>q')

    out = [None] * len(paths)

    def fill(i):
        try:
            file = uproot.rootio.open(paths[i], localsource=localsource, xrootdsource=xrootdsource, httpsource=httpsource, read_streamers=False, **options)
        except:
            return sys.exc_info()
        else:
            try:
                source = file._context.source
                file._context.classes["TTree"] = _TTreeForNumEntries
                try:
                    out[i] = file[treepath]._fEntries
                except KeyError:
                    out[i] = 0
                uuids[i] = file._context.uuid
            except:
                return sys.exc_info()
            else:
                return None
            finally:
                source.close()

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
            return OrderedDict(zip(paths, out))

    if blocking:
        return wait()
    else:
        return wait
