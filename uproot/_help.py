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
    "localsource": u"""localsource : function: path \u21d2 :py:class:`Source <uproot.source.source.Source>`
        function that will be applied to the path to produce an uproot :py:class:`Source <uproot.source.source.Source>` object if the path is a local file. Default is :py:meth:`MemmapSource.defaults <uproot.source.memmap.MemmapSource.defaults>` for memory-mapped files.""",

    # xrootdsource
    "xrootdsource": u"""xrootdsource : function: path \u21d2 :py:class:`Source <uproot.source.source.Source>`
        function that will be applied to the path to produce an uproot :py:class:`Source <uproot.source.source.Source>` object if the path is an XRootD URL. Default is :py:meth:`XRootDSource.defaults <uproot.source.xrootd.XRootDSource.defaults>` for XRootD with default chunk size/caching. (See :py:class:`XRootDSource <uproot.source.xrootd.XRootDSource>` constructor for details.)""",

    # options
    "options": u"""**options
        passed to :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` constructor.""",
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
        local file path or URL specifying the location of a file (note: not a Python file object!). If the URL schema is "root://", :py:func:`xrootd <uproot.xrootd>` will be called.

    {localsource}

    {xrootdsource}

    {options}

    Returns
    -------
    :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`
        top-level directory of the ROOT file.

    Notes
    -----
    The ROOTDirectory returned by this function is not necessarily an open file. File handles are managed internally by :py:class:`Source <uproot.source.source.Source>` objects to permit parallel reading. Although this function can be used in a ``with`` construct (which protects against unclosed files), the ``with`` construct has no meaning when applied to this function. Files will be opened or closed as needed to read data on demand.

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
    :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`
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

    Although this class has a constructor that could be called by a user, objects are usually created from ROOT files through :py:func:`open <uproot.rootio.open>` or :py:func:`xrootd <uproot.rootio.xrootd>`.

    :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` objects may be accessed as Python containers:

    - square brackets (``__getitem__``) read objects from the file by key name (see :py:meth:`get <uproot.rootio.ROOTDirectory.get>`).
    - the ``len`` function (``__len__``) returns the number of keys.
    - iteration (``__iter__``) iterates over the *names* of the keys only (like a ``dict``, see :py:meth:`keys <uproot.rootio.ROOTDirectory.keys>`).

    **Attributes, properties, and methods:**

    - **name** (*bytes*) name of the file or directory *as read from the ROOT file*. (ROOT files may be imprinted with a different name than they have in the file system.)

    - **compression** (:py:class:`Compression <uproot.source.compressed.Compression>`) the compression algorithm and level specified in the file header. (Some objects, including TTree branches, may have different compression settings than the global file settings.)

    - :py:meth:`get <uproot.rootio.ROOTDirectory.get>` read an object from the file, selected by name.

    - :py:meth:`keys <uproot.rootio.ROOTDirectory.keys>` iterate over key names in this directory.

    - :py:meth:`values <uproot.rootio.ROOTDirectory.values>` iterate over objects in this directory.

    - :py:meth:`items <uproot.rootio.ROOTDirectory.items>` iterate over *(key name, object)* pairs in this directory, like a ``dict``.

    - :py:meth:`classes <uproot.rootio.ROOTDirectory.classes>` iterate over *(key name, class name)* pairs in this directory.

    - :py:meth:`allkeys <uproot.rootio.ROOTDirectory.allkeys>` iterate over keys at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`keys <uproot.rootio.ROOTDirectory.keys>`).

    - :py:meth:`allvalues <uproot.rootio.ROOTDirectory.allvalues>` iterate over objects at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`values <uproot.rootio.ROOTDirectory.values>`).

    - :py:meth:`allitems <uproot.rootio.ROOTDirectory.allitems>` iterate over *(key name, object)* pairs at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`items <uproot.rootio.ROOTDirectory.items>`).

    - :py:meth:`allclasses <uproot.rootio.ROOTDirectory.allclasses>` iterate over *(key name, class name)* pairs at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`classes <uproot.rootio.ROOTDirectory.classes>`).
"""

_method(uproot.rootio.ROOTDirectory.get).__doc__ = \
u"""Read an object from the ROOT file or directory by name.

    Parameters
    ----------
    name : str (str)
        name of the object. Any text before a "``/``" is interpreted as a subdirectory, and subdirectories of any depth may be searched. A number after a "``;``" indicates a `TKey <uproot.rootio.TKey>` cycle.

    cycle : ``None`` or int
        `TKey <uproot.rootio.TKey>` cycle number to disambiguate keys of the same name. This argument overrides a number after a "``;``".

    Returns
    -------
    :py:class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`
        a freshly read object from the ROOT file.
    
    Notes
    -----

    This method, without the ``cycle`` argument, can be accessed more directly through square brackets (``__getitem__``) on the :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` object.
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.keys).__doc__ = \
u"""Iterate over key names in this directory.

    This method does not read objects.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}

    Returns
    -------
    *iterator over bytes*
        names of objects and subdirectories in the file.

    Notes
    -----

    This method can be accessed more directly by simply iterating over a :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` object.
