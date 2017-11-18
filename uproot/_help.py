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

import uproot

def _method(x):
    if hasattr(x, "__func__"):
        return x.__func__
    else:
        return x

################################################################ uproot.rootio fragments

open_fragments = {
    # localsource
    "localsource": u"""localsource : function: path \u21d2 :class:`Source <uproot.source.source.Source>`
        function that will be applied to the path to produce an uproot :class:`Source <uproot.source.source.Source>` object if the path is a local file. Default is :meth:`MemmapSource.defaults <uproot.source.memmap.MemmapSource.defaults>` for memory-mapped files.""",

    # xrootdsource
    "xrootdsource": u"""xrootdsource : function: path \u21d2 :class:`Source <uproot.source.source.Source>`
        function that will be applied to the path to produce an uproot :class:`Source <uproot.source.source.Source>` object if the path is an XRootD URL. Default is :meth:`XRootDSource.defaults <uproot.source.xrootd.XRootDSource.defaults>` for XRootD with default chunk size/caching. (See :class:`XRootDSource <uproot.source.xrootd.XRootDSource>` constructor for details.)""",

    # options
    "options": u"""**options
        passed to :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` constructor.""",
}

rootdirectory_fragments = {
    # recursive
    "recursive": u"""recursive : bool
        if ``False`` *(default)*, only iterate over this directory level; if ``True``, depth-first iterate over all subdirectories as well.""",

    # filtername
    "filtername": u"""filtername : function: str \u21d2 bool
        only keys for which filtername(name) returns ``True`` are yielded by the iterator (does not eliminate subdirectories if ``recursive=True``). Default returns ``True`` for all input.""",

    # filterclass
    "filterclass": u"""filterclass : function: str \u21d2 bool
        only keys for which filterclass(class name) returns ``True`` are yielded by the iterator (does not eliminate subdirectories if ``recursive=True``). Default returns ``True`` for all input.""",
    }

################################################################ uproot.rootio.open

uproot.rootio.open.__doc__ = \
u"""Opens a ROOT file (local or remote), specified by file path.

    Parameters
    ----------
    path : str
        local file path or URL specifying the location of a file (note: not a Python file object!). If the URL schema is "root://", :func:`xrootd <uproot.xrootd>` will be called.

    {localsource}

    {xrootdsource}

    {options}

    Returns
    -------
    :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`
        top-level directory of the ROOT file.

    Notes
    -----
    The ROOTDirectory returned by this function is not necessarily an open file. File handles are managed internally by :class:`Source <uproot.source.source.Source>` objects to permit parallel reading. Although this function can be used in a ``with`` construct (which protects against unclosed files), the ``with`` construct has no meaning when applied to this function. Files will be opened or closed as needed to read data on demand.

    Examples
    --------
    ::

        import uproot
        tfile = uproot.open("/my/root/file.root")
    """.format(**open_fragments)

################################################################ uproot.rootio.xrootd

uproot.rootio.xrootd.__doc__ = \
u"""Opens a remote ROOT file with XRootD (if installed).

    Parameters
    ----------
    path : str
        URL specifying the location of a file.

    {xrootdsource}

    {options}

    Returns
    -------
    :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`
        top-level directory of the ROOT file.
    
    Examples
    --------
    ::

        import uproot
        tfile = uproot.open("root://eos-server.cern/store/file.root")
    """.format(**open_fragments)

################################################################ uproot.rootio.ROOTDirectory

