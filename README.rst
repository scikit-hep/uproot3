.. inclusion-marker-1-do-not-remove

uproot
======

.. image:: https://travis-ci.org/scikit-hep/uproot.svg?branch=master
   :target: https://travis-ci.org/scikit-hep/uproot

ROOT I/O in pure Python and Numpy.

uproot (originally μproot, for "micro-Python ROOT") is a reader and (someday) a writer of the `ROOT file format <https://root.cern/>`_ using only Python and Numpy. Unlike the standard C++ ROOT implementation, uproot is only an I/O library, primarily intended to stream data into machine learning libraries in Python.

It is important to note that uproot is *not* maintained by the ROOT project team, so post bug reports as `uproot GitHub issues <https://github.com/scikit-hep/uproot/issues>`_, not on any ROOT forum.

.. inclusion-marker-2-do-not-remove

Installation
------------

Install OAMap like any other Python package:

.. code-block:: bash

    pip install uproot --user

or similar (use ``sudo``, ``virtualenv``, or ``conda`` if you wish).

**Strict dependencies:**

- `Python <http://docs.python-guide.org/en/latest/starting/installation/>`_ (2.6+, 3.4+)
- `Numpy <https://scipy.org/install.html>`_

**Recommended dependencies:**

- `lz4 <https://anaconda.org/anaconda/lz4>`_ compression used by some ROOT files
- `lzma <https://anaconda.org/anaconda/lzma>`_ compression used by some ROOT files; this is part of the Python 3 standard library, so only install for Python 2

**Optional dependencies:** (all are bindings to binaries that can be package-installed)

- `Numba and LLVM <http://numba.pydata.org/numba-doc/latest/user/installing.html>`_ to JIT-compile functions (requires a particular version of LLVM, follow instructions)
- `python-futures <https://pypi.python.org/pypi/futures>`_ for parallel processing; this is part of the Python 3 standard library, so only install for Python 2

*Reminder: you do not need C++ ROOT to run uproot.*

.. inclusion-marker-3-do-not-remove

Getting started
---------------

Download a `Z → μμ flat ntuple <http://scikit-hep.org/uproot/examples/Zmumu.root>`_ and a `H → ZZ → μμμμ <http://scikit-hep.org/uproot/examples/HZZ.root>`_ structured TTree.

.. code-block:: bash

    wget http://scikit-hep.org/uproot/examples/Zmumu.root
    wget http://scikit-hep.org/uproot/examples/HZZ.root

Open each of the files; uproot presents them as dict-like objects with ROOT names and objects as keys and values. (The "cycle number" after the semicolon can usually be ignored.)

.. code-block:: python

    >>> uproot.open("Zmumu.root").keys()
    ['events;1']
    >>> uproot.open("HZZ.root").keys()
    ['events;1']

