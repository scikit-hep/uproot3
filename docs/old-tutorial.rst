Tutorial
========

**Table of contents:**

* `Getting started <#getting-started>`__
* `Exploring a file <#exploring-a-file>`__
* `Array-reading parameters <#array-reading-parameters>`__
* `Remote files through XRootD <#remote-files-through-xrootd>`__
* `Reading only part of a TBranch <#reading-only-part-of-a-tbranch>`__
* `Iterating over files (like TChain) <#iterating-over-files-like-tchain>`__
* `Non-flat TTrees\: jagged arrays and more <#non-flat-ttrees-jagged-arrays-and-more>`__
* `Non-TTrees\: histograms and more <#non-ttrees-histograms-and-more>`__
* `Caching data <#caching-data>`__
* `Parallel processing <#parallel-processing>`__
* `Connectors to other packages <#connectors-to-other-packages>`__

Getting started
---------------

Download a Z → μμ `flat ntuple <http://scikit-hep.org/uproot/examples/Zmumu.root>`__ and a H → ZZ → eeμμ `structured TTree <http://scikit-hep.org/uproot/examples/HZZ.root>`__.

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/Zmumu.root
    wget http://scikit-hep.org/uproot/examples/HZZ.root

Open each of the files; uproot presents them as ``dict``-like objects with ROOT names and objects as keys and values. (The "cycle number" after the semicolon can usually be ignored.)

.. code-block:: python

    >>> import uproot
    >>> uproot.open("Zmumu.root").keys()
    [b'events;1']
    >>> uproot.open("HZZ.root").keys()
    [b'events;1']

