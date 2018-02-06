uproot
======

.. image:: https://travis-ci.org/scikit-hep/uproot.svg?branch=master
   :target: https://travis-ci.org/scikit-hep/uproot

.. inclusion-marker-1-do-not-remove

ROOT I/O in pure Python and Numpy.

uproot (originally μproot, for "micro-Python ROOT") is a reader and (someday) a writer of the `ROOT file format <https://root.cern/>`_ using only Python and Numpy. Unlike the standard C++ ROOT implementation, uproot is only an I/O library, primarily intended to stream data into machine learning libraries in Python. Unlike PyROOT and root_numpy, uproot does not depend on C++ ROOT. Instead, it uses Numpy calls to rapidly cast data blocks in the ROOT file as Numpy arrays.

It is important to note that uproot is *not* maintained by the ROOT project team, so post bug reports as `uproot GitHub issues <https://github.com/scikit-hep/uproot/issues>`_, not on any ROOT forum.

.. inclusion-marker-2-do-not-remove

Installation
------------

Install OAMap like any other Python package:

.. code-block:: bash

    pip install uproot --user

or similar (use ``sudo``, ``virtualenv``, or ``conda`` if you wish).

Strict dependencies:
""""""""""""""""""""

- `Python <http://docs.python-guide.org/en/latest/starting/installation/>`_ (2.6+, 3.4+)
- `Numpy <https://scipy.org/install.html>`_

Recommended dependencies:
"""""""""""""""""""""""""

- `lz4 <https://anaconda.org/anaconda/lz4>`_ compression used by some ROOT files
- `lzma <https://anaconda.org/conda-forge/backports.lzma>`_ compression used by some ROOT files; this is part of the Python 3 standard library, so only install for Python 2

Optional dependencies:
""""""""""""""""""""""

- `XRootD <https://anaconda.org/nlesc/xrootd>`_ to access remote files
- `python-futures <https://pypi.python.org/pypi/futures>`_ for parallel processing; this is part of the Python 3 standard library, so only install for Python 2
- `Numba and LLVM <http://numba.pydata.org/numba-doc/latest/user/installing.html>`_ to JIT-compile functions (requires a particular version of LLVM, follow instructions)

*Reminder: you do not need C++ ROOT to run uproot.*

.. inclusion-marker-3-do-not-remove

Getting started
---------------

Download a Z → μμ `flat ntuple <http://scikit-hep.org/uproot/examples/Zmumu.root>`_ and a H → ZZ → μμμμ `structured TTree <http://scikit-hep.org/uproot/examples/HZZ.root>`_.

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/Zmumu.root
    wget http://scikit-hep.org/uproot/examples/HZZ.root

Open each of the files; uproot presents them as ``dict``-like objects with ROOT names and objects as keys and values. (The "cycle number" after the semicolon can usually be ignored.)

.. code-block:: python

    >>> import uproot
    >>> uproot.open("Zmumu.root").keys()
    ['events;1']
    >>> uproot.open("HZZ.root").keys()
    ['events;1']

Since the file acts as a ``dict``, access the TTrees with square brackets. TTrees are also ``dict``-like objects, with branch names and branches as keys and values. (Hint: ``allkeys()`` lists branches recursively, if they're nested.)

.. code-block:: python

    >>> zmumu = uproot.open("Zmumu.root")["events"]
    >>> hzz = uproot.open("HZZ.root")["events"]
    >>> zmumu.keys()
    ['Type', 'Run', 'Event', 'E1', 'px1', 'py1', 'pz1', 'pt1', 'eta1', 'phi1', 'Q1', 'E2',
     'px2', 'py2', 'pz2', 'pt2', 'eta2', 'phi2', 'Q2', 'M']
    >>> hzz.keys()
    ['NJet', 'Jet_Px', 'Jet_Py', 'Jet_Pz', 'Jet_E', 'Jet_btag', 'Jet_ID', 'NMuon', 'Muon_Px',
     'Muon_Py', 'Muon_Pz', 'Muon_E', 'Muon_Charge', 'Muon_Iso', 'NElectron', 'Electron_Px',
     'Electron_Py', 'Electron_Pz', 'Electron_E', 'Electron_Charge', 'Electron_Iso', 'NPhoton',
    ...

You can turn a chosen set of branches into Numpy arrays with the ``arrays`` method. Each array represents the values of a single attribute for all events, just as they're stored in a split ROOT file.

.. code-block:: python

    >>> zmumu.arrays(["px1", "py1", "pz1"])
    {'px1': array([-41.19528764,  35.11804977, ..., 32.37749196,  32.48539387]),
     'py1': array([ 17.4332439 , -16.57036233, ..., 1.19940578,   1.2013503 ]),
     'pz1': array([-68.96496181, -48.77524654, ..., -74.53243061, -74.80837247])}

If the number of items per entry is not constant, such as the number of jets in an event, they can't be expressed as flat Numpy arrays. Instead, uproot loads them into `jagged arrays <https://en.wikipedia.org/wiki/Jagged_array>`_.

.. code-block:: python

    >>> hzz.array("Jet_E")
    jaggedarray([[],
                 [44.137363],
                 [],
                 ...,
                 [55.95058],
                 [229.57799  33.92035],
                 []])

A jagged array behaves like an array of unequal-length arrays,

.. code-block:: python

    >>> for jetenergies in hzz.array("Jet_E"):
    ...     print("event")
    ...     for jetenergy in jetenergies:
    ...         print(jetenergy)
    ...
    event
    event
    44.137363
    event
    event
    230.34601
    101.35884
    60.08414

But it's built out of regular Numpy arrays, for use in libraries that accept Numpy.

.. code-block:: python

    >>> jaggedarray.content
    array([ 44.137363, 230.34601 , 101.35884 , ...,  55.95058 , 229.57799 ,
            33.92035 ], dtype=float32)
    >>> jaggedarray.starts
    array([   0,    0,    1, ..., 2770, 2771, 2773])
    >>> jaggedarray.stops
    array([   0,    1,    1, ..., 2771, 2773, 2773])

.. inclusion-marker-4-do-not-remove

Reference documentation
-----------------------

The complete reference documentation is available on `uproot.readthedocs.io <http://uproot.readthedocs.io/en/latest/>`_. These are exhaustive descriptions of each function and its parameters, also available as Python help strings.

- `Opening files <http://uproot.readthedocs.io/en/latest/opening-files.html>`_
- `ROOT I/O <http://uproot.readthedocs.io/en/latest/root-io.html>`_
- `TTree methods <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`_
- `TBranch methods <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`_

Introductory tutorials
----------------------

Reference documentation is not the place to start learning about a topic. Introductory tutorials are included on this page.

- `Exploring a file <#exploring-a-file>`_
- `Array-reading options <#array-reading-options>`_
- `Remote files through XRootD <#remote-files-through-xrootd>`_
- `Reading only part of a TBranch <#reading-only-part-of-a-tbranch>`_
- `Iterating over files (like TChain) <#iterating-over-files-like-tchain>`_
- `Non-flat TTrees: jagged arrays and more <#non-flat-ttrees-jagged-arrays-and-more>`_
- `Non-TTrees: histograms and more <#non-ttrees-histograms-and-more>`_
- `Caching data <#caching-data>`_
- `Parallel processing <#parallel-processing>`_
- `Lazy arrays <#lazy-arrays>`_
- `Connectors to other packages <#connectors-to-other-packages>`_

.. inclusion-marker-5-do-not-remove

Exploring a file
""""""""""""""""

