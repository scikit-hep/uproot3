Opening files
=============

uproot.open
-----------

All ROOT objects come from ROOT files, so the first function you'll probably call is :py:func:`uproot.open`.

.. autofunction:: uproot.open

uproot.xrootd
-------------

Although :py:func:`uproot.open` opens files regardless of whether they're local or remote, you can explicitly invoke XRootD with :py:func:`uproot.xrootd`.

.. autofunction:: uproot.xrootd

uproot.iterate
--------------

From a :py:class:`uproot.rootio.ROOTDirectory` returned by :py:func:`uproot.open`, you can search through directories and find your TTree. However, this is inconvenient if you want to iterate over a large collection of files, each with a TTree in the same location. (In C++ ROOT, you would use a TChain.) For this kind of iteration in uproot, you would call :py:func:`uproot.iterate`.

.. autofunction:: uproot.iterate
