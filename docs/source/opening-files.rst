Opening files
=============

Unlike ROOT, Uproot strongly assumes that the input file does not change while you read it. File :py:class:`Sources <uproot3.source.source.Source>` do not lock the file, and they may open, close, and reopen it as needed to read the file in parallel. Therefore, if another process is changing the contents of a file while Uproot reads it, the behavior is undefined (but likely bad!).

uproot3.open
-----------

All ROOT objects come from ROOT files, so :py:func:`uproot3.open <uproot3.rootio.open>` is probably the first function you'll call. The :py:class:`ROOTDirectory <uproot3.rootio.ROOTDirectory>` object it returns is a handle for accessing contents deeper within the file. If the file is remote, use ``"root://"`` or ``"http://"`` in the file name to invoke a remote protocol.

.. autofunction:: uproot3.rootio.open

uproot3.xrootd
-------------

Although :py:func:`uproot3.open <uproot3.rootio.open>` opens files regardless of whether they're local or remote, you can explicitly invoke XRootD with :py:func:`uproot3.xrootd <uproot3.rootio.xrootd>`. You get the same kind of :py:class:`ROOTDirectory <uproot3.rootio.ROOTDirectory>` as from :py:func:`uproot3.open <uproot3.rootio.open>`.

.. autofunction:: uproot3.rootio.xrootd

uproot3.http
-----------

You can also open files through the HTTP protocol (and some XRootD servers support HTTP, too). The :py:func:`uproot3.http <uproot3.rootio.http>` function opens files via HTTP.

.. autofunction:: uproot3.rootio.http

uproot3.iterate
--------------

With a :py:class:`ROOTDirectory <uproot3.rootio.ROOTDirectory>`, you can dig into a file and extract objects, subdirectories, or TTree data, but sometimes you know exactly where to find a TTree and have a collection of identically-typed files to iterate through.

The :py:func:`uproot3.iterate <uproot3.tree.iterate>` function gives you an iterator over groups of arrays just like :py:meth:`TreeMethods.iterate <uproot3.tree.TreeMethods.iterate>`, except that it iterates over a large set of files (and verifies that the selected TTree branches are compatible). This serves essentially the same function as ROOT's TChain, allowing you to use TTrees in a set of files the same way you would use a single TTree.

.. autofunction:: uproot3.tree.iterate

uproot3.pandas.iterate
---------------------

The :py:func:`uproot3.pandas.iterate <uproot3.pandas.iterate>` function is like the above, except that it iterates over Pandas DataFrames (as though you passed ``outputtype=pandas.DataFrame`` and changed some defaults).

.. autofunction:: uproot3.pandas.iterate

uproot3.lazyarray and lazyarrays
-------------------------------

The :py:func:`uproot3.lazyarray <uproot3.tree.lazyarray>` and :py:func:`uproot3.lazyarrays <uproot3.tree.lazyarrays>` give you a lazy view into a whole collection of files. They behave like the :py:meth:`TTreeMethods.lazyarray <uproot3.tree.TTreeMethods.lazyarray>` and :py:meth:`TTreeMethods.lazyarrays <uproot3.tree.TTreeMethods.lazyarrays>` methods except that they wildcarded filenames and a TTree name as the first arguments.

.. autofunction:: uproot3.tree.lazyarray

.. autofunction:: uproot3.tree.lazyarrays

uproot3.daskarray and daskframe
------------------------------

The following are the above, but presents the data as `Dask <https://dask.org/>`__ objects.

.. autofunction:: uproot3.tree.daskarray

.. autofunction:: uproot3.tree.daskframe

uproot3.numentries
-----------------

If you need to know the total number of entries of a set of files before processing them (e.g. for normalization or setting weights), you could open each file and TTree individually, but the function below is faster because it skips some steps that aren't needed when you only want the number of files.

.. autofunction:: uproot3.tree.numentries