Download the `nesteddirs.root <http://scikit-hep.org/uproot/examples/nesteddirs.root>`_ sample and open it with uproot.

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/nesteddirs.root

.. code-block:: python

    >>> import uproot
    >>> file = uproot.open("nesteddirs.root")

This ``file`` is a `ROOTDirectory`_, a class that can represent either a whole ROOT file or a TDirectory within that file. It emulates a Python ``dict``, so if you're familiar with this interface, you don't have to remember many method names. The "keys" are the names ROOT uses to find objects in files and the "values" are the data themselves.

.. code-block:: python

    >>> file.keys()                                      # get keys as a list
    ['one;1', 'three;1']
    >>> file.iterkeys()                                  # iterate over keys
    <generator object iterkeys at 0x77209e67c0a0>
    >>> (x for x in file)                                # iterate over keys (just like a dict)
    <generator object <genexpr> at 0x7de7eca80320>
    >>> file.allkeys()                                   # get all keys recursively
    ['one;1', 'one/two;1', 'one/two/tree;1', 'one/tree;1', 'three;1', 'three/tree;1']

If you only ask for the keys, the data won't be loaded (which can be important for performance!). The ``values()`` and ``items()`` functions do the same thing they do for lists, and there's an "iter" and "all" form for each of them.

.. code-block:: python

    >>> file.values()
    [<ROOTDirectory 'one' at 0x783af8f82d10>, <ROOTDirectory 'three' at 0x783af8cf6250>]
    >>> file.items()
    [('one;1', <ROOTDirectory 'one' at 0x783af8cf64d0>),
     ('three;1', <ROOTDirectory 'three' at 0x783af8cf6810>)]

In addition, `ROOTDirectory`_ has ``classes()``, ``iterclasses()`` and ``allclasses()`` to iterate over keys and class names of the contained objects. You can identify the class of an object before loading it.

.. code-block:: python

    >>> for n, x in file.allclasses():
    ...     print(repr(n), "\t", x)
    ... 
    'one;1'          <class 'uproot.rootio.ROOTDirectory'>
    'one/two;1'      <class 'uproot.rootio.ROOTDirectory'>
    'one/two/tree;1' <class 'uproot.rootio.TTree'>
    'one/tree;1'     <class 'uproot.rootio.TTree'>
    'three;1'        <class 'uproot.rootio.ROOTDirectory'>
    'three/tree;1'   <class 'uproot.rootio.TTree'>

As with a ``dict``, square brackets extract values by key. If you include ``"/"`` or ``";"`` in your request, you can specify subdirectories or cycle numbers (those ``;1`` at the end of key names, which you can usually ignore).