""".format(**rootdirectory_fragments)
    
_method(uproot.rootio.ROOTDirectory.values).__doc__ = \
u"""Iterate over objects in this directory.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}

    Returns
    -------
    *iterator over* :py:class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`
        freshly read objects from the ROOT file.
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.items).__doc__ = \
u"""Iterate over *(key name, object)* pairs in this directory, like a ``dict``.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}

    Returns
    -------
    *iterator over (bytes,* :py:class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`*)*
        name-object pairs from the file.
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.classes).__doc__ = \
u"""Iterate over *(key name, class name)* pairs in this directory.

    This method does not read objects.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}

    Returns
    -------
    *iterator over *(bytes, bytes)*
        name-class name pairs from the file.
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.allkeys).__doc__ = \
u"""Iterate over keys at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`keys <uproot.rootio.ROOTDirectory.keys>`).

    This method does not read objects.

    Parameters
    ----------
    {filtername}

    {filterclass}

    Returns
    -------
    *iterator over bytes*
        names of objects and subdirectories in the file.
""".format(**rootdirectory_fragments)
    
_method(uproot.rootio.ROOTDirectory.allvalues).__doc__ = \
u"""Iterate over objects at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`values <uproot.rootio.ROOTDirectory.values>`).

    Parameters
    ----------
    {filtername}

    {filterclass}

    Returns
    -------
    *iterator over* :py:class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`
        freshly read objects from the ROOT file.
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.allitems).__doc__ = \
u"""Iterate over *(key name, object)* pairs at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`items <uproot.rootio.ROOTDirectory.items>`).

    Parameters
    ----------
    {filtername}

    {filterclass}

    Returns
    -------
    *iterator over (bytes,* :py:class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`*)*
        name-object pairs from the file.
""".format(**rootdirectory_fragments)

_method(uproot.rootio.ROOTDirectory.allclasses).__doc__ = \
u"""Iterate over *(key name, class name)* pairs at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`classes <uproot.rootio.ROOTDirectory.classes>`).

    This method does not read objects.

    Parameters
    ----------
    {filtername}

    {filterclass}

    Returns
    -------
    *iterator over *(bytes, bytes)*
        name-class name pairs from the file.
