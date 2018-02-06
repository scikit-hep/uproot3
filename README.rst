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

- `Exploring a file`_
- `Array-reading parameters`_
- `Remote files through XRootD`_
- `Reading only part of a TBranch`_
- `Lazy arrays`_
- `Iterating over files (like TChain)`_
- `Non-flat TTrees: jagged arrays and more`_
- `Non-TTrees: histograms and more`_
- `Caching data`_
- `Parallel processing`_
- `Connectors to other packages`_

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

The `TTree`_ also has the attributes you expect from ROOT, presented with Pythonic conventions (``numentries`` follows an uproot convention, in which all "number of" methods start with "num"),

.. code-block:: python

    >>> tree.name, tree.title, tree.numentries
    ('tree', 'my tree title', 100)

as well as the raw data that was read from the file (C++ private members that start with "f").

.. code-block:: python

    >>> [x for x in dir(tree) if x.startswith("f")]
    ['fAliases', 'fAutoFlush', 'fAutoSave', 'fBranchRef', 'fBranches', 'fClusterRangeEnd',
     'fClusterSize', 'fDefaultEntryOffsetLen', 'fEntries', 'fEstimate', 'fFillColor',
     'fFillStyle', 'fFlushedBytes', 'fFriends', 'fIndex', 'fIndexValues', 'fLeaves',
     'fLineColor', 'fLineStyle', 'fLineWidth', 'fMarkerColor', 'fMarkerSize',
     'fMarkerStyle', 'fMaxEntries', 'fMaxEntryLoop', 'fMaxVirtualSize', 'fNClusterRange',
     'fName', 'fSavedBytes', 'fScanField', 'fTimerInterval', 'fTitle', 'fTotBytes',
     'fTreeIndex', 'fUpdate', 'fUserInfo', 'fWeight', 'fZipBytes', 'filter']

To get an overview of what arrays are available in the `TTree`_ and whether uproot can read it, call ``show()``.

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

The first column shows `TBranch`_ names, the "streamers" in the second column are ROOT schemas in the file used to reconstruct complex user classes. (This file doesn't have any.) The third column shows uproot's default interpretation of the data. If any `TBranch`_ objects have ``None`` as the default interpretation, uproot cannot read it (but possibly will in the future, as more types are handled).

You can read each `TBranch`_ into an array by calling ``array()`` on the `TBranch`_.

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

Array-reading parameters
""""""""""""""""""""""""

The complete list of array-reading parameters is given in the `TTree`_ reference (`e.g. this link <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot.tree.TTreeMethods.arrays>`_), but here's a guide to what you should know.

The **branches** parameter lets you specify which `TBranch`_ data to load and optionally, an interpretation other than the default.

- If it's ``None`` or unspecified, you'll get all arrays.
- If it's a single string, you'll get the only array you've named.
- If it's a list of strings, you'll get all the arrays you've named.
- If it's a ``dict`` from name to `Interpretation`_, you'll read the requested arrays in the specified ways.
- There's also a functional form that gives more control at the cost of more complexity.

An `Interpretation`_ lets you view the bytes of the ROOT file in different ways. Naturally, most of these are non-sensical:

.. code-block:: python

    # this array contains big-endian, 8-byte floating point numbers
    >>> tree.arrays("Float64")
    {'Float64': array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10., 11., 12.,
                        13., 14., 15., 16., 17., 18., 19., 20., 21., 22., 23., 24., 25.,
                        26., 27., 28., 29., 30., 31., 32., 33., 34., 35., 36., 37., 38.,
                        39., 40., 41., 42., 43., 44., 45., 46., 47., 48., 49., 50., 51.,
                        52., 53., 54., 55., 56., 57., 58., 59., 60., 61., 62., 63., 64.,
                        65., 66., 67., 68., 69., 70., 71., 72., 73., 74., 75., 76., 77.,
                        78., 79., 80., 81., 82., 83., 84., 85., 86., 87., 88., 89., 90.,
                        91., 92., 93., 94., 95., 96., 97., 98., 99.])}

    # but we could try reading them as little-endian, 4-byte integers (non-sensically)
    >>> tree.arrays({"Float32": uproot.interp.asdtype("<i4")})
    {'Float32': array([    0, 32831,    64, 16448, 32832, 41024, 49216, 57408,    65,
                        4161,  8257, 12353, 16449, 20545, 24641, 28737, 32833, 34881,
                       36929, 38977, 41025, 43073, 45121, 47169, 49217, 51265, 53313,
                       55361, 57409, 59457, 61505, 63553,    66,  1090,  2114,  3138,
                        4162,  5186,  6210,  7234,  8258,  9282, 10306, 11330, 12354,
                       13378, 14402, 15426, 16450, 17474, 18498, 19522, 20546, 21570,
                       22594, 23618, 24642, 25666, 26690, 27714, 28738, 29762, 30786,
                       31810, 32834, 33346, 33858, 34370, 34882, 35394, 35906, 36418,
                       36930, 37442, 37954, 38466, 38978, 39490, 40002, 40514, 41026,
                       41538, 42050, 42562, 43074, 43586, 44098, 44610, 45122, 45634,
                       46146, 46658, 47170, 47682, 48194, 48706, 49218, 49730, 50242,
                       50754], dtype=int32)}