Since the file acts as a dict, access the TTrees with square brackets. TTrees are also dict-like objects, with branch names and branches as keys and values. (Hint: ``allkeys()`` lists branches recursively, if they're nested.)

.. code-block:: python

    >>> zmumu = uproot.open("Zmumu.root")["events"]
    >>> hzz = uproot.open("HZZ.root")["events"]
    >>> zmumu.keys()
    ['Type', 'Run', 'Event', 'E1', 'px1', 'py1', 'pz1', 'pt1', 'eta1', 'phi1', 'Q1', 'E2', 'px2', 'py2',
     'pz2', 'pt2', 'eta2', 'phi2', 'Q2', 'M']
    >>> hzz.keys()
    ['NJet', 'Jet_Px', 'Jet_Py', 'Jet_Pz', 'Jet_E', 'Jet_btag', 'Jet_ID', 'NMuon', 'Muon_Px', 'Muon_Py',
     'Muon_Pz', 'Muon_E', 'Muon_Charge', 'Muon_Iso', 'NElectron', 'Electron_Px', 'Electron_Py',
     'Electron_Pz', 'Electron_E', 'Electron_Charge', 'Electron_Iso', 'NPhoton', 'Photon_Px', 'Photon_Py',
     ...]

You can turn a chosen set of branches into Numpy arrays with the ``arrays`` method. Each array represents the values of a single attribute for all events, just as they're stored in a split ROOT file.

.. code-block:: python

    >>> zmumu.arrays(["px1", "py1", "pz1"])
    {'px1': array([-41.19528764,  35.11804977,  35.11804977, ...,  32.37749196, 32.37749196,  32.48539387]),
     'py1': array([ 17.4332439 , -16.57036233, -16.57036233, ...,   1.19940578, 1.19940578,   1.2013503 ]),
     'pz1': array([-68.96496181, -48.77524654, -48.77524654, ..., -74.53243061, -74.53243061, -74.80837247])}

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

Reference Documentation
-----------------------

The complete reference documentation is available on `uproot.readthedocs.io <http://uproot.readthedocs.io/en/latest/>`_. These are exhaustive descriptions of each function and its parameters, also available as Python help strings.

- `Opening files <http://uproot.readthedocs.io/en/latest/opening-files.html>`_
- `ROOT I/O <http://uproot.readthedocs.io/en/latest/root-io.html>`_
- `TTree methods <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-ttreemethods>`_
- `TBranch methods <http://uproot.readthedocs.io/en/latest/ttree-handling.html#uproot-tree-tbranchmethods>`_

.. inclusion-marker-5-do-not-remove

Introductory Tutorials
----------------------

Reference documentation is not the place to start learning about a topic. Introductory tutorials are included on this page.

TODO!

..
   Capabilities
   ------------

   uproot is primarily intended for moving data between `ROOT TTrees <https://root.cern.ch/root/htmldoc/guides/users-guide/Trees.html>`_ and `Numpy arrays <http://www.scipy-lectures.org/intro/numpy/array_object.html>`_. Therefore, it works best on ROOT files containing tabular (flat ntuple) data, but it can also handle structured data, such as ``vector<double>`` or even arbitrary classes, thanks to `ROOT's streamer mechanism <https://root.cern.ch/root/html534/guides/users-guide/InputOutput.html#streamers>`_. Since ROOT was designed for C++ data structures, uproot has an open-ended API for interpreting data— if the default interpretations do not appeal to you, you can modify byte-level reading to fill your own data structures.

   In brief, uproot

   - reads TTree data as flat Numpy arrays, `jagged arrays <https://en.wikipedia.org/wiki/Jagged_array>`_ for data like ``vector<double>``, or `namedtuples <https://pymotw.com/2/collections/namedtuple.html>`_ for arbitrary classes.
   - reads any kind of object (such as histograms or fit functions) from a ROOT file, generating Python classes with the appropriate data members.
   - creates new arrays or fills user-provided arrays, if desired.
   - iterates over collections of files, similar to ROOT's TChain but as a loop over aligned sets of arrays.
   - parallelizes read operations using Python's `executor interface <https://www.blog.pythonlibrary.org/2016/08/03/python-3-concurrency-the-concurrent-futures-module/>`_ (reading and decompressing are both performed in parallel).
   - provides hooks to cache repeated reads.
   - has low-level access to ROOT's basket structure. Basket-reading from uncompressed, memory-mapped files incurs zero copies.
   - memory-mapped file reading by default; `XRootD for remote file servers <http://xrootd.org/>`_.

   The objects read from a ROOT file into Python are only data containers, lacking methods and bound functions written in C++. However, uproot recognizes some objects (most notably TTree) and imbues them with relevant Python methods. The collection of recognized methods will grow as needed and you can add your own.

   uproot 3.0 will be able to write data to ROOT files.

   Dependencies
   ------------

   For basic use, only **Python 2.6, 2.7, or 3.4+** and **Numpy 1.4+** are required. The following unlock extra features:

   - **Numba** (`pip <https://pypi.python.org/pypi/numba/0.35.0>`_, `conda <https://anaconda.org/numba/numba>`_) accelerates the reading of some data types. Since Numba is a Python compiler, you can also use it to speed up your analysis code. All data read out of TTrees is Numba-aware and can be used in Numba-accelerated functions.
   - **python-lzma** (`pip <https://pypi.python.org/pypi/backports.lzma>`_, `conda <https://anaconda.org/conda-forge/backports.lzma>`_) decompresses LZMA, one of the three algorithms used to encode ROOT data. This library is only needed for Python 2 because it is part of Python 3's standard library (like zlib, the most common compression algorithm used in ROOT).
   - **python-lz4** (`pip <https://pypi.python.org/pypi/lz4>`_, `conda <https://anaconda.org/anaconda/lz4>`_) decompresses LZ4, another algorithm used to compress some ROOT data.
   - **python-futures** (`pip <https://pypi.python.org/pypi/futures>`_, `conda <https://anaconda.org/anaconda/futures>`_) is a backport of the Python 3 parallelization interface. You only need this for Python 2.
   - **pyxrootd** (no pip, `conda <https://anaconda.org/search?q=xrootd>`_, `source <http://xrootd.org/dload.html>`_) accesses files using the XRootD (``root://``) protocol. (Hint: if you install XRootD from source, you may have to set ``PYTHONPATH`` and ``LD_LIBRARY_PATH``. XRootD's Python library is part of the C++ installation; avoid the external Python wrapper, which was XRootD 3 and below.)

   *Reminder: you do not need C++ ROOT to run uproot.*

   Performance
   -----------

   Despite Python's reputation as a slow language, uproot performs favorably to the standard C++ ROOT implementation because the majority of the processing is performed in `Numpy <http://www.numpy.org/>`_ calls. Special cases that can't be implemented in Numpy are implemented in `Numba <http://numba.pydata.org/>`_, which accelerates your code if you have Numba installed.

   Since these libraries are executed as or generate native bytecode, the usual Python speed constraints do not apply. (They even release the `Python GIL <https://opensource.com/article/17/4/grok-gil>`_ for good multithreaded scaling.)

   .. todo:: Update performance tests for uproot 2.0 and link to a separate page for performance plots.

   Why not PyROOT?
   ---------------

   `PyROOT <https://root.cern.ch/pyroot>`_ is a part of C++ ROOT that generates Python bindings on the fly. It requires C++ ROOT to be installed and provides the full power of ROOT, not just I/O. By nature of its design, however, it is very slow: type-checking, bounds checking, etc. are performed in real time. Also, Python's memory management does not perfectly mirror ROOT's ownership policies, leading to some surprising behavior.

   Why not root_numpy?
   -------------------

   `root_numpy <http://scikit-hep.org/root_numpy/index.html>`_ is a Cython project built on top of C++ ROOT. Unlike uproot, it requires C++ ROOT to be installed, but like uproot it copies data between TTrees and Numpy arrays. Although root_numpy is a little faster than ``TTree::Draw`` (because it uses a similar mechanism), uproot is much faster, particularly for jagged arrays (``vector<double>``).