""".format(**rootdirectory_fragments)

################################################################ uproot.rootio.ROOTObject and uproot.rootio.ROOTStreamedObject

uproot.rootio.ROOTObject.__doc__ = \
u"""Superclass of all objects read out of a ROOT file (except :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`).

    If a :py:class:`ROOTObject <uproot.rootio.ROOTObject>` is not a :py:class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`, then its class definition is hard-coded, not derived from the file's *streamer info*.
"""

uproot.rootio.ROOTStreamedObject.__doc__ = \
u"""Superclass of all objects read out of a ROOT file with an automatically generated class, derived from the file's *streamer info*.
    
    Each subclass of a :py:class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>` has a ``version`` attribute, corresponding to the class version in the *streamer info*, and each object has a ``version`` attribute, read from the serialized object. If these versions do not match, an error is raised during the read.
"""

################################################################ uproot.tree fragments

tree_fragments = {
    # entrystart
    "entrystart": u"""entrystart : ``None`` or int
        entry at which reading starts (inclusive). If ``None`` *(default)*, start at the beginning of the branch.""",

    # entrystop
    "entrystop": u"""entrystop : ``None`` or int
        entry at which reading stops (exclusive). If ``None`` *(default)*, stop at the end of the branch.""",

    # entrystepsize
    "entrystepsize": u"""entrystepsize : positive int
        number of entries to provide in each step of iteration except the last in each file (unless it exactly divides the number of entries in the file).""",

    # branch
    "branch": u"""branch : str
        name of the branch to read.""",

    # interpretation
    "interpretation": u"""interpretation : ``None`` or :py:class:`Interpretation <uproot.interp.interp.Interpretation>`
        the meaning imposed upon the bytes of the file and the ultimate form to instantiate. If ``None`` *(default)*, :py:func:`interpret <uproot.interp.auto.interpret>` will be applied to the branch to generate an interpretation.""",

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

    # blocking
    "blocking": u"""blocking : bool
        if ``True`` *(default)*, do not exit this function until the arrays are read, and return those arrays. If ``False``, exit immediately and return a zero-argument function. That zero-argument function returns the desired array, and it blocks until the array is available. This option is only useful with a non-``None`` executor.""",

    # recursive
    "recursive": u"""recursive : bool
        if ``False`` *(default)*, only iterate at this tree/branch level; if ``True``, depth-first iterate over all subbranches as well.""",

    # filtername
    "filtername": u"""filtername : function: str \u21d2 bool
        only branches for which filtername(name) returns ``True`` are yielded by the iterator. Default returns ``True`` for all input.""",

    # filtertitle
    "filtertitle": u"""filtertitle : function: str \u21d2 bool
        only branches for which filtertitle(title) returns ``True`` are yielded by the iterator. Default returns ``True`` for all input.""",

    # i
    "i": u"""i : non-negative int
        basket number (must be greater than or equal to zero and strictly less than *numbaskets*)."""
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

    Returns
    -------
    *iterator over *(int, int, outputtype)* (if *reportentries*) or *outputtype*
        aligned array segments from the files.

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

    - square brackets (``__getitem__``) returns a branch by name (see :py:meth:`get <uproot.tree.TTreeMethods.get>`).
    - the ``len`` function (``__len__``) returns the number of entries (same as ``numentries``).
    - iteration (``__iter__``) has no implementation. This is to avoid confusion between iterating over all branches (probably not what you want, but fitting the pattern set by :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` and ``dict``) and iterating over the data. Also, iteration over data requires a user-provided ``entrystepsize``, so it must be started with a function (see :py:meth:`iterate <uproot.tree.TTreeMethods.iterate>`).

    **Attributes, properties, and methods:**

    - **name** (*bytes*) name of the TTree.
    - **title** (*bytes*) title of the TTree.
    - **numentries** (*int*) number of entries in the TTree (same as ``len``).
    - **pandas** connector to `Pandas <http://pandas.pydata.org/>`_ functions *(not implemented)*.
    - **numba** connector to `Numba <http://numba.pydata.org/>`_ functions *(not implemented)*.
    - **oamap** connector to `OAMap <https://github.com/diana-hep/oamap>`_ functions *(not implemented)*.

    - :py:meth:`get <uproot.tree.TTreeMethods.get>` return a branch by name (at any level of depth).
    - :py:meth:`keys <uproot.tree.TTreeMethods.keys>` iterate over branch names.
    - :py:meth:`values <uproot.tree.TTreeMethods.values>` iterate over branches.
    - :py:meth:`items <uproot.tree.TTreeMethods.items>` iterate over *(branch name, branch)* pairs.
    - :py:meth:`allkeys <uproot.tree.TTreeMethods.allkeys>` iterate over branch names at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`keys <uproot.tree.TTreeMethods.keys>`).
    - :py:meth:`allvalues <uproot.tree.TTreeMethods.allvalues>` iterate over branches at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`values <uproot.tree.TTreeMethods.values>`).
    - :py:meth:`allitems <uproot.tree.TTreeMethods.allitems>` iterate over *(branch name, branch)* pairs at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`items <uproot.tree.TTreeMethods.items>`).
    - :py:meth:`clusters <uproot.tree.TTreeMethods.clusters>` iterate over *(int, int)* pairs representing cluster entry starts and stops in this TTree *(not implemented)*.

    **Methods for reading array data:**

    - :py:meth:`array <uproot.tree.TTreeMethods.array>` read one branch into an array (or other object if provided an alternate *interpretation*).
    - :py:meth:`lazyarray <uproot.tree.TTreeMethods.lazyarray>` create a lazy array that would read the branch as needed.
    - :py:meth:`arrays <uproot.tree.TTreeMethods.arrays>` read many branches into arrays (or other objects if provided alternate *interpretations*).
    - :py:meth:`lazyarrays <uproot.tree.TTreeMethods.lazyarrays>` create many lazy arrays.
    - :py:meth:`iterate <uproot.tree.TTreeMethods.iterate>` iterate over many arrays at once, yielding a fixed number of entries at a time in all the arrays.
    - :py:meth:`iterate_clusters <uproot.tree.TTreeMethods.iterate_clusters>` iterate at cluster boundaries, which are more efficient but not necessarily a fixed number of entries *(not implemented)*.