uproot.rootio.ROOTDirectory.__doc__ = \
u"""Represents a ROOT file or directory, an entry point for reading objects.

    Although this class has a constructor that could be called by a user, objects are usually created from ROOT files through :func:`open <uproot.rootio.open>` or :func:`xrootd <uproot.rootio.xrootd>`.

    :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` objects may be accessed as Python containers:

    - square brackets (``__getitem__``) read objects from the file by key name (see :meth:`get <uproot.rootio.ROOTDirectory.get>`).
    - the ``len`` function (``__len__``) returns the number of keys.
    - iteration (``__iter__``) iterates over the *names* of the keys only (like a ``dict``, see :meth:`keys <uproot.rootio.ROOTDirectory.keys>`).

    **Attributes, properties, and methods:**

    - **name** (*bytes*) name of the file or directory *as read from the ROOT file*. (ROOT files may be imprinted with a different name than they have in the file system.)

    - **compression** (:class:`Compression <uproot.source.compressed.Compression>`) the compression algorithm and level specified in the file header. (Some objects, including TTree branches, may have different compression settings than the global file settings.)

    - :meth:`get <uproot.rootio.ROOTDirectory.get>` read an object from the file, selected by name.

    - :meth:`keys <uproot.rootio.ROOTDirectory.keys>` iterate over key names in this directory.

    - :meth:`values <uproot.rootio.ROOTDirectory.values>` iterate over objects in this directory.

    - :meth:`items <uproot.rootio.ROOTDirectory.items>` iterate over key-value pairs in this directory, like a ``dict``.

    - :meth:`classes <uproot.rootio.ROOTDirectory.classes>` iterate over key-class name pairs in this directory.

    - :meth:`allkeys <uproot.rootio.ROOTDirectory.allkeys>` iterate over keys at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`keys <uproot.rootio.ROOTDirectory.keys>`).

    - :meth:`allvalues <uproot.rootio.ROOTDirectory.allvalues>` iterate over objects at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`values <uproot.rootio.ROOTDirectory.values>`).

    - :meth:`allitems <uproot.rootio.ROOTDirectory.allitems>` iterate over key-value pairs at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`items <uproot.rootio.ROOTDirectory.items>`).

    - :meth:`allclasses <uproot.rootio.ROOTDirectory.allclasses>` iterate over key-class name pairs at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`classes <uproot.rootio.ROOTDirectory.classes>`).
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.get).__doc__ = \
u"""Read an object from the ROOT file or directory by name.

    Parameters
    ----------
    name : str (unicode or bytes)
        name of the object. Any text before a "``/``" is interpreted as a subdirectory, and subdirectories of any depth may be searched. A number after a "``;``" indicates a `TKey <uproot.rootio.TKey>` cycle.

    cycle : ``None`` or int
        `TKey <uproot.rootio.TKey>` cycle number to disambiguate keys of the same name. This argument overrides a number after a "``;``".

    Notes
    -----

    This method, without the ``cycle`` argument, can be accessed more directly through square brackets (``__getitem__``) on the :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` object.
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.keys).__doc__ = \
u"""Iterate over key names in this directory.

    This method does not read objects.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}

    Notes
    -----

    This method can be accessed more directly by simply iterating over a :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` object.
""".format(**rootdirectory_fragments)
    
_method(uproot.rootio.ROOTDirectory.values).__doc__ = \
u"""Iterate over objects in this directory.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.items).__doc__ = \
u"""Iterate over key-value pairs in this directory, like a ``dict``.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.classes).__doc__ = \
u"""Iterate over key-class name pairs in this directory.

    This method does not read objects.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.allkeys).__doc__ = \
u"""Iterate over keys at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`keys <uproot.rootio.ROOTDirectory.keys>`).

    This method does not read objects.

    Parameters
    ----------
    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)
    
_method(uproot.rootio.ROOTDirectory.allvalues).__doc__ = \
u"""Iterate over objects at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`values <uproot.rootio.ROOTDirectory.values>`).

    Parameters
    ----------
    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.allitems).__doc__ = \
u"""Iterate over key-value pairs at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`items <uproot.rootio.ROOTDirectory.items>`).

    Parameters
    ----------
    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.allclasses).__doc__ = \
u"""Iterate over key-class name pairs at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`classes <uproot.rootio.ROOTDirectory.classes>`).

    This method does not read objects.

    Parameters
    ----------
    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