Since the file acts as a ``dict``, access the TTrees with square brackets. TTrees are also ``dict``-like objects, with branch names and branches as keys and values. (Hint: ``allkeys()`` lists branches recursively, if they're nested.)

.. code-block:: python

    >>> zmumu = uproot.open("Zmumu.root")["events"]
    >>> hzz = uproot.open("HZZ.root")["events"]
    >>> zmumu.keys()
    [b'Type', b'Run', b'Event', b'E1', b'px1', b'py1', b'pz1', b'pt1', b'eta1', b'phi1',
     b'Q1', b'E2', b'px2', b'py2', b'pz2', b'pt2', b'eta2', b'phi2', b'Q2', b'M']
    >>> hzz.keys()
    [b'NJet', b'Jet_Px', b'Jet_Py', b'Jet_Pz', b'Jet_E', b'Jet_btag', b'Jet_ID', b'NMuon',
     b'Muon_Px', b'Muon_Py', b'Muon_Pz', b'Muon_E', b'Muon_Charge', b'Muon_Iso', b'NElectron',
     b'Electron_Px', b'Electron_Py', b'Electron_Pz', b'Electron_E', b'Electron_Charge',
    ...

You can turn a chosen set of branches into Numpy arrays with the ``arrays`` method. Each array represents the values of a single attribute for all events, just as they're stored in a split ROOT file.

.. code-block:: python

    >>> zmumu.arrays(["px1", "py1", "pz1"])
    {b'px1': array([-41.19528764,  35.11804977, ..., 32.37749196,  32.48539387]),
     b'py1': array([ 17.4332439 , -16.57036233, ..., 1.19940578,   1.2013503 ]),
     b'pz1': array([-68.96496181, -48.77524654, ..., -74.53243061, -74.80837247])}

If the number of items per entry is not constant, such as the number of jets in an event, they can't be expressed as flat Numpy arrays. Instead, uproot loads them into `jagged arrays <https://en.wikipedia.org/wiki/Jagged_array>`__.

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

    >>> jaggedarray = hzz.array("Jet_E")
    >>> for jetenergies in jaggedarray:
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

Exploring a file
----------------

Download the `nesteddirs.root <http://scikit-hep.org/uproot/examples/nesteddirs.root>`__ sample and open it with uproot.

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/nesteddirs.root

.. code-block:: python

    >>> import uproot
    >>> file = uproot.open("nesteddirs.root")

This ``file`` is a `ROOTDirectory <http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootdirectory>`__, a class that can represent either a whole ROOT file or a TDirectory within that file. It emulates a Python ``dict``, so if you're familiar with this interface, you don't have to remember many method names. The "keys" are the names ROOT uses to find objects in files and the "values" are the data themselves.

.. code-block:: python

    >>> file.keys()                                      # get keys as a list
    [b'one;1', b'three;1']
    >>> file.iterkeys()                                  # iterate over keys
    <generator object iterkeys at 0x77209e67c0a0>
    >>> (x for x in file)                                # iterate over keys (just like a dict)
    <generator object <genexpr> at 0x7de7eca80320>
    >>> file.allkeys()                                   # get all keys recursively
    [b'one;1', b'one/two;1', b'one/two/tree;1', b'one/tree;1', b'three;1', b'three/tree;1']

If you only ask for the keys, the data won't be loaded (which can be important for performance!). The ``values()`` and ``items()`` functions do the same thing they do for lists, and there's an "iter" and "all" form for each of them.

.. code-block:: python

    >>> file.values()
    [<ROOTDirectory b'one' at 0x783af8f82d10>, <ROOTDirectory b'three' at 0x783af8cf6250>]
    >>> file.items()
    [(b'one;1', <ROOTDirectory b'one' at 0x783af8cf64d0>),
     (b'three;1', <ROOTDirectory b'three' at 0x783af8cf6810>)]

In addition, `ROOTDirectory <http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootdirectory>`__ has ``classes()``, ``iterclasses()`` and ``allclasses()`` to iterate over keys and class names of the contained objects. You can identify the class of an object before loading it.

.. code-block:: python

    >>> for n, x in file.allclasses():
    ...     print(repr(n), "\t", x)
    ...
    b'one;1'          <class 'uproot.rootio.ROOTDirectory'>
    b'one/two;1'      <class 'uproot.rootio.ROOTDirectory'>
    b'one/two/tree;1' <class 'uproot.rootio.TTree'>
    b'one/tree;1'     <class 'uproot.rootio.TTree'>
    b'three;1'        <class 'uproot.rootio.ROOTDirectory'>
    b'three/tree;1'   <class 'uproot.rootio.TTree'>

As with a ``dict``, square brackets extract values by key. If you include ``"/"`` or ``";"`` in your request, you can specify subdirectories or cycle numbers (those ``;1`` at the end of key names, which you can usually ignore).

.. code-block:: python

    >>> tree = file["one"]["two"]["tree"]
    >>> tree
    <TTree b'tree' at 0x783af8f8aed0>

is equivalent to

.. code-block:: python

    >>> file["one/two/tree"]
    <TTree b'tree' at 0x783af8cf6490>

The memory management is explicit: each time you request a value from a `ROOTDirectory <http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootdirectory>`__, it is deserialized from the file. This usually doesn't matter on the command-line, but it could in a loop.

`TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ objects are also ``dict``-like objects, but this time the keys and values are the `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ names and objects. If you're not familiar with ROOT terminology, "tree" means a dataset and "branch" means one column or attribute of that dataset. The `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ class also has ``keys()``, ``iterkeys()``, ``allkeys()``, ``values()``, ``items()``, etc., because `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ instances may be nested.

The `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ also has the attributes you expect from ROOT, presented with Pythonic conventions (``numentries`` follows an uproot convention, in which all "number of" methods start with "num"),

.. code-block:: python

    >>> tree.name, tree.title, tree.numentries
    (b'tree', b'my tree title', 100)

as well as the raw data that was read from the file (C++ private members that start with "f").

.. code-block:: python

    >>> [x for x in dir(tree) if x.startswith("_f")]
    ['_fAliases', '_fAutoFlush', '_fAutoSave', '_fBranchRef', '_fBranches', '_fClusterRangeEnd',
     '_fClusterSize', '_fDefaultEntryOffsetLen', '_fEntries', '_fEstimate', '_fFillColor',
     '_fFillStyle', '_fFlushedBytes', '_fFriends', '_fIndex', '_fIndexValues', '_fLeaves',
     '_fLineColor', '_fLineStyle', '_fLineWidth', '_fMarkerColor', '_fMarkerSize',
     '_fMarkerStyle', '_fMaxEntries', '_fMaxEntryLoop', '_fMaxVirtualSize', '_fNClusterRange',
     '_fName', '_fSavedBytes', '_fScanField', '_fTimerInterval', '_fTitle', '_fTotBytes',
     '_fTreeIndex', '_fUpdate', '_fUserInfo', '_fWeight', '_fZipBytes', '_filter']

To get an overview of what arrays are available in the `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ and whether uproot can read it, call ``show()``.

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

The first column shows `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ names, the "streamers" in the second column are ROOT schemas in the file used to reconstruct complex user classes. (This file doesn't have any.) The third column shows uproot's default interpretation of the data. If any `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ objects have ``None`` as the default interpretation, uproot cannot read it (but possibly will in the future, as more types are handled).

You can read each `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ into an array by calling ``array()`` on the `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__.

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

or read many at once with a single ``arrays([...])`` call on the `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__.

.. code-block:: python

    >>> tree.arrays(["Int32", "Int64", "UInt32", "UInt64", "Float32", "Float64"])
    ...
    >>> tree.arrays()
    ...

Array-reading parameters
------------------------

The complete list of array-reading parameters is given in the `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ reference (`e.g. this link <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot.tree.TTreeMethods.arrays>`__), but here's a guide to what you should know.

The **branches** parameter lets you specify which `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ data to load and optionally, an interpretation other than the default.

- If it's ``None`` or unspecified, you'll get all arrays.
- If it's a single string, you'll either get the array you've named or all the arrays that match a glob pattern (if it includes ``*``, ``?``, or ``[...]``) or full regular expression (if it starts and ends with slashes with optional flags ``/pattern/i``).
- If it's a list of strings, you'll get all the arrays you've named or specified by pattern-matching.
- If it's a ``dict`` from name to `Interpretation <http://uproot.readthedocs.io/en/latest/interpretation.html>`__, you'll read the requested arrays in the specified ways.
- There's also a functional form that gives more control at the cost of more complexity.

An `Interpretation <http://uproot.readthedocs.io/en/latest/interpretation.html>`__ lets you view the bytes of the ROOT file in different ways. Naturally, most of these are non-sensical:

.. code-block:: python

    # this array contains big-endian, 8-byte floating point numbers
    >>> tree.arrays("Float64")
    {b'Float64': array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10., 11., 12.,
                         13., 14., 15., 16., 17., 18., 19., 20., 21., 22., 23., 24., 25.,
                         26., 27., 28., 29., 30., 31., 32., 33., 34., 35., 36., 37., 38.,
                         39., 40., 41., 42., 43., 44., 45., 46., 47., 48., 49., 50., 51.,
                         52., 53., 54., 55., 56., 57., 58., 59., 60., 61., 62., 63., 64.,
                         65., 66., 67., 68., 69., 70., 71., 72., 73., 74., 75., 76., 77.,
                         78., 79., 80., 81., 82., 83., 84., 85., 86., 87., 88., 89., 90.,
                         91., 92., 93., 94., 95., 96., 97., 98., 99.])}

    # but we could try reading them as little-endian, 4-byte integers (non-sensically)
    >>> tree.arrays({"Float32": uproot.asdtype("<i4")})
    {b'Float32': array([    0, 32831,    64, 16448, 32832, 41024, 49216, 57408,    65,
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

    >>> import numpy
    >>> tree.arrays({"Float64": uproot.asdtype(numpy.dtype((">f8", (5, 5))))})
    {b'Float64': array([[[ 0.,  1.,  2.,  3.,  4.],
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

    >>> tree.arrays({"Float64": uproot.asarray(">f8", myarray)})
    {b'Float64': array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10., 11., 12.,
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

The **entrystart** and **entrystop** parameters let you slice an array while reading it, to avoid reading more than you want. See `Reading only part of a TBranch <#reading-only-part-of-a-tbranch>`__ below.

The **cache**, **basketcache**, and **keycache** parameters allow you to avoid re-reading data without significantly altering your code. See `Caching data <#caching-data>`__ below.

The **executor** and **blocking** parameters allow you to read and possibly decompress the branches in parallel. See `Parallel processing <#parallel-processing>`__ below.

All of the `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ and `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ methods that read data into arrays— ``array``, ``lazyarray``, ``arrays``,  ``lazyarrays``, ``iterate``, ``basket``, ``baskets``, and ``iterate_baskets``— all use these parameters consistently. If you understand what they do for one method, you understand them all.

Remote files through XRootD
---------------------------

XRootD is a remote file protocol that allows selective reading: if you only want a few arrays from a file that has hundreds, it can be much faster to leave the file on the server and read it through XRootD.

To use XRootD with uproot, you need to have an XRootD installation with its Python interface (ships with XRootD 4 and up). You may `install XRootD with conda <https://anaconda.org/nlesc/xrootd>`__ or `install XRootD from source <http://xrootd.org/dload.html>`__, but in the latter case, be sure to configure ``PYTHONPATH`` and ``LD_LIBRARY_PATH`` such that

.. code-block:: python

    >>> import pyxrootd

does not raise an ``ImportError`` exception.

Once XRootD is installed, you can open remote files in uproot by specifying the ``root://`` protocol:

.. code-block:: python

    >>> import uproot
    >>> file = uproot.open("root://eospublic.cern.ch//eos/opendata/atlas/OutreachDatasets/"
    ...                    "2016-07-29/MC/mc_117049.ttbar_had.root")
    >>> file.keys()
    [b'mini;1']
    >>> tree = file["mini"]
    >>> tree.show()
    runNumber                  (no streamer)              asdtype('>i4')
    eventNumber                (no streamer)              asdtype('>i4')
    channelNumber              (no streamer)              asdtype('>i4')
    mcWeight                   (no streamer)              asdtype('>f4')
    pvxp_n                     (no streamer)              asdtype('>i4')
    vxp_z                      (no streamer)              asdtype('>f4')
    ...

Apart from possible network bandwidth issues, this `ROOTDirectory <http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootdirectory>`__ and the objects it contains are indistinguishable from data from a local file.

Unlike a local file, however, remote files are buffered and cached by uproot. (The operating system buffers and caches local files!) For performance reasons, you may need to tune this buffering and caching: you do it through an **xrootdsource** parameter.

.. code-block:: python

    >>> file = uproot.open(..., xrootdsource=dict(chunkbytes=8*1024, limitbytes=1024**2))

- **chunkbytes** is the granularity (in bytes) of requests through XRootD (by default, it requests data in 8 kB chunks);
- **limitbytes** is the number of bytes that are held in memory before evicting and reusing memory (by default, it stores 1 MB of recently read XRootD data).

These defaults have not been tuned. You might find improvements in throughput by tweaking them.

Reading only part of a TBranch
------------------------------

ROOT files can be very large— it wouldn't be unusual to encounter a file that is too big to load entirely into memory. Even in these cases, you may be able to load individual arrays into memory, but maybe you don't want to. uproot lets you slice an array before you load it from the file.

Inside a ROOT file, `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ data are split into chunks called baskets; each basket can be read and uncompressed independently of the others. Specifying a slice before reading, rather than loading a whole array and then slicing it, avoids reading baskets that aren't in the slice.

The `foriter.root <http://scikit-hep.org/uproot/examples/foriter.root>`__ file has very small baskets to demonstrate.

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

We can demonstrate that this is actually happening with a cache (see `Caching data <#caching-data>`__ below).

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
         memmap([ 0,  0,  0, 42,  0,  0,  0, 43,  0,  0,  0, 44,  0,  0,  0, 45], dtype=uint8)}

All of the baskets were touched by the above call (and hence, they are all loaded into cache).

One reason you might want to only part of an array is to get a sense of the data without reading all of it. This can be a particularly useful way to examine a remote file over XRootD with a slow network connection. While you could do this by specifying a small **entrystop**, uproot has a lazy array interface to make this more convenient.

.. code-block:: python

    >>> basketcache = {}
    >>> myarray = branch.lazyarray(basketcache=basketcache)
    >>> myarray
    <uproot.tree._LazyArray object at 0x71eb8661f9d0>
    >>> len(basketcache)
    0
    >>> myarray[5]
    5
    >>> len(basketcache)
    1
    >>> myarray[5:15]
    array([ 5,  6,  7,  8,  9, 10, 11, 12, 13, 14], dtype=int32)
    >>> len(basketcache)
    3
    >>> myarray[:]
    array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16,
           17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
           34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45], dtype=int32)
    >>> len(basketcache)
    8

Whenever a lazy array is indexed or sliced, it loads as little as possible to yield the result. Slicing everything (``[:]``) gives you a normal array.

Since caching in uproot is always explicit (for consistency: see `Caching data <#caching-data>`__), repeatedly indexing the same value repeatedly reads from the file unless you specify a cache. You'd probably always want to provide lazy arrays with caches.

Another reason to want to read part of an array is to efficiently iterate over data. `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ has an ``iterate`` method for that purpose (which, incidentally, also takes **entrystart** and **entrystop** parameters).

.. code-block:: python

    >>> tree = uproot.open("foriter.root")["foriter"]
    >>> for chunk in tree.iterate("data"):
    ...     print(chunk)
    ...
    {b'data': array([0, 1, 2, 3, 4, 5], dtype=int32)}
    {b'data': array([ 6,  7,  8,  9, 10, 11], dtype=int32)}
    {b'data': array([12, 13, 14, 15, 16, 17], dtype=int32)}
    {b'data': array([18, 19, 20, 21, 22, 23], dtype=int32)}
    {b'data': array([24, 25, 26, 27, 28, 29], dtype=int32)}
    {b'data': array([30, 31, 32, 33, 34, 35], dtype=int32)}
    {b'data': array([36, 37, 38, 39, 40, 41], dtype=int32)}
    {b'data': array([42, 43, 44, 45], dtype=int32)}
    >>> for chunk in tree.iterate("data", entrysteps=5):
    ...     print(chunk)
    ...
    {b'data': array([0, 1, 2, 3, 4], dtype=int32)}
    {b'data': array([5, 6, 7, 8, 9], dtype=int32)}
    {b'data': array([10, 11, 12, 13, 14], dtype=int32)}
    {b'data': array([15, 16, 17, 18, 19], dtype=int32)}
    {b'data': array([20, 21, 22, 23, 24], dtype=int32)}
    {b'data': array([25, 26, 27, 28, 29], dtype=int32)}
    {b'data': array([30, 31, 32, 33, 34], dtype=int32)}
    {b'data': array([35, 36, 37, 38, 39], dtype=int32)}
    {b'data': array([40, 41, 42, 43, 44], dtype=int32)}
    {b'data': array([45], dtype=int32)}

By default, the iteration step size is the minimum necessary to line up with basket boundaries, but you can specify an explicit **entrysteps** (fixed integer or iterable over start, stop pairs).

Iterating over files (like TChain)
----------------------------------

If one file doesn't fit in memory, a collection of them won't, so we need to iterate over a collection of files just as we iterate over one file. The interface for this is similar to the `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ ``iterate`` method:

.. code-block:: python

    >>> for arrays in uproot.iterate("/set/of/files*.root", "events",
    ...         ["branch1", "branch2", "branch3"],entrysteps=10000):
    ...     do_something_with(arrays)

The **branches** parameter is the same (usually, a list of `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__ names will do), as is **entrysteps**, **outputtype**, caching, and parallel processing parameters. Since this form must iterate over a collection of files, it also takes a **path** (string with wildcards or a list of strings) and a **treepath** (location of the `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ within each file; must be the same), as well as **xrootdsource** options, if relevant.

Non-flat TTrees\: jagged arrays and more
----------------------------------------

We have already seen non-scalar structure in the `H → ZZ → eeμμ sample <http://scikit-hep.org/uproot/examples/HZZ.root>`__.

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/HZZ.root

.. code-block:: python

    >>> import uproot
    >>> tree = uproot.open("HZZ.root")["events"]
    >>> tree.arrays(["Muon_Px", "Muon_Py", "Muon_Pz"])
    {b'Muon_Pz':
        jaggedarray([[ -8.160793 -11.307582],
                     [20.199968],
                     [11.168285 36.96519 ],
                     ...,
                     [-52.66375],
                     [162.17632],
                     [54.719437]]),
     b'Muon_Py':
        jaggedarray([[-11.654672    0.6934736],
                     [-24.404259],
                     [-21.723139  29.800508],
                     ...,
                     [-15.303859],
                     [63.60957],
                     [-35.665077]]),
     b'Muon_Px':
        jaggedarray([[-52.899456  37.73778 ],
                     [-0.81645936],
                     [48.98783    0.8275667],
                     ...,
                     [-29.756786],
                     [1.1418698],
                     [23.913206]])}

Jagged arrays are presented as Python objects with an array-like syntax (square brackets), but the subarrays that you get from each entry can have a different length. You can use this in straightforward Python code (double nested ``for`` loop).

.. code-block:: python

    >>> px, py, pz = tree.arrays(["Muon_Px", "Muon_Py", "Muon_Pz"], outputtype=tuple)
    >>> import math
    >>> p = []
    >>> for pxi, pyi, pzi in zip(px, py, pz):
    ...     p.append([])
    ...     for pxj, pyj, pzj in zip(pxi, pyi, pzi):
    ...         p[-1].append(math.sqrt(pxj**2 + pyj**2 + pzj**2))
    >>> p[:10]
    [[54.77939728331514, 39.40155413769603],
     [31.690269339405322],
     [54.73968355087043, 47.48874088422057],
     [413.46002426963094, 344.0415120421566],
     [120.86427107457735, 51.28450356111275],
     [44.093180987524, 52.881414889639125],
     [132.11798977251323, 39.83906179940468],
     [160.19447580091284],
     [112.09960289042792, 21.37544434752662],
     [101.37877704093872, 70.2069335164593]]

But you can also take advantage of the fact that `JaggedArray <http://uproot.readthedocs.io/en/latest/interpretation.html#uproot-interp-jagged-jaggedarray>`__ is backed by Numpy arrays to perform structure-preserving operations much more quickly. The following does the same thing as the above, but using only Numpy calls.

.. code-block:: python

    >>> p = numpy.sqrt(px**2 + py**2 + pz**2)
    >>> p[:10]
    jaggedarray([[54.7794   39.401554],
                 [31.69027],
                 [54.739685 47.48874 ],
                 [413.46005 344.0415 ],
                 [120.86427  51.2845 ],
                 [44.09318  52.881416],
                 [132.11798  39.83906],
                 [160.19447],
                 [112.09961   21.375444],
                 [101.37878  70.20693]])

In the first code block, we used the Python interpreter and ``math`` library to compute momentum magnitudes, one for each muon, maintaining the event structure (one or two muons per event). In the second code block, we used Numpy to compute all the momentum magnitudes in one call (the loop is performed in compiled code) and packaged the result in a new `JaggedArray <http://uproot.readthedocs.io/en/latest/interpretation.html#uproot-interp-jagged-jaggedarray>`__. Since we want the same structure as the original ``px``, we can reuse its ``starts`` and ``stops``.

`JaggedArray <http://uproot.readthedocs.io/en/latest/interpretation.html#uproot-interp-jagged-jaggedarray>`__ is a single Python type used to describe any list of lists of numbers from ROOT. In C++, it may be a branch with another branch as a counter (e.g. ``Muon_pt[nMuons]``), a ``std::vector<number>``, a numeric field from an exploded ``TClonesArray`` of class instances, etc. Jagged arrays are also the simplest kind of variable-sized object that can be found in a `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__. More complex objects are deserialized into `JaggedArray <http://uproot.readthedocs.io/en/latest/interpretation.html#uproot-interp-jagged-jaggedarray>`__ wrapped in classes that present them differently, for instance

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/Zmumu.root

.. code-block:: python

    >>> import uproot
    >>> tree = uproot.open("Zmumu.root")["events"]
    >>> tree.array("Type")
    strings([b'GT' b'TT' b'GT' ... b'TT' b'GT' b'GG'])

The `Strings <http://uproot.readthedocs.io/en/latest/interpretation.html#uproot-interp-strings-strings>`__ type represents a collection of strings, not as (memory-hogging) Python ``bytes``, but as a `JaggedArray <http://uproot.readthedocs.io/en/latest/interpretation.html#uproot-interp-jagged-jaggedarray>`__ wrapper:

.. code-block:: python

    >>> strings = tree.array("Type")
    >>> strings.content
    <JaggedArray [[71 84] [84 84] [71 84] ... [84 84] [71 84] [71 71]] at 7f4020f2f358>
    >>> strings.content.starts
    array([   0,    2,    4, ..., 4602, 4604, 4606])
    >>> strings.content.stops
    array([   2,    4,    6, ..., 4604, 4606, 4608])

The "numeric" content is actually the ASCII representation of all the string data:

    >>> strings.content.content.tostring()
    b'GTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTG
      GGTTTGTTTTTGTGTGGGTTTGTGGGTTTGTTTTTGTGTTTTTTTGTGTTTTTTTTTGTGTTTTTTTTTTTGTGTGGGTTTGTGGGT
      TTGTTTTTGTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGG
      TTTGTTTTTGTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGGGTTTGTGG
     ...

The role of the `Strings <http://uproot.readthedocs.io/en/latest/interpretation.html#uproot-interp-strings-strings>`__ wrapper is to yield each item as a Python ``bytes`` on demand.

.. code-block:: python

    >>> strings[5]
    b'TT'
    >>> isinstance(strings[5], bytes)
    True
    >>> strings[5:10]
    strings([b'TT' b'GT' b'GG' b'GT' b'TT'])
    >>> strings[5:10].tolist()
    [b'TT', b'GT', b'GG', b'GT', b'TT']

Again, it doesn't matter whether the strings were ``char*``, ``std::string``, or ``TString``, etc. in C++. They all translate into `Strings <http://uproot.readthedocs.io/en/latest/interpretation.html#uproot-interp-strings-strings>`__.

At the time of this writing, ``std::vector<std::string>`` and ``std::vector<std::vector<numbers>>`` are also implemented this way. Eventually, uproot should be able to read any type, translating C++ classes into Python ``namedtuples``, filled on demand.

Non-TTrees\: histograms and more
--------------------------------

The uproot implementation is fairly general, to be robust against changes in the ROOT format. ROOT has a wonderful backward-compatibility mechanism called "streamers," which specify how bytes translate into data fields for every type of object contained in the file. Even such basic types as ``TObjArray`` and ``TNamed`` are defined by streamers.

To read a `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__, uproot first consults the streamers in your ROOT file to know how to deserialize your particular version of that class. This is why it contains so many members starting with ``"_f"``: they are the C++ class private members, and uproot is literally following the prescription to deserialize the C++ class. Pythonic attributes like ``tree.name`` and ``tree.numentries`` are aliases for ``tree._fName`` and ``tree._fEntries``, etc.

This means that literally any kind of object may be read from a `ROOTDirectory <http://uproot.readthedocs.io/en/latest/root-io.html#uproot-rootio-rootdirectory>`__. Even if the uproot authors have never heard of it, the new data type will have a streamer in the file, and uproot will follow that prescription to make an object with the appropriate private fields. What you do with that object is another story: the member functions, written in C++, are *not* serialized into the ROOT file, and thus the Python object will have data but no functionality.

We have to add functionality by writing the equivalent Python. The uproot `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__ implementation is a bundle of functions that expect private members like ``_fName``, ``_fEntries``, and ``_fBranches``. Other ROOT types can be wrapped in similar ways. Histograms are useful, and therefore the ``TH1`` classes are similarly wrapped:

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/histograms.root

.. code-block:: python

    >>> import uproot
    >>> file = uproot.open("histograms.root")
    >>> file.allkeys()
    [b'one;1', b'two;1', b'three;1']
    >>> file["one"].show()

.. code-block:: none

                      0                                                       2410.8
                      +------------------------------------------------------------+
    [-inf, -3)   0    |                                                            |
    [-3, -2.4)   68   |**                                                          |
    [-2.4, -1.8) 285  |*******                                                     |
    [-1.8, -1.2) 755  |*******************                                         |
    [-1.2, -0.6) 1580 |***************************************                     |
    [-0.6, 0)    2296 |*********************************************************   |
    [0, 0.6)     2286 |*********************************************************   |
    [0.6, 1.2)   1570 |***************************************                     |
    [1.2, 1.8)   795  |********************                                        |
    [1.8, 2.4)   289  |*******                                                     |
    [2.4, 3)     76   |**                                                          |
    [3, inf]     0    |                                                            |
                      +------------------------------------------------------------+

Code to view histograms in Pythonic plotting packages is in development, but this is a wide-open area for the future. For now, uproot's ability to read histograms is useful for querying bin values in scripts, like so.

.. code-block:: python

    >>> h = file["one"]
    >>> h.edges      # returns a numpy array of bin edges, excluding under/overflow bins
    array([-3. , -2.4, -1.8, -1.2, -0.6,  0. ,  0.6,  1.2,  1.8,  2.4,  3. ])
    >>> h.values     # returns counter values, excluding *flow bins
    array([  68.,  285.,  755., 1580., 2296., 2286., 1570.,  795.,  289., 76.], dtype=float32)
    >>> h.variances  # returns counter variances for weighted histograms (*flow bins excluded)
    array([], dtype=float64)

There are corresponding fields ``alledges``, ``allvalues``, and ``allvariances``, which include the under/overflow bins.

Caching data
------------

Following Python's preference for explicit operations over implicit ones, uproot does not cache any data by default. If you say ``file["tree"]`` twice or ``tree["branch"].array()`` twice, uproot will go back to the file each time to extract the contents. It will not hold previously loaded objects or arrays in memory in case you want them again. You can keep them in memory yourself by assigning them to a variable; the price of having to be explicit is well worth not having to reverse engineer a memory-hogging cache.

Sometimes, however, changing your code to assign new variable names (or ``dict`` entries) for every array you want to keep in memory can be time-consuming or obscure an otherwise simple analysis script. It would be nice to just turn on caching. For this purpose, all array-extracting methods have **cache**, **basketcache**, and **keycache** parameters that accpet any ``dict``-like object as a cache.

If you have a loop like

.. code-block:: python

    >>> for q1, q2 in tree.iterate(["Q1", "Q2"], outputtype=tuple):
    ...     do_something(q1, q2)

and you don't want it to return to the file the second time you run it, you can change it to

    >>> cache = {}
    >>> for q1, q2 in tree.iterate(["Q1", "Q2"], outputtype=tuple, cache=cache):
    ...     do_something(q1, q2)

The array methods will always check the cache first, and if it's empty, get the arrays the normal way and fill the cache. Since this cache was a simple ``dict``, we can see what's in it.

    >>> cache
    {'AAGUS3fQmKsR56dpAQAAf77v;events;Q1;asdtype(Bi4,Li4,(),());0-2304':
         array([ 1, -1, -1, ...,  1,  1,  1], dtype=int32),
     'AAGUS3fQmKsR56dpAQAAf77v;events;Q2;asdtype(Bi4,Li4,(),());0-2304':
         array([-1,  1,  1, ..., -1, -1, -1], dtype=int32)}

Key names are long because they encode a unique identifier to the file, the path to the `TTree <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`__, to the `TBranch <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`__, the `Interpretation <http://uproot.readthedocs.io/en/latest/interpretation.html>`__, and the entry range, so that we don't confuse one cached array for another.

Python ``dict`` objects will keep the arrays as long as the process lives (or they're manually deleted, or the ``dict`` goes out of scope). Sometimes this is too long. Real caches typically have a Least Recently Used (LRU) eviction policy: they're capped at a given size and when adding a new array would exceed that size, they delete the ones that were least recently accessed. `ArrayCache <http://uproot.readthedocs.io/en/latest/caches.html#uproot-cache-arraycache>`__ implements such a policy.

.. code-block:: python

    >>> cache = uproot.cache.ArrayCache(8*1024**3)    # 8 GB (typical)
    >>> import numpy
    >>> cache["one"] = numpy.zeros(2*1024**3, dtype=numpy.uint8)   # 2 GB
    >>> list(cache)
    ['one']
    >>> cache["two"] = numpy.zeros(2*1024**3, dtype=numpy.uint8)   # 2 GB
    >>> list(cache)
    ['one', 'two']
    >>> cache["three"] = numpy.zeros(2*1024**3, dtype=numpy.uint8) # 2 GB
    >>> list(cache)
    ['one', 'two', 'three']
    >>> cache["four"] = numpy.zeros(2*1024**3, dtype=numpy.uint8)  # 2 GB
    >>> list(cache)
    ['two', 'three', 'four']
    >>> cache["five"] = numpy.zeros(2*1024**3, dtype=numpy.uint8)  # 2 GB causes eviction
    >>> list(cache)
    ['three', 'four', 'five']

Thus, you can pass a `ArrayCache <http://uproot.readthedocs.io/en/latest/caches.html#uproot-cache-arraycache>`__ as the **cache** argument to get caching with an LRU (least recently used) policy. If you need it, there's also a `ThreadSafeArrayCache <http://uproot.readthedocs.io/en/latest/caches.html#uproot-cache-threadsafearraycache>`__ for parallel processing, and the ``method="LFU"`` parameter to both lets you pick an LFU (least frequently used) policy.

Finally, you may be wondering why the array methods have three cache parameters: **cache**, **basketcache**, and **keycache**. Here's what they mean.

- **cache:** applies to fully constructed arrays. Thus, if you request the same branch with a different **entrystart**, **entrystop**, or `Interpretation <http://uproot.readthedocs.io/en/latest/interpretation.html>`__ (e.g. ``dtype`` or ``dims``), it counts as a new array and *competes* with arrays already in the cache, rather than drawing on them. Pass a **cache** argument if you're extracting whole arrays or iterating with fixed **entrysteps**.
- **basketcache:** applies to raw (but decompressed) basket data. This data can be re-sliced and re-interpreted many ways, and uproot finds what it needs in the cache. It's particularly useful for lazy arrays, which are frequently re-sliced.
- **keycache:** applies to ROOT ``TKey`` objects, used to look up baskets. With a full **basketcache** and a **keycache**, uproot never needs to access the file. The reason **keycache** is separate from **basketcache** is because ``TKey`` objects are much smaller than most arrays and should have a different eviction priority than an array: use a cache with LRU for **basketcache** and a simple ``dict`` for **keycache**.

Normally, you'd *either* set only **cache** *or* both **basketcache** and **keycache**. You can use the same ``dict``-like object for many applications (single pool) or different caches for different applications (to keep the priority queues distinct).

As we have seen, uproot's XRootD handler has an even lower-level cache for bytes read over the network. This is implemented as a `ThreadSafeArrayCache <http://uproot.readthedocs.io/en/latest/caches.html#uproot-cache-threadsafearraycache>`__. Local files are usually read as memory-mapped files, in which case the operating system does the low-level caching with the same mechanism as virtual memory. (For more control, you can `uproot.open <http://uproot.readthedocs.io/en/latest/opening-files.html#uproot-open>`__ a file with ``localsource=dict(chunkbytes=8*1024, limitbytes=1024**2)`` to use a regular file handle and custom paging/cache size.)

Parallel processing
-------------------

Just as caching must be explicit in uproot, parallel processing must be explicit as well. By default, every read, decompression, and array construction is single-threaded. To enable parallel processing, pass in a Python 3 executor.

To use executors in Python 2, install the backport.

.. code-block:: bash

    pip install futures --user

An executor is a group of pre-allocated threads that are all waiting for work. Create them with

.. code-block:: python

    >>> import concurrent.futures
    >>> executor = concurrent.futures.ThreadPoolExecutor(32)   # 32 threads

where the number of threads can be several times the number of CPUs on your machine.

.. code-block:: python

    >>> import multiprocessing
    >>> multiprocessing.cpu_count()
    8

These threads are being used for I/O, which is usually limited by hardware other than the CPU. (If you observe 100% CPU usage for a long time, you may be limited by CPU time spent decompressing, so reduce the number of threads. If you observe mostly idle CPUs, however, then you are limited by disk or network reading: increase the number of threads until the CPUs are busy.)

Most array-reading methods have an **executor** parameter, into which you can pass this thread pool.

.. code-block:: python

    >>> import uproot
    >>> branch = uproot.open("foriter.root")["foriter"]["data"]
    >>> branch.array(executor=executor)
    array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16,
           17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
           34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45], dtype=int32)

The only difference that might be visible to the user is performance. With an executor, each basket is read, decompressed, and copied to the output array in a separate task, and these tasks are handed to the executor for scheduling. A ``ThreadPoolExecutor`` fills all of the available workers and pushes more work on whenever a task finishes. The tasks must share memory (cannot be a ``ProcessPoolExecutor``) because they all write to (different parts of) the same output array.

If you're familiar with Python's Global Interpreter Lock (GIL), you might be wondering how parallel processing could help a single-process Python program. In uproot, at least, all of the operations that scale with the number of events— reading, decompressing, and the array copy— are performed in operating system calls (reading), compiled compression libraries that release the GIL, and Numpy, which also releases the GIL.

Since the baskets are being read in parallel, you may want to read them in the background, freeing up the main thread to do other things (such as submit even more work!). If you set ``blocking=False``, the array methods return a zero-argument function instead of an array, ``dict`` of arrays, or whatever. When you want to wait for the result, evaluate this function.

.. code-block:: python

    >>> arrays = branch.array(executor=executor, blocking=False)
    >>> arrays
    <function TBranchMethods.array.<locals>.wait at 0x783465575950>
    >>> arrays()
    array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16,
           17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
           34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45], dtype=int32)

The ``blocking=False`` setting can be used without an executor (without parallel processing), but it doesn't make much sense to do that.

Connectors to other packages
----------------------------

As a connector between ROOT and the scientific Python world, uproot has a growing set of extensions to ease these transitions. For instance, to get a Pandas DataFrame, call `tree.pandas.df <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot._connect.to_pandas.TTreeMethods_pandas.df>`__:

.. code-block:: python

    >>> import uproot
    >>> tree = uproot.open("Zmumu.root")["events"]
    >>> tree.pandas.df(["pt1", "eta1", "phi1", "pt2", "eta2", "phi2"])
              eta1      eta2      phi1      phi2      pt1      pt2
    0    -1.217690 -1.051390  2.741260 -0.440873  44.7322  38.8311
    1    -1.051390 -1.217690 -0.440873  2.741260  38.8311  44.7322
    2    -1.051390 -1.217690 -0.440873  2.741260  38.8311  44.7322
    3    -1.051390 -1.217690 -0.440873  2.741260  38.8311  44.7322
    ...        ...       ...       ...       ...      ...      ...
    2300 -1.482700 -1.570440 -2.775240  0.037027  72.8781  32.3997
    2301 -1.570440 -1.482700  0.037027 -2.775240  32.3997  72.8781
    2302 -1.570440 -1.482700  0.037027 -2.775240  32.3997  72.8781
    2303 -1.570440 -1.482700  0.037027 -2.775240  32.3997  72.8781

    [2304 rows x 6 columns]

This method takes the same **branches**, **entrystart**, **entrystop**, **cache**, **basketcache**, **keycache**, and **executor** methods as all the other array methods.

Note that ``pandas.DataFrame`` is also a recognized option for all **outputtype** parameters, so you can, for instance, iterate through DataFrames with ``uproot.iterate("files*.root", "treename", outputtype=pandas.DataFrame)``.