"""

_method(uproot.tree.TTreeMethods.get).__doc__ = \
u"""Return a branch by name (at any level of depth).

    Parameters
    ----------
    name : str
        name of the branch to return.

    Returns
    -------
    :py:class:`TBranch <upoot.tree.TBranchMethods>`
        selected branch.
"""

_method(uproot.tree.TTreeMethods.keys).__doc__ = \
u"""Iterate over branch names.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over bytes*
        names of branches.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.values).__doc__ = \
u"""Iterate over branches.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over* :py:class:`TBranch <uproot.tree.TBranchMethods>`
        branches.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.items).__doc__ = \
u"""Iterate over *(branch name, branch)* pairs.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over (bytes,* :py:class:`TBranch <uproot.tree.TBranchMethods>`*)*
        name-branch pairs.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.allkeys).__doc__ = \
u"""Iterate over branch names at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`keys <uproot.tree.TTreeMethods.keys>`).

    Parameters
    ----------
    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over bytes*
        names of branches.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.allvalues).__doc__ = \
u"""Iterate over branches at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`values <uproot.tree.TTreeMethods.values>`).

    Parameters
    ----------
    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over* :py:class:`TBranch <uproot.tree.TBranchMethods>`
        branches.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.allitems).__doc__ = \
u"""Iterate over *(branch name, branch)* pairs at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`items <uproot.tree.TTreeMethods.items>`).

    Parameters
    ----------
    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over (bytes,* :py:class:`TBranch <uproot.tree.TBranchMethods>`
        name-branch pairs.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.clusters).__doc__ = \
u"""Iterate over *(int, int)* pairs representing cluster entry starts and stops in this TTree.

    ..todo:: Not implemented.

    Returns
    -------
    *iterator over (int, int)*
        start (inclusive) and stop (exclusive) pairs for each cluster.
"""

_method(uproot.tree.TTreeMethods.array).__doc__ = \
u"""Read one branch into an array (or other object if provided an alternate *interpretation*).

    Parameters
    ----------
    {branch}

    {interpretation}

    {entrystart}

    {entrystop}

    {cache}

    {rawcache}

    {keycache}

    {executor}

    {blocking}

    Returns
    -------
    array or other object, depending on *interpretation*.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.lazyarray).__doc__ = \
u"""Create a lazy array that would read the branch as needed.

    Parameters
    ----------
    {branch}

    {interpretation}

    {cache}

    {rawcache}

    {keycache}

    {executor}

    Returns
    -------
    lazy array.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.arrays).__doc__ = \
u"""read many branches into arrays (or other objects if provided alternate *interpretations*).

    Parameters
    ----------
    {branches}

    {outputtype}

    {entrystart}

    {entrystop}

    {cache}

    {rawcache}

    {keycache}

    {executor}

    {blocking}

    Returns
    -------
    outputtype of arrays or other objects, depending on *interpretation*.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.lazyarrays).__doc__ = \
u"""Create many lazy arrays.

    Parameters
    ----------
    {branches}

    {outputtype}

    {cache}

    {rawcache}

    {keycache}

    {executor}

    Returns
    -------
    outputtype of lazy arrays.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.iterate).__doc__ = \
u"""Iterate over many arrays at once, yielding a fixed number of entries at a time in all the arrays.

    Parameters
    ----------
    {entrystepsize}

    {branches}

    {outputtype}

    {reportentries}

    {entrystart}

    {entrystop}

    {cache}

    {rawcache}

    {keycache}

    {executor}

    Returns
    -------
    *iterator over *(int, int, outputtype)* (if *reportentries*) or *outputtype*
        aligned array segments from the TTree.
""".format(**tree_fragments)

_method(uproot.tree.TTreeMethods.iterate_clusters).__doc__ = \
u"""Iterate at cluster boundaries, which are more efficient but not necessarily a fixed number of entries.

    ..todo:: Not implemented.

    Parameters
    ----------
    {branches}

    {outputtype}

    {reportentries}

    {entrystart}

    {entrystop}

    {cache}

    {rawcache}

    {keycache}

    {executor}

    Returns
    -------
    *iterator over *(int, int, outputtype)* (if *reportentries*) or *outputtype*
        aligned array segments from the TTree.