Some reinterpretations are useful, though:

.. code-block:: python

    >>> tree.arrays({"Float64": uproot.interp.asdtype(">f8", todims=(5, 5))})
    {'Float64': array([[[ 0.,  1.,  2.,  3.,  4.],
                        [ 5.,  6.,  7.,  8.,  9.],
                        [10., 11., 12., 13., 14.],
                        [15., 16., 17., 18., 19.],
                        [20., 21., 22., 23., 24.]],

                       [[25., 26., 27., 28., 29.],
                        [30., 31., 32., 33., 34.],
                        [35., 36., 37., 38., 39.],
                        [40., 41., 42., 43., 44.],
                        [45., 46., 47., 48., 49.]],

                       [[50., 51., 52., 53., 54.],
                        [55., 56., 57., 58., 59.],
                        [60., 61., 62., 63., 64.],
                        [65., 66., 67., 68., 69.],
                        [70., 71., 72., 73., 74.]],

                       [[75., 76., 77., 78., 79.],
                        [80., 81., 82., 83., 84.],
                        [85., 86., 87., 88., 89.],
                        [90., 91., 92., 93., 94.],
                        [95., 96., 97., 98., 99.]]])}

In particular, replacing ``asdtype`` with ``asarray`` lets you instruct uproot to fill an existing array, so that you can manage your own memory:

.. code-block:: python

    >>> import numpy
    >>> myarray = numpy.zeros(200)   # allocate 200 zeros

    >>> tree.arrays({"Float64": uproot.interp.asarray(">f8", myarray)})
    {'Float64': array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10., 11., 12.,
                       13., 14., 15., 16., 17., 18., 19., 20., 21., 22., 23., 24., 25.,
                       26., 27., 28., 29., 30., 31., 32., 33., 34., 35., 36., 37., 38.,
                       39., 40., 41., 42., 43., 44., 45., 46., 47., 48., 49., 50., 51.,
                       52., 53., 54., 55., 56., 57., 58., 59., 60., 61., 62., 63., 64.,
                       65., 66., 67., 68., 69., 70., 71., 72., 73., 74., 75., 76., 77.,
                       78., 79., 80., 81., 82., 83., 84., 85., 86., 87., 88., 89., 90.,
                       91., 92., 93., 94., 95., 96., 97., 98., 99.])}
    >>> myarray
    array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10., 11., 12.,
           13., 14., 15., 16., 17., 18., 19., 20., 21., 22., 23., 24., 25.,
           26., 27., 28., 29., 30., 31., 32., 33., 34., 35., 36., 37., 38.,
           39., 40., 41., 42., 43., 44., 45., 46., 47., 48., 49., 50., 51.,
           52., 53., 54., 55., 56., 57., 58., 59., 60., 61., 62., 63., 64.,
           65., 66., 67., 68., 69., 70., 71., 72., 73., 74., 75., 76., 77.,
           78., 79., 80., 81., 82., 83., 84., 85., 86., 87., 88., 89., 90.,
           91., 92., 93., 94., 95., 96., 97., 98., 99.,  0.,  0.,  0.,  0.,
            0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
            0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
            0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
            0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
            0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
            0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
            0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
            0.,  0.,  0.,  0.,  0.])

The **outputtype** parameter lets you specify the container for your arrays. By default, you get a ``dict``, but that wouldn't be very useful in a ``for`` loop:

.. code-block:: python

    >>> for x, y, z in tree.iterate(["Float64", "Str", "ArrayInt32"]):
    ...     print(x, y, z)
    ... 
    ArrayInt32 Str Float64

A ``for`` loop over a ``dict`` just iterates over the names. We've read in three arrays, thrown away the arrays, and returned the names. In this case, we really wanted a tuple, which drops the names (normally needed for context), but preserves the order and unpacks into a given set of variables:

.. code-block:: python

    >>> for x, y, z in tree.iterate(["Float64", "Str", "ArrayInt32"], outputtype=tuple):
    ...     print(x, y, z)
    ...
    [ 0.  1.  2.  3.  4.  5.  6.  7.  8.  9. 10. 11. 12. 13. 14. 15. 16. 17.
     18. 19. 20. 21. 22. 23. 24. 25. 26. 27. 28. 29. 30. 31. 32. 33. 34. 35.
     36. 37. 38. 39. 40. 41. 42. 43. 44. 45. 46. 47. 48. 49. 50. 51. 52. 53.
     54. 55. 56. 57. 58. 59. 60. 61. 62. 63. 64. 65. 66. 67. 68. 69. 70. 71.
     72. 73. 74. 75. 76. 77. 78. 79. 80. 81. 82. 83. 84. 85. 86. 87. 88. 89.
     90. 91. 92. 93. 94. 95. 96. 97. 98. 99.]
    ['evt-000' 'evt-001' 'evt-002' ... 'evt-097' 'evt-098' 'evt-099']
    [[ 0  0  0  0  0  0  0  0  0  0]
     [ 1  1  1  1  1  1  1  1  1  1]
     [ 2  2  2  2  2  2  2  2  2  2]
     [ 3  3  3  3  3  3  3  3  3  3]

The **entrystart** and **entrystop** parameters let you slice an array while reading it, to avoid reading more than you want. See `Reading only part of a TBranch`_ below.

The **cache**, **basketcache**, and **keycache** parameters allow you to avoid re-reading data without significantly altering your code. See `Caching data`_ below.

The **executor** and **blocking** parameters allow you to read and possibly decompress the branches in parallel. See `Parallel processing`_ below.

All of the `TTree`_ and `TBranch`_ methods that read data into arrays— ``array``, ``lazyarray``, ``arrays``,  ``lazyarrays``, ``iterate``, ``basket``, ``baskets``, and ``iterate_baskets``— all use these parameters consistently. If you understand what they do for one method, you understand them all.

Remote files through XRootD
"""""""""""""""""""""""""""

XRootD is a remote file protocol that allows selective reading: if you only want a few arrays from a file that has hundreds, it can be much faster to leave the file on the server and read it through XRootD.

To use XRootD with uproot, you need to have an XRootD installation with its Python interface (ships with XRootD 4 and up). You may `install XRootD with conda <https://anaconda.org/nlesc/xrootd>`_ or `install XRootD from source <http://xrootd.org/dload.html>`_, but in the latter case, be sure to configure ``PYTHONPATH`` and ``LD_LIBRARY_PATH`` such that

.. code-block:: python

    >>> import pyxrootd

does not raise an ``ImportError`` exception.

Once XRootD is installed, you can open remote files in uproot by specifying the ``root://`` protocol:

.. code-block:: python

    >>> import uproot
    >>> file = uproot.open("root://eospublic.cern.ch//eos/opendata/atlas/OutreachDatasets/"
    ...                    "2016-07-29/MC/mc_117049.ttbar_had.root")
    >>> file.keys()
    ['mini;1']
    >>> tree = file["mini"]
    >>> tree.show()
    runNumber                  (no streamer)              asdtype('>i4')
    eventNumber                (no streamer)              asdtype('>i4')
    channelNumber              (no streamer)              asdtype('>i4')
    mcWeight                   (no streamer)              asdtype('>f4')
    pvxp_n                     (no streamer)              asdtype('>i4')
    vxp_z                      (no streamer)              asdtype('>f4')
    ...

Apart from possible network bandwidth issues, this `ROOTDirectory`_ and the objects it contains are indistinguishable from data from a local file.

Unlike a local file, however, remote files are buffered and cached by uproot. (The operating system buffers and caches local files!) For performance reasons, you may need to tune this buffering and caching: you do it through an **xrootdsource** parameter.

.. code-block:: python

    >>> file = uproot.open(..., xrootdsource=dict(chunkbytes=8*1024, limitbytes=1024**2))

- **chunkbytes** is the granularity (in bytes) of requests through XRootD (by default, it requests data in 8 kB chunks);
- **limitbytes** is the number of bytes that are held in memory before evicting and reusing memory (by default, it stores 1 MB of recently read XRootD data).

These defaults have not been tuned. You might find improvements in throughput by tweaking them.

Reading only part of a TBranch
""""""""""""""""""""""""""""""

ROOT files can be very large— it wouldn't be unusual to encounter a file that is too big to load entirely into memory. Even in these cases, you may be able to load individual arrays into memory, but maybe you don't want to. uproot lets you slice an array before you load it from the file.

Inside a ROOT file, `TBranch`_ data are split into chunks called baskets; each basket can be read and uncompressed independently of the others. Specifying a slice before reading, rather than loading a whole array and then slicing it, avoids reading baskets that aren't in the slice.

The `foriter.root <http://scikit-hep.org/uproot/examples/foriter.root>`_ file has very small baskets to demonstrate.

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/foriter.root

.. code-block:: python

    >>> import uproot
    >>> branch = uproot.open("foriter.root")["foriter"]["data"]
    >>> branch.numbaskets
    8
    >>> branch.baskets()
    [array([ 0,  1,  2,  3,  4,  5], dtype=int32),
     array([ 6,  7,  8,  9, 10, 11], dtype=int32),
     array([12, 13, 14, 15, 16, 17], dtype=int32),
     array([18, 19, 20, 21, 22, 23], dtype=int32),
     array([24, 25, 26, 27, 28, 29], dtype=int32),
     array([30, 31, 32, 33, 34, 35], dtype=int32),
     array([36, 37, 38, 39, 40, 41], dtype=int32),
     array([42, 43, 44, 45], dtype=int32)]

When we ask for the whole array, all eight of the baskets would be read, decompressed, and concatenated. Specifying **entrystart** and/or **entrystop** avoids unnecessary reading and decompression.

.. code-block:: python

    >>> branch.array(entrystart=5, entrystop=15)
    array([ 5,  6,  7,  8,  9, 10, 11, 12, 13, 14], dtype=int32)

We can demonstrate that this is actually happening with a cache (see `Caching data`_ below).

.. code-block:: python

    >>> basketcache = {}
    >>> branch.array(entrystart=5, entrystop=15, basketcache=basketcache)
    array([ 5,  6,  7,  8,  9, 10, 11, 12, 13, 14], dtype=int32)
    >>> basketcache
    {'foriter.root;foriter;data;0;raw':
         memmap([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 4, 0, 0, 0, 5],
                dtype=uint8),
     'foriter.root;foriter;data;1;raw':
         memmap([ 0,  0,  0,  6,  0,  0,  0,  7,  0,  0,  0,  8,  0,  0,  0,  9, 0,  0,  0,
                 10,  0,  0,  0, 11], dtype=uint8),
     'foriter.root;foriter;data;2;raw':
         memmap([ 0,  0,  0, 12,  0,  0,  0, 13,  0,  0,  0, 14,  0,  0,  0, 15, 0,  0,  0,
                 16,  0,  0,  0, 17], dtype=uint8)}

Only the first three baskets were touched by the above call (and hence, only those three were loaded into cache).

.. code-block:: python

    >>> branch.array(basketcache=basketcache)
    array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16,
           17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
           34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45], dtype=int32)
    >>> basketcache
    {'foriter.root;foriter;data;0;raw':
         memmap([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 4, 0, 0, 0, 5],
                dtype=uint8),
     'foriter.root;foriter;data;1;raw':
         memmap([ 0,  0,  0,  6,  0,  0,  0,  7,  0,  0,  0,  8,  0,  0,  0,  9, 0,  0,  0,
                 10,  0,  0,  0, 11], dtype=uint8),
     'foriter.root;foriter;data;2;raw':
         memmap([ 0,  0,  0, 12,  0,  0,  0, 13,  0,  0,  0, 14,  0,  0,  0, 15, 0,  0,  0,
                 16,  0,  0,  0, 17], dtype=uint8),
     'foriter.root;foriter;data;3;raw':
         memmap([ 0,  0,  0, 18,  0,  0,  0, 19,  0,  0,  0, 20,  0,  0,  0, 21, 0,  0,  0,
                 22,  0,  0,  0, 23], dtype=uint8),
     'foriter.root;foriter;data;4;raw':
         memmap([ 0,  0,  0, 24,  0,  0,  0, 25,  0,  0,  0, 26,  0,  0,  0, 27, 0,  0,  0,
                 28,  0,  0,  0, 29], dtype=uint8),
     'foriter.root;foriter;data;5;raw':
         memmap([ 0,  0,  0, 30,  0,  0,  0, 31,  0,  0,  0, 32,  0,  0,  0, 33, 0,  0,  0,
                 34,  0,  0,  0, 35], dtype=uint8),
     'foriter.root;foriter;data;6;raw':
         memmap([ 0,  0,  0, 36,  0,  0,  0, 37,  0,  0,  0, 38,  0,  0,  0, 39, 0,  0,  0,
                 40,  0,  0,  0, 41], dtype=uint8),
     'foriter.root;foriter;data;7;raw':
         memmap([ 0,  0,  0, 42,  0,  0,  0, 43,  0,  0,  0, 44,  0,  0,  0, 45],
                dtype=uint8)}

All of the baskets were touched by the above call (and hence, they are all loaded into cache).

Most often, the reason you'd want to slice an array before reading it is to efficiently iterate over data. `TTree`_ has an ``iterate`` method for that purpose (which, incidentally, also takes **entrystart** and **entrystop** parameters).

.. code-block:: python

    >>> tree = uproot.open("foriter.root")["foriter"]
    >>> for chunk in tree.iterate("data"):
    ...     print(chunk)
    ... 
    {'data': array([0, 1, 2, 3, 4, 5], dtype=int32)}
    {'data': array([ 6,  7,  8,  9, 10, 11], dtype=int32)}
    {'data': array([12, 13, 14, 15, 16, 17], dtype=int32)}
    {'data': array([18, 19, 20, 21, 22, 23], dtype=int32)}
    {'data': array([24, 25, 26, 27, 28, 29], dtype=int32)}
    {'data': array([30, 31, 32, 33, 34, 35], dtype=int32)}
    {'data': array([36, 37, 38, 39, 40, 41], dtype=int32)}
    {'data': array([42, 43, 44, 45], dtype=int32)}
    >>> for chunk in tree.iterate("data", entrysteps=5):
    ...     print(chunk)
    ... 
    {'data': array([0, 1, 2, 3, 4], dtype=int32)}
    {'data': array([5, 6, 7, 8, 9], dtype=int32)}
    {'data': array([10, 11, 12, 13, 14], dtype=int32)}
    {'data': array([15, 16, 17, 18, 19], dtype=int32)}
    {'data': array([20, 21, 22, 23, 24], dtype=int32)}
    {'data': array([25, 26, 27, 28, 29], dtype=int32)}
    {'data': array([30, 31, 32, 33, 34], dtype=int32)}
    {'data': array([35, 36, 37, 38, 39], dtype=int32)}
    {'data': array([40, 41, 42, 43, 44], dtype=int32)}
    {'data': array([45], dtype=int32)}

By default, the iteration step size is the minimum necessary to line up with basket boundaries, but you can specify an explicit **entrysteps** (fixed integer or iterable over start, stop pairs).
     
Lazy arrays
"""""""""""


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

Connectors to other packages
""""""""""""""""""""""""""""


.. _Exploring a file: #exploring-a-file
.. _Array-reading parameters: #array-reading-parameters
.. _Remote files through XRootD: #remote-files-through-xrootd
.. _Reading only part of a TBranch: #reading-only-part-of-a-tbranch
.. _Lazy arrays: #lazy-arrays
.. _Iterating over files (like TChain): #iterating-over-files-like-tchain
.. _Non-flat TTrees: jagged arrays and more: #non-flat-ttrees-jagged-arrays-and-more
.. _Non-TTrees: histograms and more: #non-ttrees-histograms-and-more
.. _Caching data: #caching-data
.. _Parallel processing: #parallel-processing
.. _Connectors to other packages: #connectors-to-other-packages

.. _ROOTDirectory: http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootdirectory
.. _TTree: http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods
.. _TBranch: http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods
.. _Interpretation: http://uproot.readthedocs.io/en/latest/interpretation.html
