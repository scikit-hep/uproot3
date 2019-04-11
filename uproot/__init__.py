#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

"""uproot -- ROOT I/O in pure Python and Numpy.

Basic cheat-sheet
-----------------

Open ROOT files with uproot.open (for reading) or uproot.create (for read-write).

    file = uproot.open("/path/to/my/file.root")
    file = uproot.open("root://path/to/my/file.root")
    file = uproot.open("http://path/to/my/file.root")
    writeable = uproot.create("/new/local/file.root")

These file objects act like dicts; get objects like TTrees from them with square brackets.

    tree = file["path/to/events"]
    tree = file["path/to/events;2"]            # optional cycle number
    writeable["name"] = numpy.histogram(...)   # write to files by assignment (histograms only)

TTree objects also act like dicts; get branches with square brackets or list them with keys().

    tree.keys()
    tree.allkeys()    # recursive branches-of-branches
    tree.show()       # display view
    tree["mybranch"]  # searches recursively

Get data as arrays with an array(...) or arrays(...) call.

    tree["mybranch"].array()
    tree.array("mybranch")
    tree.arrays(["branch1", "branch2", "branch3"])
    tree.arrays(["Muon_*"])

Variable numbers of objects per entry (particles per event) are handled by awkward-array:

    https://github.com/scikit-hep/awkward-array

The arrays(...) call returns a dict from branch name (bytes) to data (Numpy array) by default.
Change this by passing an outputtype class (e.g. dict, tuple, pandas.DataFrame).

    x, y, z = tree.arrays(["x", "y", "z"], outputtype=tuple)

For more idiomatic Pandas defaults, use tree.pandas.df().

    df = tree.pandas.df()

If the desired branches do not fit into memory, iterate over chunks of entries with iterate().
The interface is the same as above: you get the same dict/tuple/DataFrame with fewer entries.

    for x, y, z in tree.iterate(["x", "y", "z"], outputtype=tuple):
        do_something(x, y, z)

To iterate over many files (like TChain), do uproot.iterate(...).

    for arrays in uproot.iterate("files*.root", "path/to/events", ["Muon_*"]):
        do_something(arrays)

Intermediate cheat-sheet
------------------------

Each call to array/arrays/iterate reads the file again. For faster access after the first time,
pass a dict-like object to the cache parameter and uproot will try the cache first.

    cache = {}
    arrays = tree.arrays(["Muon_*"], cache=cache)    # slow
    arrays = tree.arrays(["Muon_*"], cache=cache)    # fast

You control the cache object. If you're running out of memory, remove it or remove items from it.
Or use one of the dict-like caches from cachetools (already installed) or another library.

For parallel processing, pass a Python 3 executor.

    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(32)
    arrays = tree.arrays(["Muon_*"], executor=executor)

To get the number of entries per file in a a collection of files, use uproot.numentries().

    uproot.numentries("tests/samples/sample*.root", "sample", total=False)

For arrays that read on demand, use uproot.lazyarray and uproot.lazyarrays.
For processing with Dask, use uproot.daskarray, uproot.daskarrays, or uproot.daskframe.

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

    mybranch.array(uproot.asdebug)    # view raw bytes of each entry

By default, local files are read as memory-mapped arrays. Change this by setting

    open("...", localsource=lambda path: uproot.LocalSource(path, **uproot.LocalSource.defaults))

The same procedure sets options for uproot.XRootDSource and uproot.HTTPSource.
"""

# high-level entry points
from uproot.rootio import open, xrootd, http
from uproot.tree import iterate, numentries, lazyarray, lazyarrays, daskarray, daskarrays, daskframe
from uproot.write.TFile import TFileCreate as create
from uproot.write.TFile import TFileRecreate as recreate
from uproot.write.TFile import TFileUpdate as update

from uproot.source.memmap import MemmapSource
from uproot.source.file import FileSource
from uproot.source.xrootd import XRootDSource
from uproot.source.http import HTTPSource

from uproot.interp.auto import interpret
from uproot.interp.numerical import asdtype
from uproot.interp.numerical import asarray
from uproot.interp.numerical import asdouble32
from uproot.interp.numerical import asstlbitset
from uproot.interp.jagged import asjagged
from uproot.interp.objects import astable
from uproot.interp.objects import asobj
from uproot.interp.objects import asgenobj
from uproot.interp.objects import asstring
from uproot.interp.objects import SimpleArray
from uproot.interp.objects import STLVector
from uproot.interp.objects import STLMap
from uproot.interp.objects import STLString
asdebug = asjagged(asdtype("u1"))

from uproot import pandas

# put help strings on everything (they're long, too disruptive to intersperse
# in the code, and are built programmatically to avoid duplication; Python's
# inline docstring method doesn't accept non-literals)
import uproot._help

# convenient access to the version number
from uproot.version import __version__

# don't expose uproot.uproot; it's ugly
del uproot

__all__ = ["open", "xrootd", "http", "iterate", "numentries", "lazyarray", "lazyarrays", "daskarray", "daskarrays", "daskframe", "create", "recreate", "update", "MemmapSource", "FileSource", "XRootDSource", "HTTPSource", "interpret", "asdtype", "asarray", "asdouble32", "asstlbitset", "asjagged", "astable", "asobj", "asgenobj", "asstring", "asdebug", "SimpleArray", "STLVector", "STLMap", "STLString", "pandas", "__version__"]
