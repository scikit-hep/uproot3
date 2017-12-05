uproot
======

.. image:: https://travis-ci.org/scikit-hep/uproot.svg?branch=master
   :target: https://travis-ci.org/scikit-hep/uproot

ROOT I/O in pure Python and Numpy.

uproot (originally μproot, for "micro-Python ROOT") is a reader and (someday) a writer of the `ROOT file format <https://root.cern/>`_ using only Python and Numpy. Unlike the standard C++ ROOT implementation, uproot is only an I/O library, primarily intended to stream data into machine learning libraries in Python.

It is important to note that uproot is *not* maintained by the ROOT project team, so post bug reports as `uproot GitHub issues <https://github.com/scikit-hep/uproot/issues>`_, not on any ROOT forum.

Documentation
-------------

See `uproot.readthedocs.io <http://uproot.readthedocs.io/en/latest/>`_ for the latest documentation. To install, simply

.. code-block:: bash

    pip install uproot --user

.. inclusion-marker-do-not-remove

Capabilities
------------

uproot is primarily intended for moving data between `ROOT TTrees <https://root.cern.ch/root/htmldoc/guides/users-guide/Trees.html>`_ and `Numpy arrays <http://www.scipy-lectures.org/intro/numpy/array_object.html>`_. Therefore, it works best on ROOT files containing tabular (flat ntuple) data, but it can also handle structured data, such as ``vector<double>`` or even arbitrary classes, thanks to `ROOT's streamer mechanism <https://root.cern.ch/root/html534/guides/users-guide/InputOutput.html#streamers>`_. Since ROOT was designed for C++ data structures, uproot has an open-ended API for interpreting data--- if the default interpretations do not appeal to you, you can modify byte-level reading to fill your own data structures.

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