################################################################ uproot.rootio.ROOTObject and uproot.rootio.ROOTStreamedObject

uproot.rootio.ROOTObject.__doc__ = \
u"""Superclass of all objects read out of a ROOT file (except :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`).

    If a :class:`ROOTObject <uproot.rootio.ROOTObject>` is not a :class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`, then its class definition is hard-coded, not derived from the file's *streamer info*.
"""

uproot.rootio.ROOTStreamedObject.__doc__ = \
u"""Superclass of all objects read out of a ROOT file with an automatically generated class, derived from the file's *streamer info*.
    
    Each subclass of a :class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>` has a ``version`` attribute, corresponding to the class version in the *streamer info*, and each object has a ``version`` attribute, read from the serialized object. If these versions do not match, an error is raised during the read.
"""

################################################################ uproot.tree fragments

tree_fragments = {
    # entrystepsize
    "entrystepsize": u"""entrystepsize : positive int
        number of entries to provide in each step of iteration except the last in each file (unless it exactly divides the number of entries in the file).""",

    # branches
    "branches": u"""branches
        - if ``None`` *(default)*, select all *interpretable* branches;
        - if a function :py:class:`TBranchMethods <uproot.tree.TBranchMethods>` \u21d2 ``None`` or :py:class:`Interpretation <uproot.interp.interp.Interpretation>`, select branches for which the function does not return ``None`` and use the interpretation it returns otherwise;
        - if a ``dict`` of str \u2192 :py:class:`Interpretation <uproot.interp.interp.Interpretation>`, select branches named by keys and use interpretations from the associated values;
        - if a list of str, select branches by name
        - if a single str, select a single branch""",

    # outputtype
    "outputtype": u"""outputtype : type
        constructor for the desired yield type, such as ``dict`` *(default)*, ``OrderedDict``, ``tuple``, ``namedtuple``, custom user class, etc.""",

    # reportentries
    "reportentries": u"""reportentries : bool
        if ``False`` *(default)*, yield only arrays (as ``outputtype``); otherwise, yield 3-tuple: *(entry start, entry stop, arrays)*, where *entry start* is inclusive and *entry stop* is exclusive.""",

    # cache
    "cache": u"""cache : ``None`` or ``dict``-like object
        if not ``None`` *(default)*, chunks of fully interpreted data (at most basket size) will be saved in the ``dict``-like object for later use. If arrays are later accessed with a different interpretation, the output may be wrong.""",

    # rawcache
    "rawcache": u"""rawcache : ``None`` or ``dict``-like object
        if not ``None`` *(default)*, chunks of raw basket data (exactly basket size) will be saved in the ``dict``-like object for later use. Arrays may be later accessed with a different interpretation because raw data must be reinterpreted each time.""",

    # keycache
    "keycache": u"""keycache : ``None`` or ``dict``-like object
        if not ``None`` *(default)*, basket TKeys will be saved in the ``dict``-like object for later use. TKeys are small, but require file access, so caching them can speed up repeated access.""",

    # executor
    "executor": u"""executor : `concurrent.futures.Executor <https://docs.python.org/3/library/concurrent.futures.html>`_
        if not ``None`` *(default)*, parallelize basket-reading and decompression by scheduling tasks on the executor. Assumes caches are thread-safe.""",

    }

################################################################ uproot.tree.iterate

