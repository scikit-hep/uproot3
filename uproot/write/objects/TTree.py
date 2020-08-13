#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import struct
from copy import copy
import sys
import math

import numpy
import awkward

import uproot
import uproot.const
from uproot.rootio import _bytesid
from uproot.rootio import nofilter
from uproot.rootio import _memsize
from uproot._util import _tobytes
import uproot.write.compress
import uproot.write.sink.cursor
from uproot.write.TKey import BasketKey
from uproot.write.objects.util import Util

class newbranch(object):

    def __init__(self, type, title="", shape=(1,), size=None, **options):
        self.name = ""
        self.type = type
        self.title = title
        self.shape = shape
        self.counter = size
        self._iscounter = False
        if "compression" in options:
            self.compression = options["compression"]
            del options["compression"]
        if len(options) > 0:
            raise TypeError("{0} not supported".format(options))

class newtree(object):

    def __init__(self, branches={}, title="", **options):
        self.branches = branches
        self.title = title
        if "compression" in options:
            self.compression = options["compression"]
            del options["compression"]
        if len(options) > 0:
            raise TypeError("{0} not supported".format(options))

class TTree(object):

    def __init__(self, name, newtree, file):
        self._tree = TTreeImpl(name, newtree, file)
        self._file = file

        self._branches = {}
        checker = []
        for name, branch in newtree.branches.items():
            if isinstance(branch, newbranch) == False:
                branch = newbranch(branch)
            if branch.counter is not None:
                if isinstance(newtree.branches[name].type, str):
                    # FIXME: int8 and boolean cannot be read properly by ROOT yet
                    if newtree.branches[name].type == "int8" or newtree.branches[name].type == numpy.dtype("int8"):
                        raise NotImplementedError("int8 cannot be read properly by ROOT yet")
                    elif "?" in newtree.branches[name].type or newtree.branches[name].type == numpy.dtype(">?") or newtree.branches[name].type == numpy.dtype("<?"):
                        raise NotImplementedError("Booleans cannot be read properly by ROOT yet")
                else:
                    # FIXME: int8 and boolean cannot be read properly by ROOT yet
                    if newtree.branches[name].type.str == "int8" or newtree.branches[name].type.str == numpy.dtype("int8"):
                        raise NotImplementedError("int8 cannot be read properly by ROOT yet")
                    elif "?" in newtree.branches[name].type.str or newtree.branches[name].type.str == numpy.dtype(">?") or newtree.branches[name].type.str == numpy.dtype("<?"):
                        raise NotImplementedError("Booleans cannot be read properly by ROOT yet")
                if branch.counter not in checker:
                    checker += [branch.counter]
                    if branch.counter not in newtree.branches.keys():
                        dummybranch = newbranch(">i4")
                        dummybranch._iscounter = True
                        compression = getattr(dummybranch, "compression", getattr(newtree, "compression", file.compression))
                        self._branches[branch.counter] = TBranch(branch.counter, dummybranch, compression, self, file)
                        self._tree.fields["_fLeaves"].append(self._branches[branch.counter]._branch.fields["_fLeaves"])
                        self._tree.fields["_fBranches"].append(self._branches[branch.counter]._branch)
                    else:
                        raise Exception(branch.counter, " will be created automatically. Do not create it manually.")
            compression = getattr(branch, "compression", getattr(newtree, "compression", file.compression))
            self._branches[name] = TBranch(name, branch, compression, self, file)
            self._tree.fields["_fLeaves"].append(self._branches[name]._branch.fields["_fLeaves"])
            self._tree.fields["_fBranches"].append(self._branches[name]._branch)
            if branch.counter is not None:
                self._branches[name]._branch._awkwardbranch = self._branches[branch.counter]._branch.fields["_fLeaves"]

    def __getitem__(self, name):
        return self._branches[name]

    @property
    def _fClassName(self):
        return self._tree.fClassName

    @property
    def _fTitle(self):
        return self._tree.fTitle

    def _write(self, context, cursor, name, compression, key, keycursor, util):
        self._tree.write(context, cursor, name, key, copy(keycursor), util)

    def extend(self, branchdict):
        #Baskets need to be added to all the branches
        if len(branchdict) != len(self._branches):
            raise Exception("Basket data should be added to all branches")

        # Check for equal number of values in baskets
        values = iter(branchdict.values())
        first = next(values)
        if all(len(first) == len(value) for value in values) == False:
            raise Exception("Baskets of all branches should have the same length")

        #Check if length of jaggedarrays depending on the same lengths branch is the same
        tempdict = {}
        for key, value in branchdict.items():
            if self._branches[key]._branch.counter is not None:
                if self._branches[key]._branch.counter in tempdict.keys():
                    if not ((tempdict[self._branches[key]._branch.counter].counts == value.counts).all()):
                        raise Exception("Lengths of jagged arrays depending on the same lengths branch should be the same")
                else:
                    tempdict[self._branches[key]._branch.counter] = value

        #Convert to numpy arrays of required dtype
        for key, value in branchdict.items():
            if not isinstance(value, awkward.array.jagged.JaggedArray):
                branchdict[key] = numpy.array(value, dtype=self._branches[key]._branch.type, copy=False)

        for key, value in branchdict.items():
            if isinstance(value, awkward.array.jagged.JaggedArray):
                self._branches[key].newbasket(value)
            elif value.ndim == 1:
                self._branches[key].newbasket(value)
            else:
                for i in range(0, value.shape[0]):
                    self._branches[key].newbasket(value[i], i + 1)

    @property
    def name(self):
        return self._tree.fName

    @property
    def title(self):
        return self._tree.fTitle

    @property
    def numentries(self):
        t = uproot.open(self._file._path)[self.name]
        return t.numentries

    @property
    def numbranches(self):
        return len(self._branches)

    def iterkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        t = uproot.open(self._file._path)[self.name]
        return t.iterkeys(recursive, filtername, filtertitle, aliases)

    def itervalues(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        t = uproot.open(self._file._path)[self.name]
        return t.itervalues(recursive, filtername, filtertitle)

    def iteritems(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        t = uproot.open(self._file._path)[self.name]
        return t.iteritems(recursive, filtername, filtertitle, aliases)

    def keys(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        t = uproot.open(self._file._path)[self.name]
        return t.keys(recursive, filtername, filtertitle, aliases)

    def values(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        t = uproot.open(self._file._path)[self.name]
        return t.values(recursive, filtername, filtertitle)

    def items(self, recursive=False, filtername=nofilter, filtertitle=nofilter, aliases=True):
        t = uproot.open(self._file._path)[self.name]
        return t.items(recursive, filtername, filtertitle, aliases)

    def allkeys(self, filtername=nofilter, filtertitle=nofilter, aliases=True):
        t = uproot.open(self._file._path)[self.name]
        return t.allkeys(filtername, filtertitle, aliases)

    def allvalues(self, filtername=nofilter, filtertitle=nofilter):
        t = uproot.open(self._file._path)[self.name]
        return t.allvalues(filtername, filtertitle)

    def allitems(self, filtername=nofilter, filtertitle=nofilter, aliases=True):
        t = uproot.open(self._file._path)[self.name]
        return t.allitems(filtername, filtertitle, aliases)

    def get(self, name, recursive=True, filtername=nofilter, filtertitle=nofilter, aliases=True):
        t = uproot.open(self._file._path)[self.name]
        return t.get(name, recursive, filtername, filtertitle, aliases)

    def __contains__(self, name):
        t = uproot.open(self._file._path)[self.name]
        return t.__contains__(name)

    def mempartitions(self, numbytes, branches=None, entrystart=None, entrystop=None, keycache=None, linear=True):
        t = uproot.open(self._file._path)[self.name]
        return t.mempartitions(numbytes, branches, entrystart, entrystop, keycache, linear)

    def clusters(self, branches=None, entrystart=None, entrystop=None, strict=False):
        t = uproot.open(self._file._path)[self.name]
        return t.clusters(branches, entrystart, entrystop, strict)

    def array(self, branch, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        t = uproot.open(self._file._path)[self.name]
        return t.array(branch, interpretation, entrystart, entrystop, flatten, awkwardlib, cache, basketcache, keycache, executor, blocking)

    def arrays(self, branches=None, outputtype=dict, namedecode=None, entrystart=None, entrystop=None, flatten=False, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        t = uproot.open(self._file._path)[self.name]
        return t.arrays(branches, outputtype, namedecode, entrystart, entrystop, flatten, flatname, awkwardlib, cache, basketcache, keycache, executor, blocking)

    def lazyarray(self, branch, interpretation=None, entrysteps=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, persistvirtual=False):
        t = uproot.open(self._file._path)[self.name]
        return t.lazyarray(branch, interpretation, entrysteps, entrystart, entrystop, flatten, awkwardlib, cache, basketcache, keycache, executor, persistvirtual)

    def lazyarrays(self, branches=None, namedecode="utf-8", entrysteps=None, entrystart=None, entrystop=None, flatten=False, profile=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, persistvirtual=False):
        t = uproot.open(self._file._path)[self.name]
        return t.lazyarrays(branches, namedecode, entrysteps, entrystart, entrystop, flatten, profile, awkwardlib, cache, basketcache, keycache, executor, persistvirtual)

    def iterate(self, branches=None, entrysteps=None, outputtype=dict, namedecode=None, reportentries=False, entrystart=None, entrystop=None, flatten=False, flatname=None, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        t = uproot.open(self._file._path)[self.name]
        return t.iterate(branches, entrysteps, outputtype, namedecode, reportentries, entrystart, entrystop, flatten, flatname, awkwardlib, cache, basketcache, keycache, executor, blocking)

    def show(self, foldnames=False, stream=sys.stdout):
        t = uproot.open(self._file._path)[self.name]
        return t.show(foldnames, stream)

    def matches(self, branches):
        t = uproot.open(self._file._path)[self.name]
        return t.matches(branches)

    def __len__(self):
        return self.numentries

    def __iter__(self):
        # prevent Python's attempt to interpret __len__ and __getitem__ as iteration
        raise TypeError("'TTree' object is not iterable")

    @property
    def pandas(self):
        t = uproot.open(self._file._path)[self.name]
        return t.pandas

class TBranch(object):

    def __init__(self, name, branchobj, compression, treelvl1, file):
        self._branch = TBranchImpl(name, branchobj, compression, file)
        self._treelvl1 = treelvl1

    @staticmethod
    def revertstring(string):
        if isinstance(string, bytes):
            return string.decode()
        else:
            return string

    _tree_size = struct.Struct(">qqq")
    def newbasket(self, items, multidim=None):
        if len(items) == 0:
            return

        self._branch.fields["_fWriteBasket"] += 1

        if self._branch.fields["_fWriteBasket"] >= self._branch.fields["_fMaxBaskets"]:
            for branch in self._treelvl1._branches.values():
                branch._branch.fields["_fMaxBaskets"] = branch._branch.fields["_fMaxBaskets"] * 2
                temp_arr = numpy.array([0] * branch._branch.fields["_fMaxBaskets"], dtype=">i8")
                temp_arr[0:len(branch._branch.fields["_fBasketEntry"])] = branch._branch.fields["_fBasketEntry"]
                branch._branch.fields["_fBasketEntry"] = temp_arr
                temp_arr = numpy.array([0] * branch._branch.fields["_fMaxBaskets"], dtype=">i8")
                temp_arr[0:len(branch._branch.fields["_fBasketSeek"])] = branch._branch.fields["_fBasketSeek"]
                branch._branch.fields["_fBasketSeek"] = temp_arr
                temp_arr = numpy.array([0] * branch._branch.fields["_fMaxBaskets"], dtype=">i4")
                temp_arr[0:len(branch._branch.fields["_fBasketBytes"])] = branch._branch.fields["_fBasketBytes"]
                branch._branch.fields["_fBasketBytes"] = temp_arr

            tree = TTreeImpl(self._treelvl1._tree.name, newtree(), self._branch.file)
            tree.name = self._treelvl1._tree.name
            tree.fName = self._treelvl1._tree.fName
            tree.fTitle = self._treelvl1._tree.fTitle

            tree.fields["_fEntries"] = self._treelvl1._tree.fields["_fEntries"]
            tree.fields["_fTotBytes"] = self._treelvl1._tree.fields["_fTotBytes"]
            tree.fields["_fZipBytes"] = self._treelvl1._tree.fields["_fZipBytes"]

            temp_branches = {}
            for name, branch in self._treelvl1._branches.items():
                compression = getattr(branch._branch, "compression", branch._branch.file.compression)
                temp_branches[name] = TBranch(name, newbranch(branch._branch.type, ""), compression, self._treelvl1, branch._branch.file)
                temp_branches[name]._branch.fields["_fWriteBasket"] = branch._branch.fields["_fWriteBasket"]
                temp_branches[name]._branch.fields["_fEntries"] = branch._branch.fields["_fEntries"]
                temp_branches[name]._branch.fields["_fBasketEntry"] = branch._branch.fields["_fBasketEntry"]
                temp_branches[name]._branch.fields["_fEntryNumber"] = branch._branch.fields["_fEntryNumber"]
                temp_branches[name]._branch.fields["_fMaxBaskets"] = branch._branch.fields["_fMaxBaskets"]
                temp_branches[name]._branch.fields["_fBasketSeek"] = branch._branch.fields["_fBasketSeek"]
                temp_branches[name]._branch.fields["_fBasketBytes"] = branch._branch.fields["_fBasketBytes"]
                temp_branches[name]._branch.fields["_fTotBytes"] = branch._branch.fields["_fTotBytes"]
                temp_branches[name]._branch.fields["_fZipBytes"] = branch._branch.fields["_fZipBytes"]
                tree.fields["_fLeaves"].append(temp_branches[name]._branch.fields["_fLeaves"])
                tree.fields["_fBranches"].append(temp_branches[name]._branch)

            tree.branches = copy(temp_branches)

            cursor = uproot.write.sink.cursor.Cursor(self._branch.file._fSeekFree)
            tree.write_key = uproot.write.TKey.TKey(fClassName=self._treelvl1._tree.write_key.fClassName,
                                                    fName=self._treelvl1._tree.write_key.fName,
                                                    fTitle=self._treelvl1._tree.write_key.fTitle,
                                                    fObjlen=0,
                                                    fSeekKey=copy(self._branch.file._fSeekFree),
                                                    fSeekPdir=self._treelvl1._tree.write_key.fSeekPdir,
                                                    fCycle=self._treelvl1._tree.write_key.fCycle)
            tree.keycursor = uproot.write.sink.cursor.Cursor(tree.write_key.fSeekKey)
            tree.write_key.write(cursor, self._branch.file._sink)
            tree.write(tree.file, cursor, self._treelvl1._tree.write_name, tree.write_key, copy(tree.keycursor), Util())
            tree.file._expandfile(cursor)
            tree.file._rootdir.setkey(tree.write_key)

            self = tree.branches[self.revertstring(self._branch.name)]
            self._treelvl1._tree = tree
            self._treelvl1._branches = temp_branches

        if multidim is None:
            self._branch.fields["_fEntries"] += len(items)
            self._branch.fields["_fEntryNumber"] += len(items)
        else:
            self._branch.fields["_fEntries"] = multidim
            self._branch.fields["_fEntryNumber"] = multidim
        self._branch.fields["_fBasketEntry"][self._branch.fields["_fWriteBasket"]] = self._branch.fields["_fEntries"]
        if isinstance(items, awkward.array.jagged.JaggedArray):
            givenbytes = b""
            for i in range(items.shape[0]):
                givenbytes += _tobytes(numpy.array(items[i], dtype=self._branch.type))
        else:
            givenbytes = _tobytes(numpy.array(items, dtype=self._branch.type, copy=False))

        cursor = uproot.write.sink.cursor.Cursor(self._branch.file._fSeekFree)
        self._branch.fields["_fBasketSeek"][self._branch.fields["_fWriteBasket"] - 1] = cursor.index
        if isinstance(items, awkward.array.jagged.JaggedArray):
            key = BasketKey(fName=self._branch.name,
                            fTitle=self._treelvl1._tree.write_key.fName,
                            fNevBuf=items.shape[0],
                            fNevBufSize=1000, # FIXME: What does this mean?
                            fSeekKey=copy(self._branch.file._fSeekFree),
                            fSeekPdir=copy(self._branch.file._fBEGIN),
                            fBufferSize=32000)
        else:
            key = BasketKey(fName=self._branch.name,
                            fTitle=self._treelvl1._tree.write_key.fName,
                            fNevBuf=1 if multidim else len(items),
                            fNevBufSize=numpy.dtype(self._branch.type).itemsize*len(items) if multidim else numpy.dtype(self._branch.type).itemsize,
                            fSeekKey=copy(self._branch.file._fSeekFree),
                            fSeekPdir=copy(self._branch.file._fBEGIN),
                            fBufferSize=32000)
        keycursor = uproot.write.sink.cursor.Cursor(key.fSeekKey)
        key.write(cursor, self._branch.file._sink)
        uproot.write.compress.write(self._branch.file, cursor, givenbytes, self._branch.compression, key, copy(keycursor))
        if isinstance(items, awkward.array.jagged.JaggedArray):
            # 3 looks like a harmless value for the first entry of offsetbytes
            # Relevant code - https://github.com/root-project/root/blob/master/tree/tree/src/TBasket.cxx#L921-L954
            offsetbytes = [3, key.fKeylen]
            for i in range(items.shape[0] - 1):
                offsetbytes += [(len(items[i]) * numpy.dtype(self._branch.type).itemsize) + offsetbytes[-1]]
            offsetbytes += [0]
            offsetbytes = _tobytes(numpy.array(offsetbytes, dtype=">i4"))
            uproot.write.compress.write(self._branch.file, cursor, offsetbytes, self._branch.compression, key,
                                        copy(keycursor), isjagged=True)

        self._branch.file._expandfile(cursor)

        self._treelvl1._tree.fields["_fEntries"] = self._branch.fields["_fEntries"]
        self._branch.fields["_fTotBytes"] += key.fObjlen + key.fKeylen
        self._branch.fields["_fZipBytes"] += key.fNbytes
        self._treelvl1._tree.fields["_fTotBytes"] += self._branch.fields["_fTotBytes"]
        self._treelvl1._tree.fields["_fZipBytes"] += self._branch.fields["_fZipBytes"]
        self._branch.fields["_fBasketBytes"][self._branch.fields["_fWriteBasket"] - 1] = key.fNbytes
        if self._branch.counter and ((len(items[-1])*4) > 10):
            self._branch.fields["_fEntryOffsetLen"] = len(items[-1])*4
            self._branch._fentryoffsetlencursor.update_fields(self._branch.file._sink, self._branch._format_tbranch112, self._branch.fields["_fEntryOffsetLen"])
        self._treelvl1._tree.size_cursor.update_fields(self._branch.file._sink, self._tree_size, self._treelvl1._tree.fields["_fEntries"],
                                                       self._treelvl1._tree.fields["_fTotBytes"],
                                                       self._treelvl1._tree.fields["_fZipBytes"])
        self._branch._writebasket_cursor.update_fields(self._branch.file._sink, self._branch._format_tbranch12,
                                                       self._branch.fields["_fWriteBasket"], self._branch.fields["_fEntryNumber"])
        self._branch._fentries_cursor.update_fields(self._branch.file._sink, self._branch._format_fentries, self._branch.fields["_fEntries"])
        self._branch._fbasketentry_cursor.update_array(self._branch.file._sink, self._branch.fields["_fBasketEntry"])
        self._branch._fbasketseek_cursor.update_array(self._branch.file._sink, self._branch.fields["_fBasketSeek"])
        self._branch._tbranch_size_cursor.update_fields(self._branch.file._sink, self._branch._format_branch_size,
                                                        self._branch.fields["_fTotBytes"], self._branch.fields["_fZipBytes"])
        self._branch._fbasketbytes_cursor.update_array(self._branch.file._sink, self._branch.fields["_fBasketBytes"])

    @property
    def name(self):
        return self._branch.name

    @property
    def title(self):
        return self._branch.title

    @property
    def interpretation(self):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.interpretation

    @property
    def countbranch(self):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.countbranch

    @property
    def countleaf(self):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.countleaf

    @property
    def numentries(self):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.numentries

    @property
    def numbranches(self):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.numbranches

    def iterkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.iterkeys(recursive, filtername, filtertitle)

    def itervalues(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.itervalues(recursive, filtername, filtertitle)

    def iteritems(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.iteritems(recursive, filtername, filtertitle)

    def keys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.keys(recursive, filtername, filtertitle)

    def values(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.keys(recursive, filtername, filtertitle)

    def items(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.items(recursive, filtername, filtertitle)

    def allkeys(self, recursive=False, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.allkeys(recursive, filtername, filtertitle)

    def allvalues(self, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.keys(filtername, filtertitle)

    def allitems(self, filtername=nofilter, filtertitle=nofilter):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.allitems(filtername, filtertitle)

    def get(self, name, recursive=True, filtername=nofilter, filtertitle=nofilter, aliases=True):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.get(name, recursive, filtername, filtertitle, aliases)

    @property
    def numbaskets(self):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.numbaskets

    def uncompressedbytes(self, keycache=None):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.uncompressedbhytes(keycache)

    def compressedbytes(self, keycache=None):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.compressedbhytes(keycache)

    def compressionratio(self, keycache=None):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.compressionratio(keycache)

    def numitems(self, interpretation=None, keycache=None):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.numitems(interpretation, keycache)

    def basket_entrystart(self, i):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.basket_entrystart(i)

    def basket_entrystop(self, i):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.basket_entrystop(i)

    def basket_numentries(self, i):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.basket_numentries(i)

    def basket_uncompressedbytes(self, i, keycache=None):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.basket_uncompressedbytes(i, keycache)

    def basket_compressedbytes(self, i):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.basked_compressedbytes(i)

    def basket_numitems(self, i, interpretation=None, keycache=None):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.basket_numitems(i, interpretation, keycache)

    def basket(self, i, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.basket(i, interpretation, entrystart, entrystop, flatten, awkwardlib, cache, basketcache, keycache)

    def baskets(self, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, reportentries=False, executor=None, blocking=True):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.baskets(interpretation, entrystart, entrystop, flatten, awkwardlib, cache, basketcache, keycache, reportentries, executor, blocking)

    def iterate_baskets(self, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, reportentries=False):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.baskets(interpretation, entrystart, entrystop, flatten, awkwardlib, cache, basketcache, keycache, reportentries)

    def array(self, interpretation=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, blocking=True):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.array(interpretation, entrystart, entrystop, flatten, awkwardlib, cache, basketcache, keycache, executor, blocking)

    def mempartitions(self, numbytes, entrystart=None, entrystop=None, keycache=None, linear=True):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.mempartitions(numbytes, entrystart, entrystop, keycache, linear)

    def lazyarray(self, interpretation=None, entrysteps=None, entrystart=None, entrystop=None, flatten=False, awkwardlib=None, cache=None, basketcache=None, keycache=None, executor=None, persistvirtual=False):
        b = uproot.open(self._treelvl1._file._path)[self._treelvl1.name][self.name]
        return b.lazyarray(interpretation, entrysteps, entrystart, entrystop, flatten, awkwardlib, cache, basketcache, keycache, executor, persistvirtual)

class TTreeImpl(object):

    def __init__(self, name, newtree, file):
        self.name = name
        self.fClassName = b"TTree"
        self.fName = _bytesid(self.name)
        self.fTitle = _bytesid(newtree.title)
        self.file = file

        self.fields = {"_fLineColor": 602,
                       "_fLineStyle": 1,
                       "_fLineWidth": 1,
                       "_fFillColor": 0,
                       "_fFillStyle": 1001,
                       "_fMarkerColor": 1,
                       "_fMarkerStyle": 1,
                       "_fMarkerSize": 1.0,
                       "_fEntries": 0,
                       "_fTotBytes": 0,
                       "_fZipBytes": 0,
                       "_fSavedBytes": 0,
                       "_fFlushedBytes": 0,
                       "_fWeight": 1.0,
                       "_fTimerInterval": 0,
                       "_fScanField": 25,
                       "_fUpdate": 0,
                       "_fDefaultEntryOffsetLen": 1000,  # TODO: WHAT IS THIS?
                       "_fNClusterRange": 0,
                       "_fMaxEntries": 1000000000000,  # TODO: HOW DOES THIS WORK?
                       "_fMaxEntryLoop": 1000000000000,  # Same as fMaxEntries?
                       "_fMaxVirtualSize": 0,
                       "_fAutoSave": -300000000,
                       "_fAutoFlush": -30000000,
                       "_fEstimate": 1000000,
                       "_fClusterRangeEnd": [],
                       "_fClusterSize": [],
                       "_fBranches": [],
                       "_fFriends": None,
                       "_fTreeIndex": None,
                       "_fIndex": [],
                       "_fIndexValues": [],
                       "_fAliases": None,
                       "_fLeaves": [],
                       "_fUserInfo": None,
                       "_fBranchRef": None}

    _format_tobject1 = struct.Struct(">HII")
    def put_tobject(self, cursor, hexbytes):
        return cursor.put_fields(self._format_tobject1, 1, 0, hexbytes)

    def put_tnamed(self, cursor, name, title, hexbytes=numpy.uint32(0x03000000)):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        buff = (self.put_tobject(cursor, hexbytes) +
                cursor.put_string(name) + cursor.put_string(title))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattline = struct.Struct(">hhh")
    def put_tattline(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattline,
                                  self.fields["_fLineColor"],
                                  self.fields["_fLineStyle"],
                                  self.fields["_fLineWidth"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattfill = struct.Struct(">hh")
    def put_tattfill(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattfill,
                                  self.fields["_fFillColor"],
                                  self.fields["_fFillStyle"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattmarker = struct.Struct(">hhf")
    def put_tattmarker(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattmarker,
                                  self.fields["_fMarkerColor"],
                                  self.fields["_fMarkerStyle"],
                                  self.fields["_fMarkerSize"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_rootiofeatures = struct.Struct(">B")
    def put_rootiofeatures(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 0
        fIOBits = 0
        cursor.skip(4)
        buff = b"\x1a\xa1/\x10" + cursor.put_fields(self._format_rootiofeatures, fIOBits)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tobjarray1 = struct.Struct(">ii")
    def put_tobjarray(self, cursor, values, classname, fBits=50331648):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        buff = self._skiptobj(cursor, fBits)
        vers = 3
        try:
            size = len(values)
        except TypeError:
            size = 1
            values = [values]
        low = 0
        buff += cursor.put_string(b"") + cursor.put_fields(self._format_tobjarray1, size, low)
        for i in range(len(self.fields["_fLeaves"])):
            buff += self.util.put_objany(cursor, (values[i], classname[i] if type(classname)==list else classname), self.write_keycursor)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_skiptobj1 = struct.Struct(">h")
    _format_skiptobj2 = struct.Struct(">II")
    def _skiptobj(self, cursor, fBits):
        version = 1
        buff = cursor.put_fields(self._format_skiptobj1, version)
        fUniqueID = 0
        buff += cursor.put_fields(self._format_skiptobj2, fUniqueID, fBits)
        return buff

    _format_tarray = struct.Struct(">i")
    def put_tarray(self, cursor, values):
        return cursor.put_fields(self._format_tarray, values.size) + cursor.put_array(values)

    _format_cntvers = struct.Struct(">IH")

    _format_ttree = struct.Struct(">qqqqqdiiiiIqqqqqq")
    def write(self, context, cursor, name, key, keycursor, util):
        copy_cursor = copy(cursor)
        self.tree_write_cursor = copy(cursor)
        self.write_name = name
        self.write_key = key
        self.write_keycursor = keycursor
        self.util = util
        self.util.set_obj(self)

        cursor.skip(self._format_cntvers.size)
        vers = 20

        for branch in self.fields["_fBranches"]:
            branch.util = self.util
            branch.keycursor = self.write_keycursor

        self.fields["_fClusterRangeEnd"] = numpy.array(self.fields["_fClusterRangeEnd"], dtype="int64", copy=False)
        self.fields["_fClusterSize"] = numpy.array(self.fields["_fClusterSize"], dtype="int64", copy=False)
        self.fields["_fIndexValues"] = numpy.array(self.fields["_fIndexValues"], dtype=">f8", copy=False)
        self.fields["_fIndex"] = numpy.array(self.fields["_fIndex"], dtype=">i8", copy=False)

        buff = (self.put_tnamed(cursor, name, self.fTitle, hexbytes=numpy.uint32(0x03000008)) +
                self.put_tattline(cursor) +
                self.put_tattfill(cursor) +
                self.put_tattmarker(cursor))
        self.size_cursor = copy(cursor)
        buff += (cursor.put_fields(self._format_ttree, self.fields["_fEntries"],
                                   self.fields["_fTotBytes"],
                                   self.fields["_fZipBytes"],
                                   self.fields["_fSavedBytes"],
                                   self.fields["_fFlushedBytes"],
                                   self.fields["_fWeight"],
                                   self.fields["_fTimerInterval"],
                                   self.fields["_fScanField"],
                                   self.fields["_fUpdate"],
                                   self.fields["_fDefaultEntryOffsetLen"],
                                   self.fields["_fNClusterRange"],
                                   self.fields["_fMaxEntries"],
                                   self.fields["_fMaxEntryLoop"],
                                   self.fields["_fMaxVirtualSize"],
                                   self.fields["_fAutoSave"],
                                   self.fields["_fAutoFlush"],
                                   self.fields["_fEstimate"]))
        buff += b"\x00"
        cursor.skip(len(b"\x00"))
        buff += cursor.put_array(self.fields["_fClusterRangeEnd"])
        buff += b"\x00"
        cursor.skip(len(b"\x00"))
        buff += (cursor.put_array(self.fields["_fClusterSize"]))
        buff += (self.put_rootiofeatures(cursor) +
                 self.put_tobjarray(cursor, self.fields["_fBranches"], "TBranch", fBits=50348032))
        if self.fields["_fBranches"] == []:
            buff += self.put_tobjarray(cursor, self.fields["_fLeaves"], "TLeaf")
        else:
            buff += self.put_tobjarray(cursor, [self.fields["_fLeaves"][i][0] for i in range(len(self.fields["_fLeaves"]))],
                                       classname=[self.fields["_fLeaves"][i][1] for i in range(len(self.fields["_fLeaves"]))])
        buff += (self.util.put_objany(cursor, (self.fields["_fAliases"], "TList"), self.write_keycursor) +
                 self.put_tarray(cursor, self.fields["_fIndexValues"]) +
                 self.put_tarray(cursor, self.fields["_fIndex"]) +
                 self.util.put_objany(cursor, (self.fields["_fTreeIndex"], "TVirtualIndex"), self.write_keycursor) +
                 self.util.put_objany(cursor, (self.fields["_fFriends"], "TList"), self.write_keycursor) +
                 self.util.put_objany(cursor, (self.fields["_fUserInfo"], "TList"), self.write_keycursor) +
                 self.util.put_objany(cursor, (self.fields["_fBranchRef"], "TBranchRef"), self.write_keycursor))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        givenbytes = copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff
        uproot.write.compress.write(context, copy(self.tree_write_cursor), givenbytes, None, key, copy(self.write_keycursor))

class TBranchImpl(object):

    def __init__(self, name, branchobj, compression, file):
        self.name = _bytesid(name)
        self.type = numpy.dtype(branchobj.type).newbyteorder(">")
        self.shape = branchobj.shape
        self.compression = compression
        self.counter = branchobj.counter
        if self.counter:
            self.awkwardpadder = b"[" + self.counter.encode("utf-8") + b"]"
        else:
            self.awkwardpadder = b""
        self._awkwardbranch = None
        self._iscounter = branchobj._iscounter
        self.util = None
        self.keycursor = None
        self.file = file

        self.fields = {"_fCompress": 100,
                       "_fBasketSize": 32000,
                       "_fEntryOffsetLen": 10 if self.counter else 0,
                       "_fWriteBasket": 0,  # Number of baskets
                       "_fOffset": 0,
                       "_fMaxBaskets": 50,
                       "_fSplitLevel": 0,
                       "_fEntries": 0,
                       "_fFirstEntry": 0,
                       "_fTotBytes": 0,
                       "_fZipBytes": 0,
                       "_fBasketBytes": [0]*50,
                       "_fBasketEntry": [0]*50,
                       "_fBasketSeek": [0]*50,
                       "_fFileName": b"",
                       "_fBranches": [],
                       "_fLeaves": [],
                       "_fFillColor": 0,
                       "_fFillStyle": 1001,
                       "_fEntryNumber": 0,
                       "_fBaskets": b'@\x00\x00\x1d\x00\x03\x00\x01\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'}

        # For multidimensional arrays
        if len(self.shape) > 1:
            array_pad = b""
            for i in range(1, len(self.shape)):
                array_pad += b"[" + str(self.shape[i]).encode("utf-8") + b"]"

        # TODO: Fix else condition to not always return NotImplementedError
        if self.type == "int8":
            title_pad = b"/B"
            self.fields["_fLeaves"] = [self, "TLeafB"]
        elif self.type == ">f8":
            title_pad = b"/D"
            self.fields["_fLeaves"] = [self, "TLeafD"]
        elif self.type == ">f4":
            title_pad = b"/F"
            self.fields["_fLeaves"] = [self, "TLeafF"]
        elif self.type == ">i4":
            title_pad = b"/I"
            self.fields["_fLeaves"] = [self, "TLeafI"]
        elif self.type == ">i8":
            title_pad = b"/L"
            self.fields["_fLeaves"] = [self, "TLeafL"]
        elif self.type == ">?":
            title_pad = b"/O"
            self.fields["_fLeaves"] = [self, "TLeafO"]
        elif self.type == ">i2":
            title_pad = b"/S"
            self.fields["_fLeaves"] = [self, "TLeafS"]
        else:
            raise NotImplementedError

        if branchobj.title == "":
            self.title = _bytesid(name)
            if len(self.shape) > 1:
                self.nametitle = self.title + array_pad + title_pad
                self.arraytitle = self.title + array_pad

            else:
                self.nametitle = self.title + title_pad
        else:
            self.title = _bytesid(branchobj.title)
            if len(self.shape) > 1:
                self.nametitle = self.title + array_pad
                self.arraytitle = self.title + array_pad
            else:
                self.nametitle = self.title

        self.fields["_fBasketBytes"] = numpy.array(self.fields["_fBasketBytes"], dtype=">i4", copy=False)
        self.fields["_fBasketEntry"] = numpy.array(self.fields["_fBasketEntry"], dtype=">i8", copy=False)
        self.fields["_fBasketSeek"] = numpy.array(self.fields["_fBasketSeek"], dtype=">i8", copy=False)

    _format_cntvers = struct.Struct(">IH")

    _format_tobject1 = struct.Struct(">HII")
    def put_tobject(self, cursor, hexbytes):
        return cursor.put_fields(self._format_tobject1, 1, 0, hexbytes)

    def put_tnamed(self, cursor, name, title, hexbytes=numpy.uint32(0x03000000)):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        buff = (self.put_tobject(cursor, hexbytes) +
                cursor.put_string(name) + cursor.put_string(title))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tattfill = struct.Struct(">hh")
    def put_tattfill(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        buff = (cursor.put_fields(self._format_tattfill,
                                  self.fields["_fFillColor"],
                                  self.fields["_fFillStyle"]))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_rootiofeatures = struct.Struct(">B")
    def put_rootiofeatures(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 0
        fIOBits = 0
        cursor.skip(4)
        buff = b"\x1a\xa1/\x10"
        buff += cursor.put_fields(self._format_rootiofeatures, fIOBits)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleaf1 = struct.Struct(">iii??")
    def put_tleaf(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 2
        fLen = 1
        if len(self.shape) > 1:
            for i in range(1, len(self.shape)):
                fLen = fLen*self.shape[i]
        fLenType = numpy.dtype(self.type).itemsize
        fOffset = 0
        if self._iscounter:
            fIsRange = True
        else:
            fIsRange = False
        fIsUnsigned = False
        fLeafCount = None
        if self.counter:
            buff = (self.put_tnamed(cursor, self.name, self.title + self.awkwardpadder) +
                    cursor.put_fields(self._format_tleaf1, fLen, fLenType, fOffset, fIsRange, fIsUnsigned) +
                    self.util.put_objany(cursor, (self._awkwardbranch[0], self._awkwardbranch[1]), self.keycursor))
        else:
            buff = (self.put_tnamed(cursor, self.name, self.arraytitle if len(self.shape)>1 else self.title) +
                    cursor.put_fields(self._format_tleaf1, fLen, fLenType, fOffset, fIsRange, fIsUnsigned) +
                    self.util.put_objany(cursor, (fLeafCount, "TLeaf"), self.keycursor))
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafI1 = struct.Struct(">ii")
    def put_tleafI(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        if self._iscounter:
            fMaximum = min(numpy.iinfo(self.type).max, 1000) # FIXME: Make updateble
        else:
            fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafI1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafB1 = struct.Struct(">bb")
    def put_tleafB(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        if self._iscounter:
            fMaximum = min(numpy.iinfo(self.type).max, 1000) # FIXME: Make updateble
        else:
            fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafB1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafD1 = struct.Struct(">dd")
    def put_tleafD(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        if self._iscounter:
            fMaximum = 1000 # FIXME: Make updateble or set to maximum possible value
        else:
            fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafD1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafF1 = struct.Struct(">ff")
    def put_tleafF(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        if self._iscounter:
            fMaximum = 1000 # FIXME: Make updateble or set to maximum possible value
        else:
            fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafF1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafL1 = struct.Struct(">qq")
    def put_tleafL(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        if self._iscounter:
            fMaximum = min(numpy.iinfo(self.type).max, 1000) # FIXME: Make updateble
        else:
            fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafL1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafO1 = struct.Struct(">??")
    def put_tleafO(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        if self._iscounter:
            fMaximum = min(numpy.iinfo(self.type).max, 1000) # FIXME: Make updateble
        else:
            fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafO1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tleafS1 = struct.Struct(">hh")
    def put_tleafS(self, cursor):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 1
        fMinimum = 0
        if self._iscounter:
            fMaximum = min(numpy.iinfo(self.type).max, 1000) # FIXME: Make updateble
        else:
            fMaximum = 0
        buff = self.put_tleaf(cursor) + cursor.put_fields(self._format_tleafS1, fMinimum, fMaximum)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_tobjarray1 = struct.Struct(">ii")
    def put_tobjarray(self, cursor, values, classname, fBits=50331648):
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        buff = self._skiptobj(cursor, fBits)
        vers = 3
        try:
            size = len(values)
        except TypeError:
            size = 1
            values = [values]
        low = 0
        buff += cursor.put_string(b"") + cursor.put_fields(self._format_tobjarray1, size, low)
        for value in values:
            buff += self.util.put_objany(cursor, (value, classname), self.keycursor)
        length = len(buff) + self._format_cntvers.size
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff

    _format_skiptobj1 = struct.Struct(">h")
    _format_skiptobj2 = struct.Struct(">II")

    def _skiptobj(self, cursor, fBits):
        version = 1
        buff = cursor.put_fields(self._format_skiptobj1, version)
        fUniqueID = 0
        buff += cursor.put_fields(self._format_skiptobj2, fUniqueID, fBits)
        return buff

    _format_tbranch111 = struct.Struct(">ii")
    _format_tbranch112 = struct.Struct(">i")
    _format_tbranch12 = struct.Struct(">iq")
    _format_tbranch21 = struct.Struct(">iIi")
    _format_fentries = struct.Struct(">q")
    _format_tbranch22 = struct.Struct(">q")
    _format_branch_size = struct.Struct(">qq")
    def write(self, cursor):
        if self.compression != None:
            self.fields["_fCompress"] = self.compression.code
        copy_cursor = copy(cursor)
        cursor.skip(self._format_cntvers.size)
        vers = 13
        if self.counter:
            buff = (self.put_tnamed(cursor, self.name, self.nametitle[:-2] + self.awkwardpadder + self.nametitle[-2:], hexbytes=numpy.uint32(0x03400000)) +
                    self.put_tattfill(cursor))
        else:
            buff = (self.put_tnamed(cursor, self.name, self.nametitle, hexbytes=numpy.uint32(0x03400000)) +
                    self.put_tattfill(cursor))
        self.branch_compress_cursor = copy(cursor)
        buff += (cursor.put_fields(self._format_tbranch111,
                                  self.fields["_fCompress"],
                                  self.fields["_fBasketSize"]))
        self._fentryoffsetlencursor = copy(cursor)
        buff += (cursor.put_fields(self._format_tbranch112, self.fields["_fEntryOffsetLen"]))
        self._writebasket_cursor = copy(cursor)
        buff += (cursor.put_fields(self._format_tbranch12,
                                   self.fields["_fWriteBasket"],
                                   self.fields["_fEntryNumber"]) +
                self.put_rootiofeatures(cursor) +
                cursor.put_fields(self._format_tbranch21,
                                  self.fields["_fOffset"],
                                  self.fields["_fMaxBaskets"],
                                  self.fields["_fSplitLevel"]))
        self._fentries_cursor = copy(cursor)
        buff += (cursor.put_fields(self._format_fentries, self.fields["_fEntries"]))
        buff += cursor.put_fields(self._format_tbranch22, self.fields["_fFirstEntry"])
        self._tbranch_size_cursor = copy(cursor)
        buff += (cursor.put_fields(self._format_branch_size,
                                  self.fields["_fTotBytes"],
                                  self.fields["_fZipBytes"]) +
                self.put_tobjarray(cursor, self.fields["_fBranches"], classname="TBranch") +
                self.put_tobjarray(cursor, self.fields["_fLeaves"][0], classname=self.fields["_fLeaves"][1]) +
                cursor.put_data(self.fields["_fBaskets"]))
        buff += b"\x01"
        cursor.skip(len(b"\x01"))
        self._fbasketbytes_cursor = copy(cursor)
        buff += cursor.put_array(self.fields["_fBasketBytes"])
        buff += b"\x01"
        cursor.skip(len(b"\x01"))
        self._fbasketentry_cursor = copy(cursor)
        buff += (cursor.put_array(self.fields["_fBasketEntry"]) + b"\x01")
        cursor.skip(len(b"\x01"))
        self._fbasketseek_cursor = copy(cursor)
        buff += (cursor.put_array(self.fields["_fBasketSeek"]) + cursor.put_string(self.fields["_fFileName"]))
        length = (len(buff) + self._format_cntvers.size)
        cnt = numpy.int64(length - 4) | uproot.const.kByteCountMask
        return copy_cursor.put_fields(self._format_cntvers, cnt, vers) + buff