.. code-block:: python

    >>> file["one"]["two"]["tree"]
    <TTree 'tree' at 0x783af8f8aed0>

is equivalent to

.. code-block:: python

    >>> file["one/two/tree"]
    <TTree 'tree' at 0x783af8cf6490>

The memory management is explicit: each time you request a value from a `ROOTDirectory`_, it is deserialized from the file. This usually doesn't matter on the command-line, but it could in a loop.

`TTree`_ objects are also ``dict``-like objects, but this time the keys and values are the `TBranch`_ names and objects. If you're not familiar with ROOT terminology, "tree" means a dataset and "branch" means one column or attribute of that dataset. The `TTree`_ class also has ``keys()``, ``iterkeys()``, ``allkeys()``, ``values()``, ``items()``, etc., because `TBranch`_ instances may be nested.

To get an overview of what's available in the `TTree`_ and whether uproot can read it, call ``show()``.

.. code-block:: python

    >>> tree.show()
    Int32                      (no streamer)              asdtype('>i4')
    Int64                      (no streamer)              asdtype('>i8')
    UInt32                     (no streamer)              asdtype('>u4')
    UInt64                     (no streamer)              asdtype('>u8')
    Float32                    (no streamer)              asdtype('>f4')
    Float64                    (no streamer)              asdtype('>f8')
    Str                        (no streamer)              asstrings()
    ArrayInt32                 (no streamer)              asdtype('>i4', (10,))
    ArrayInt64                 (no streamer)              asdtype('>i8', (10,))
    ArrayUInt32                (no streamer)              asdtype('>u4', (10,))
    ArrayUInt64                (no streamer)              asdtype('>u8', (10,))
    ArrayFloat32               (no streamer)              asdtype('>f4', (10,))
    ArrayFloat64               (no streamer)              asdtype('>f8', (10,))
    N                          (no streamer)              asdtype('>i4')
    SliceInt32                 (no streamer)              asjagged(asdtype('>i4'))
    SliceInt64                 (no streamer)              asjagged(asdtype('>i8'))
    SliceUInt32                (no streamer)              asjagged(asdtype('>u4'))
    SliceUInt64                (no streamer)              asjagged(asdtype('>u8'))
    SliceFloat32               (no streamer)              asjagged(asdtype('>f4'))
    SliceFloat64               (no streamer)              asjagged(asdtype('>f8'))

The first column shows `TBranch`_ names, the "streamers" in the second column are ROOT schemas in the file used to reconstruct complex user classes. (This file doesn't have any.) The third column shows uproot's default interpretation of the data. If any `TBranch`_ objects have ``None`` as the default interpretation, it uproot cannot read it (but possibly will in the future, as more types are handled).

You can read each `TBranch`_ into an array by calling ``array()`` on the `TBranch`_

.. code-block:: python

    >>> tree["Float64"].array()
    array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10., 11., 12.,
           13., 14., 15., 16., 17., 18., 19., 20., 21., 22., 23., 24., 25.,
           26., 27., 28., 29., 30., 31., 32., 33., 34., 35., 36., 37., 38.,
           39., 40., 41., 42., 43., 44., 45., 46., 47., 48., 49., 50., 51.,
           52., 53., 54., 55., 56., 57., 58., 59., 60., 61., 62., 63., 64.,
           65., 66., 67., 68., 69., 70., 71., 72., 73., 74., 75., 76., 77.,
           78., 79., 80., 81., 82., 83., 84., 85., 86., 87., 88., 89., 90.,
           91., 92., 93., 94., 95., 96., 97., 98., 99.])
    >>> tree["Str"].array()
    strings(['evt-000' 'evt-001' 'evt-002' ... 'evt-097' 'evt-098' 'evt-099'])
    >>> tree["SliceInt32"].array()
    jaggedarray([[],
                 [1],
                 [2 2],
                 ...,
                 [97 97 97 ... 97 97 97],
                 [98 98 98 ... 98 98 98],
                 [99 99 99 ... 99 99 99]])

or read many at once with a single ``arrays([...])`` call on the `TTree`_.

.. code-block:: python

    >>> tree.arrays(["Int32", "Int64", "UInt32", "UInt64", "Float32", "Float64"])
    ...
    >>> tree.arrays()
    ...

Array-reading options
"""""""""""""""""""""

Remote files through XRootD
"""""""""""""""""""""""""""

Reading only part of a TBranch
""""""""""""""""""""""""""""""

Iterating over files (like TChain)
""""""""""""""""""""""""""""""""""

Non-flat TTrees: jagged arrays and more
"""""""""""""""""""""""""""""""""""""""

Non-TTrees: histograms and more
"""""""""""""""""""""""""""""""

Caching data
""""""""""""

Parallel processing
"""""""""""""""""""

Lazy arrays
"""""""""""

Connectors to other packages
""""""""""""""""""""""""""""



.. _ROOTDirectory: http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootdirectory
.. _TTree: http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods
.. _TBranch: http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods
