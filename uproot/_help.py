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
u"""Represents a ROOT file or directory, an entry point for extracting objects.

    Although this class has a constructor that could be called by a user, objects are usually created from ROOT files through :func:`open <uproot.rootio.open>` or :func:`xrootd <uproot.rootio.xrootd>`.

    :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` objects may be accessed as Python containers:

    - square brackets (``__getitem__``) extract objects by key name (see :meth:`get <uproot.rootio.ROOTDirectory.get>`)
    - the ``len`` function (``__len__``) returns the number of keys.
    - iteration (``__iter__``) iterates over the *names* of the keys only (like a ``dict``, see :meth:`keys <uproot.rootio.ROOTDirectory.keys>`).

    **Attributes, properties, and methods:**

    - **name** (*str*) name of the file or directory *as read from the ROOT file*. (ROOT files may be imprinted with a different name than they have in the file system.)

    - **compression** (:class:`Compression <uproot.source.compressed.Compression>`) the compression algorithm and level specified in the file header. (Some objects, including TTree branches, may have different compression settings than the global file settings.)

    - :meth:`get <uproot.rootio.ROOTDirectory.get>` extract an object by name.

    - :meth:`keys <uproot.rootio.ROOTDirectory.keys>` iterate over key names.

    - :meth:`values <uproot.rootio.ROOTDirectory.values>` iterate over objects contained in the file or directory.

    - :meth:`items <uproot.rootio.ROOTDirectory.items>` iterate over key-value pairs, like a ``dict``.

    - :meth:`classes <uproot.rootio.ROOTDirectory.classes>` iterate over key-class name pairs without extracting the objects.

    - :meth:`allkeys <uproot.rootio.ROOTDirectory.allkeys>` iterate over keys at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`keys <uproot.rootio.ROOTDirectory.keys>`).

    - :meth:`allvalues <uproot.rootio.ROOTDirectory.allvalues>` iterate over values at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`values <uproot.rootio.ROOTDirectory.values>`).

    - :meth:`allitems <uproot.rootio.ROOTDirectory.allitems>` iterate over key-value pairs at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`items <uproot.rootio.ROOTDirectory.items>`).

    - :meth:`allclasses <uproot.rootio.ROOTDirectory.allclasses>` iterate over key-class name pairs at all levels of depth (shortcut for passing ``recursive=True`` to :meth:`classes <uproot.rootio.ROOTDirectory.classes>`).
""".format(**rootdirectory_fragments)

uproot.rootio.ROOTDirectory.get.__func__.__doc__ = \
u"""Extract an object from the ROOT file or directory by name.

    Parameters
    ----------
    name : str (unicode or bytes)
        name of the object. Any text before a "``/``" is interpreted as a subdirectory, and subdirectories of any depth may be searched. A number after a "``;``" indicates a `TKey <uproot.rootio.TKey>` cycle.

    cycle : ``None`` or int
        `TKey <uproot.rootio.TKey>` cycle number to disambiguate keys of the same name. This argument overrides a number after a "``;``".

    Notes
    -----

    This method, without the ``cycle`` argument, can be called directly through square brackets (``__getitem__``) on the :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` object.
""".format(**rootdirectory_fragments)

uproot.rootio.ROOTDirectory.keys.__func__.__doc__ = \
u"""Iterate over the key names of this ROOT file or directory.

    This function does not read the objects from disk.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)
    
uproot.rootio.ROOTDirectory.values.__func__.__doc__ = \
u"""Iterate over objects contained in this ROOT file or directory.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

uproot.rootio.ROOTDirectory.items.__func__.__doc__ = \
u"""Iterate over key-value pairs from this ROOT file or directory, like a ``dict``.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

uproot.rootio.ROOTDirectory.classes.__func__.__doc__ = \
u"""Iterate over key name, class name pairs from this ROOT file or directory.

    This function does not read the objects from disk.

    Parameters
    ----------
    {recursive}

    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

uproot.rootio.ROOTDirectory.allkeys.__func__.__doc__ = \
u"""Iterate over the key names of in this directory and all nested directories (a shortcut for `keys <uproot.rootio.ROOTDirectory.keys>` with ``recursive=True``).

    This function does not read the objects from disk.

    Parameters
    ----------
    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)
    
uproot.rootio.ROOTDirectory.allvalues.__func__.__doc__ = \
u"""Iterate over objects contained in this directory and all nested directories (a shortcut for `values <uproot.rootio.ROOTDirectory.values>` with ``recursive=True``).

    Parameters
    ----------
    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

uproot.rootio.ROOTDirectory.allitems.__func__.__doc__ = \
u"""Iterate over key-value pairs from this directory and all nested directories (a shortcut for `items <uproot.rootio.ROOTDirectory.items>` with ``recursive=True``).

    Parameters
    ----------
    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

uproot.rootio.ROOTDirectory.allclasses.__func__.__doc__ = \
u"""Iterate over key name, class name pairs from this directory and all nested directories (a shortcut for `classes <uproot.rootio.ROOTDirectory.classes>` with ``recursive=True``).

    Parameters
    ----------
    {filtername}

    {filterclass}
""".format(**rootdirectory_fragments)

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
