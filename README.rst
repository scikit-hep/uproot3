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

**Strict dependencies:**

- `Python <http://docs.python-guide.org/en/latest/starting/installation/>`_ (2.6+, 3.4+)
- `Numpy <https://scipy.org/install.html>`_

**Recommended dependencies:**

- `lz4 <https://anaconda.org/anaconda/lz4>`_ compression used by some ROOT files
- `lzma <https://anaconda.org/conda-forge/backports.lzma>`_ compression used by some ROOT files; this is part of the Python 3 standard library, so only install for Python 2

**Optional dependencies:** (all are bindings to binaries that can be package-installed)

- `Numba and LLVM <http://numba.pydata.org/numba-doc/latest/user/installing.html>`_ to JIT-compile functions (requires a particular version of LLVM, follow instructions)
- `python-futures <https://pypi.python.org/pypi/futures>`_ for parallel processing; this is part of the Python 3 standard library, so only install for Python 2

*Reminder: you do not need C++ ROOT to run uproot.*

.. inclusion-marker-3-do-not-remove

Getting started
---------------

Download a Z → μμ `flat ntuple <http://scikit-hep.org/uproot/examples/Zmumu.root>`_ and a H → ZZ → μμμμ `structured TTree <http://scikit-hep.org/uproot/examples/HZZ.root>`_.

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

.. inclusion-marker-5-do-not-remove

TODO!
