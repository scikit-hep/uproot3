#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

"""Uproot -- ROOT I/O in pure Python and Numpy.

Basic cheat-sheet
-----------------

Open ROOT files with uproot3.open (for reading) or uproot3.create (for read-write).

    file = uproot3.open("/path/to/my/file.root")
    file = uproot3.open("root://path/to/my/file.root")
    file = uproot3.open("http://path/to/my/file.root")
    writeable = uproot3.create("/new/local/file.root")

These file objects act like dicts; get objects like TTrees from them with square
brackets.

    tree = file["path/to/events"]
    tree = file["path/to/events;2"]            # optional cycle number
    # write to files by assignment (histograms only)
    writeable["name"] = numpy.histogram(...)

TTree objects also act like dicts; get branches with square brackets or list them
with keys().

    tree.keys()
    tree.allkeys()    # recursive branches-of-branches
    tree.show()       # display view
    tree["mybranch"]  # searches recursively

Get data as arrays with an array(...) or arrays(...) call.

    tree["mybranch"].array()
    tree.array("mybranch")
    tree.arrays(["branch1", "branch2", "branch3"])
    tree.arrays(["Muon_*"])

Variable numbers of objects per entry (particles per event) are handled by
Awkward Array:

    https://github.com/scikit-hep/awkward-0.x

The arrays(...) call returns a dict from branch name (bytes) to data
(Numpy array) by default.
Change this by passing an outputtype class (e.g. dict, tuple, pandas.DataFrame).

    x, y, z = tree.arrays(["x", "y", "z"], outputtype=tuple)

For more idiomatic Pandas defaults, use tree.pandas.df().

    df = tree.pandas.df()

If the desired branches do not fit into memory, iterate over chunks of entries
with iterate(). The interface is the same as above: you get the same
dict/tuple/DataFrame with fewer entries.

    for x, y, z in tree.iterate(["x", "y", "z"], outputtype=tuple):
        do_something(x, y, z)

To iterate over many files (like TChain), do uproot3.iterate(...).

    for arrays in uproot3.iterate("files*.root", "path/to/events", ["Muon_*"]):
        do_something(arrays)

Intermediate cheat-sheet
------------------------

Each call to array/arrays/iterate reads the file again. For faster access after
the first time, pass a dict-like object to the cache parameter and Uproot will
try the cache first.

    cache = {}
    arrays = tree.arrays(["Muon_*"], cache=cache)    # slow
    arrays = tree.arrays(["Muon_*"], cache=cache)    # fast

You control the cache object. If you're running out of memory, remove it or
remove items from it. Or use one of the dict-like caches from cachetools (already
installed) or another library.

For parallel processing, pass a Python 3 executor.

    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(32)
    arrays = tree.arrays(["Muon_*"], executor=executor)

To get the number of entries per file in a a collection of files, use
uproot3.numentries().

    uproot3.numentries("tests/samples/sample*.root", "sample", total=False)

For arrays that read on demand, use uproot3.lazyarray and uproot3.lazyarrays.
For processing with Dask, use uproot3.daskarray, uproot3.daskarrays, or
uproot3.daskframe.

Advanced cheat-sheet
--------------------

The standard bytes-to-arrays decoding is attached to each branch as

    tree["mybranch"].interpretation

This can be overridden by passing a new interpretation to array/arrays/iterate.
Most reinterpretations will produce wrong values (it's a reinterpret_cast<...>).

Some, however, are useful:

    mybranch = tree["mybranch"]
    fill_me_instead = numpy.empty(big_enough)
    mybranch.array(mybranch.interpretation.toarray(fill_me_instead))
    fill_me_instead                   # filled in place

    mybranch.array(uproot3.asdebug)   # view raw bytes of each entry

By default, local files are read as memory-mapped arrays. Change this by setting

    from uproot3 import FileSource
    open("...", localsource=lambda path: FileSource(path, **FileSource.defaults))

The same procedure sets options for uproot3.XRootDSource and uproot3.HTTPSource.
"""

from __future__ import absolute_import

# high-level entry points
from uproot3.rootio import open, xrootd, http
from uproot3.tree import iterate, numentries, lazyarray, lazyarrays, daskarray, daskframe
from uproot3.write.TFile import TFileCreate as create
from uproot3.write.TFile import TFileRecreate as recreate
from uproot3.write.TFile import TFileUpdate as update
from uproot3.write.compress import ZLIB, LZMA, LZ4
from uproot3.write.objects.TTree import newtree, newbranch

from uproot3.source.memmap import MemmapSource
from uproot3.source.file import FileSource
from uproot3.source.xrootd import XRootDSource
from uproot3.source.http import HTTPSource

from uproot3.cache import ArrayCache, ThreadSafeArrayCache

from uproot3.interp.auto import interpret
from uproot3.interp.numerical import asdtype
from uproot3.interp.numerical import asarray
from uproot3.interp.numerical import asdouble32
from uproot3.interp.numerical import asstlbitset
from uproot3.interp.jagged import asjagged
from uproot3.interp.objects import astable
from uproot3.interp.objects import asobj
from uproot3.interp.objects import asgenobj
from uproot3.interp.objects import asstring
from uproot3.interp.objects import SimpleArray
from uproot3.interp.objects import STLVector
from uproot3.interp.objects import STLMap
from uproot3.interp.objects import STLString
from uproot3.interp.objects import Pointer
asdebug = asjagged(asdtype("u1"))

from uproot3 import pandas

# put help strings on everything (they're long, too disruptive to intersperse
# in the code, and are built programmatically to avoid duplication; Python's
# inline docstring method doesn't accept non-literals)
import uproot3._help

# convenient access to the version number
from uproot3.version import __version__

# don't expose uproot3.uproot3; it's ugly
del uproot3

__all__ = ["open", "xrootd", "http", "iterate", "numentries", "lazyarray", "lazyarrays", "daskarray", "daskframe", "create", "recreate", "update", "ZLIB", "LZMA", "LZ4", "ZSTD", "newtree", "newbranch", "MemmapSource", "FileSource", "XRootDSource", "HTTPSource", "ArrayCache", "ThreadSafeArrayCache", "interpret", "asdtype", "asarray", "asdouble32", "asstlbitset", "asjagged", "astable", "asobj", "asgenobj", "asstring", "asdebug", "SimpleArray", "STLVector", "STLMap", "STLString", "Pointer", "pandas", "__version__"]
