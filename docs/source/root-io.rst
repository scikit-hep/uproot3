ROOT I/O
========

The :module:`uproot.rootio` module contains everything needed to navigate through a ROOT file and extract inert, data-only objects. Methods for those objects are defined in other modules. The :func:`uproot.open <uproot.rootio.open>` function returns a :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` object, which is a handle into the file, from which all other data can be accessed.

The :module:`uproot.rootio` module contains many classes not documented here because they are considered internal details. (Most of these are concerned with the ROOT file's *streamer info,* which describe the layout of the classes we extract.) In fact, three of the classes described below--- :class:`ROOTObject <uproot.rootio.ROOTObject>`, :class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`, and :class:`TKey <uproot.rootio.TKey>`--- will probably never be accessed directly by the user, but the first two are relevant as superclasses and the third is so important for the operation of ROOT file seeking that we document it anyway.

uproot.rootio.ROOTDirectory
---------------------------

.. autofunction:: uproot.rootio.ROOTDirectory

.. automethod:: uproot.rootio.ROOTDirectory.get

.. automethod:: uproot.rootio.ROOTDirectory.keys

.. automethod:: uproot.rootio.ROOTDirectory.values

.. automethod:: uproot.rootio.ROOTDirectory.items

uproot.rootio.ROOTObject
------------------------

uproot.rootio.ROOTStreamedObject
--------------------------------

uproot.rootio.TKey
------------------