""".format(**tree_fragments)

################################################################ uproot.tree.TBranchMethods

uproot.tree.TBranchMethods.__doc__ = \
u"""Adds array reading methods to TBranch objects that have been streamed from a ROOT file.

    - square brackets (``__getitem__``) returns a subbranch by name (see :py:meth:`get <uproot.tree.TBranchMethods.get>`).
    - the ``len`` function (``__len__``) returns the number of entries (same as ``numentries``).
    - iteration (``__iter__``) has no implementation. This is to avoid confusion between iterating over all subbranches (probably not what you want, but fitting the pattern set by :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` and ``dict``) and iterating over the data.

    **Attributes, properties, and methods:**

    - **name** (*bytes*) name of the TBranch.
    - **title** (*bytes*) title of the TBranch.
    - **compression** (:py:class:`Compression <uproot.source.compressed.Compression>`) the compression algorithm and level specified in the TBranch header. (Actual compression used may differ.)
    - :py:meth:`get <uproot.tree.TBranchMethods.get>` return a subbranch by name (at any level of depth).
    - :py:meth:`keys <uproot.tree.TBranchMethods.keys>` iterate over subbranch names.
    - :py:meth:`values <uproot.tree.TBranchMethods.values>` iterate over subbranches.
    - :py:meth:`items <uproot.tree.TBranchMethods.items>` iterate over *(subbranch name, subbranch)* pairs.
    - :py:meth:`allkeys <uproot.tree.TBranchMethods.allkeys>` iterate over subbranch names at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`keys <uproot.tree.TBranchMethods.keys>`).
    - :py:meth:`allvalues <uproot.tree.TBranchMethods.allvalues>` iterate over subbranches at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`values <uproot.tree.TBranchMethods.values>`).
    - :py:meth:`allitems <uproot.tree.TBranchMethods.allitems>` iterate over *(subbranch name, subbranch)* pairs at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`items <uproot.tree.TBranchMethods.items>`).

    **Branch information:**

    - **numentries** (*int*) number of entries in the TBranch (same as ``len``).
    - **numbaskets** (*int*) number of baskets in the TBranch.
    - :py:meth:`uncompressedbytes <uproot.tree.TBranchMethods.uncompressedbytes>` the number of bytes contained in the TBranch (data and offsets; not including any key headers) *after* decompression, if applicable.
    - :py:meth:`compressedbytes <uproot.tree.TBranchMethods.compressedbytes>` the number of bytes contained in the TBranch (data and offsets; not including any key headers) *before* decompression, if applicable.
    - :py:meth:`compressionratio <uproot.tree.TBranchMethods.compressionratio>` the uncompressed bytes divided by compressed bytes (greater than or equal to 1).
    - :py:meth:`numitems <uproot.tree.TBranchMethods.numitems>` the number of items in the TBranch, under a given interpretation.

    **Basket information:**

    - :py:meth:`basket_entrystart <uproot.tree.TBranchMethods.basket_entrystart>` the starting entry for a given basket (inclusive).
    - :py:meth:`basket_entrystop <uproot.tree.TBranchMethods.basket_entrystop>` the stopping entry for a given basket (exclusive).
    - :py:meth:`basket_numentries <uproot.tree.TBranchMethods.basket_numentries>` the number of entries in a given basket.
    - :py:meth:`basket_uncompressedbytes <uproot.tree.TBranchMethods.basket_uncompressedbytes>` the number of bytes contained in the basket (data and offsets; not including any key headers) *after* decompression, if applicable.
    - :py:meth:`basket_compressedbytes <uproot.tree.TBranchMethods.basket_compressedbytes>` the number of bytes contained in the basket (data and offsets; not including any key headers) *before* decompression, if applicable.
    - :py:meth:`basket_numitems <uproot.tree.TBranchMethods.basket_numitems>` the number of items in the basket, under a given interpretation.

    **Methods for reading array data:**

    - :py:meth:`basket <uproot.tree.TBranchMethods.array>` read the branch into an array (or other object if provided an alternate *interpretation*).
    - :py:meth:`basket <uproot.tree.TBranchMethods.lazyarray>` create a lazy array that would read the branch as needed.
    - :py:meth:`basket <uproot.tree.TBranchMethods.basket>` read a single basket into an array.
    - :py:meth:`basket <uproot.tree.TBranchMethods.baskets>` read baskets into a list of arrays.
    - :py:meth:`basket <uproot.tree.TBranchMethods.iterate_baskets>` iterate over baskets.
"""

_method(uproot.tree.TBranchMethods.get).__doc__ = \
u"""Return a subbranch by name (at any level of depth).

    Parameters
    ----------
    name : str
        name of the subbranch to return.

    Returns
    -------
    :py:class:`TBranch <upoot.tree.TBranchMethods>`
        selected branch.
"""

_method(uproot.tree.TBranchMethods.keys).__doc__ = \
u"""Iterate over subbranch names.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over bytes*
        names of branches.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.values).__doc__ = \
u"""Iterate over subbranches.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over* :py:class:`TBranch <uproot.tree.TBranchMethods>`
        branches.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.items).__doc__ = \
u"""Iterate over *(subbranch name, subbranch)* pairs.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over (bytes,* :py:class:`TBranch <uproot.tree.TBranchMethods>`*)*
        name-branch pairs.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.allkeys).__doc__ = \
u"""Iterate over subbranch names at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`keys <uproot.tree.TBranchMethods.keys>`).

    Parameters
    ----------
    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over bytes*
        names of branches.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.allvalues).__doc__ = \
u"""Iterate over subbranches at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`values <uproot.tree.TBranchMethods.values>`).

    Parameters
    ----------
    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over* :py:class:`TBranch <uproot.tree.TBranchMethods>`
        branches.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.allitems).__doc__ = \
u"""Iterate over *(subbranch name, subbranch)* pairs at all levels of depth (shortcut for passing ``recursive=True`` to :py:meth:`items <uproot.tree.TBranchMethods.items>`).

    Parameters
    ----------
    {filtername}

    {filtertitle}

    Returns
    -------
    *iterator over (bytes,* :py:class:`TBranch <uproot.tree.TBranchMethods>`
        name-branch pairs.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.uncompressedbytes).__doc__ = \
u"""The number of bytes contained in the TBranch (data and offsets; not including any key headers) *after* decompression, if applicable.

    Parameters
    ----------
    {keycache}

    Returns
    -------
    *int*
        uncompressed bytes.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.compressedbytes).__doc__ = \
u"""The number of bytes contained in the TBranch (data and offsets; not including any key headers) *before* decompression, if applicable.

    Parameters
    ----------
    {keycache}

    Returns
    -------
    *int*
        compressed bytes.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.compressionratio).__doc__ = \
u"""The uncompressed bytes divided by compressed bytes (greater than or equal to 1).

    Parameters
    ----------
    {keycache}

    Returns
    -------
    *float*
        compression ratio.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.numitems).__doc__ = \
u"""The number of items in the TBranch, under a given interpretation.

    Parameters
    ----------
    {interpretation}

    {keycache}

    Returns
    -------
    *int*
        number of items.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.basket_entrystart).__doc__ = \
u"""The starting entry for a given basket (inclusive).

    Parameters
    ----------
    {i}

    Returns
    -------
    *int*
        starting entry.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.basket_entrystop).__doc__ = \
u"""The stopping entry for a given basket (exclusive).

    Parameters
    ----------
    {i}

    Returns
    -------
    *int*
        stopping entry.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.basket_numentries).__doc__ = \
u"""The number of entries in a given basket.

    Parameters
    ----------
    {i}

    Returns
    -------
    *int*
        number of entries.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.basket_uncompressedbytes).__doc__ = \
u"""The number of bytes contained in the basket (data and offsets; not including any key headers) *after* decompression, if applicable.

    Parameters
    ----------
    {i}

    {keycache}

    Returns
    -------
    *int*
        number of uncompressed bytes.    
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.basket_compressedbytes).__doc__ = \
u"""The number of bytes contained in the basket (data and offsets; not including any key headers) *before* decompression, if applicable.

    Parameters
    ----------
    {i}

    {keycache}

    Returns
    -------
    *int*
        number of compressed bytes.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.basket_numitems).__doc__ = \
u"""The number of items in the basket, under a given interpretation.

    Parameters
    ----------
    {i}

    {interpretation}

    {keycache}

    Returns
    -------
    *int*
        number of items.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.array).__doc__ = \
u"""Read the branch into an array (or other object if provided an alternate *interpretation*).

    Parameters
    ----------
    {interpretation}

    {entrystart}

    {entrystop}

    {cache}

    {rawcache}

    {keycache}

    {executor}

    {blocking}

    Returns
    -------
    array or other object, depending on *interpretation*
        branch data.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.lazyarray).__doc__ = \
u"""Create a lazy array that would read the branch as needed.

    Parameters
    ----------
    {interpretation}

    {cache}

    {rawcache}

    {keycache}

    {executor}

    Returns
    -------
    lazy array
        branch data.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.basket).__doc__ = \
u"""Read a single basket into an array.

    Parameters
    ----------
    {i}

    {interpretation}

    {entrystart}

    {entrystop}

    {cache}

    {rawcache}

    {keycache}

    Returns
    -------
    array or other object, depending on *interpretation*.
        branch data.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.baskets).__doc__ = \
u"""Read baskets into a list of arrays.

    Parameters
    ----------
    {interpretation}

    {entrystart}

    {entrystop}

    {cache}

    {rawcache}

    {keycache}

    {reportentries}

    {executor}

    {blocking}

    Returns
    -------
    list of arrays or other objects, depending on *interpretation*.
        basket data.
""".format(**tree_fragments)

_method(uproot.tree.TBranchMethods.iterate_baskets).__doc__ = \
u"""Iterate over baskets.

    Parameters
    ----------
    {interpretation}

    {entrystart}

    {entrystop}

    {cache}

    {rawcache}

    {keycache}

    {reportentries}

    Returns
    -------
    iterator over arrays or other objects, depending on *interpretation*
        basket data.
""".format(**tree_fragments)
