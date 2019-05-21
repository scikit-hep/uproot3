Opening files
=============

Unlike ROOT, uproot strongly assumes that the input file does not change while you read it. File :py:class:`Sources <uproot.source.source.Source>` do not lock the file, and they may open, close, and reopen it as needed to read the file in parallel. Therefore, if another process is changing the contents of a file while uproot reads it, the behavior is undefined (but likely bad!).

uproot.open
-----------

All ROOT objects come from ROOT files, so :py:func:`open <uproot.rootio.open>` is probably the first function you'll call. The :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` object it returns is a handle for accessing contents deeper within the file.

.. autofunction:: uproot.rootio.open

uproot.xrootd
-------------

Although :py:func:`open <uproot.open>` opens files regardless of whether they're local or remote, you can explicitly invoke XRootD with :py:func:`xrootd <uproot.xrootd>`. You get the same kind of :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` as from :py:func:`open <uproot.open>`.

.. autofunction:: uproot.rootio.xrootd

uproot.iterate
--------------

With a :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`, you can dig into a file and extract objects, subdirectories, or TTree data, but sometimes you know exactly where to find a TTree and have a collection of identically-typed files to iterate through.

The :py:func:`iterate <uproot.iterate>` function gives you an iterator over groups of arrays just like :py:meth:`TreeMethods.iterate <uproot.tree.TreeMethods.iterate>`, except that it iterates over a large set of files (and verifies that the selected TTree branches are compatible). This serves essentially the same function as ROOT's TChain, allowing you to use TTrees in a set of files the same way you would use a single TTree.

.. autofunction:: uproot.tree.iterate

uproot.pandas.iterate
---------------------

Like the above, except that it iterates over Pandas DataFrames (as though you passed ``outputtype=pandas.DataFrame`` and changed some defaults).

.. autofunction:: uproot.pandas.iterate

uproot.lazyarray and lazyarrays
-------------------------------

The :py:func:`lazyarray <uproot.lazyarray>` and :py:func:`lazyarrays <uproot.lazyarrays>` give you a lazy view into a whole collection of files. They behave like the :py:meth:`TTreeMethods.lazyarray <uproot.tree.TTreeMethods.lazyarray>` and :py:meth:`TTreeMethods.lazyarrays <uproot.tree.TTreeMethods.lazyarrays>` methods except that they wildcarded filenames and a TTree name as the first arguments.

.. autofunction:: uproot.tree.lazyarray

.. autofunction:: uproot.tree.lazyarrays

uproot.daskarray and daskframe
------------------------------

Like the above, but presents the data as `Dask <https://dask.org/>`__ objects.

.. autofunction:: uproot.tree.daskarray

.. autofunction:: uproot.tree.daskframe

uproot.tree.numentries
----------------------

If you need to know the total number of entries of a set of files before processing them (e.g. for normalization or setting weights), you could open each file and TTree individually, but the function below is faster because it skips some steps that aren't needed when you only want the number of files.

.. autofunction:: uproot.tree.numentries