uproot.tree.iterate.__doc__ = \
u"""Opens a series of ROOT files (local or remote), iterating over events in chunks of ``entrystepsize``.

    All but the first two parameters are identical to :py:meth:`uproot.tree.TreeMethods.iterate`.

    Parameters
    ----------
    path : str or list of str
        glob pattern(s) for local file paths (POSIX wildcards like "``*``") or URLs specifying the locations of the files. A list of filenames are processed in the given order, but glob patterns get pre-sorted to ensure a predictable order.

    treepath : str
        path within each ROOT file to find the TTree (may include "``/``" for subdirectories or "``;``" for cycle numbers).

    {entrystepsize}

    {branches}

    {outputtype}

    {reportentries}

    {cache}

    {rawcache}

    {keycache}

    {localsource}

    {xrootdsource}

    {options}

    Examples
    --------
    ::

        from math import *
        import numpy
        import uproot

        iterator = uproot.iterate(
            "/my/data*.root", "ParticleTree", 10000,
            ["pt", "eta", "phi"], outputtype=tuple)

        px = numpy.empty(10000)

        for pt, eta, phi in iterator:
            px[:len(pt)] = pt * sinh(eta) * cos(phi)
            print(px[:len(pt)])
    """.format(**dict(list(open_fragments.items()) + list(tree_fragments.items())))

################################################################ uproot.tree.TTreeMethods

uproot.tree.TTreeMethods.__doc__ = \
u"""Adds array reading methods to TTree objects that have been streamed from a ROOT file.

    - square brackets (``__getitem__``) returns a branch by name (see :meth:`get <uproot.tree.TTreeMethods.get>`).
    - the ``len`` function (``__len__``) returns the number of entries (same as ``numentries``).
    - iteration (``__iter__``) has no implementation. This is to avoid confusion between iterating over all branches (probably not what you want, but fitting the pattern set by :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` and ``dict``) and iterating over the data. Also, iteration over data requires a user-provided ``entrystepsize``, so it must be started with a function (see :meth:`iterate <uproot.tree.TTreeMethods.iterate>`).

    **Attributes, properties, and methods:**

    - **name** (*bytes*) name of the TTree.
    - **title** (*bytes*) title of the TTree.
    - **numentries** (*int*) number of entries in the TTree (same as ``len``).
    - **pandas** connector to `Pandas <http://pandas.pydata.org/>`_ functions *(not implemented)*.
    - **numba** connector to `Numba <http://numba.pydata.org/>`_ functions *(not implemented)*.
    - **oamap** connector to `OAMap <https://github.com/diana-hep/oamap>`_ functions *(not implemented)*.

    - :meth:`get <uproot.tree.TTreeMethods.get>` return a branch by name (at any level of depth).
    - :meth:`keys <uproot.tree.TTreeMethods.keys>` iterate over branch names.
    - :meth:`values <uproot.tree.TTreeMethods.values>` iterate over branches.
    - :meth:`items <uproot.tree.TTreeMethods.items>` iterate over branch name, branch pairs.
    - :meth:`allkeys <uproot.tree.TTreeMethods.allkeys>` iterate over branch names at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`keys <uproot.tree.TTreeMethods.keys>`).
    - :meth:`allvalues <uproot.tree.TTreeMethods.allvalues>` iterate over branches at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`values <uproot.tree.TTreeMethods.values>`).
    - :meth:`allitems <uproot.tree.TTreeMethods.allitems>` iterate over branch name, branch pairs at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`items <uproot.tree.TTreeMethods.items>`).
    - :meth:`clusters <uproot.tree.TTreeMethods.clusters>` iterate over clusters in this TTree *(not implemented)*.

    **Methods for reading array data:**

    - :meth:`array <uproot.tree.TTreeMethods.array>` read one branch into an array.
    - :meth:`lazyarray <uproot.tree.TTreeMethods.lazyarray>` create a lazy array that would read the branch as needed.
    - :meth:`arrays <uproot.tree.TTreeMethods.arrays>` read potentially many branches into arrays.
    - :meth:`lazyarrays <uproot.tree.TTreeMethods.lazyarrays>` create potentially many lazy arrays.
    - :meth:`iterate <uproot.tree.TTreeMethods.iterate>` iterate over potentially many arrays at once, yielding a fixed number of entries at a time in all the arrays.
    - :meth:`iterate_clusters <uproot.tree.TTreeMethods.iterate_clusters>` iterate at cluster boundaries, which are more efficient but not necessarily a fixed number of entries *(not implemented)*.
""".format()
