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
