ROOT I/O
========

The :py:mod:`uproot.rootio` module contains everything needed to navigate through a ROOT file and extract inert, data-only objects. Methods for those objects are defined in other modules. The :py:func:`uproot.open <uproot.rootio.open>` function returns a :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` object, which is a handle into the file, from which all other data can be accessed.

This module has many more classes than those documented here, but all but a few are considered internal details. The classes documented below represent the public API. In fact, only :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` has useful attributes and methods for a typical user. The other two, :py:class:`ROOTObject <uproot.rootio.ROOTObject>` and :py:class:`ROOTStreamedObject <uproot.rootio.ROOTStreamedObject>`, are documented because they are superclasses of all objects that could be extracted from a ROOT file, and may be useful in ``isinstance`` checks.

uproot.rootio.ROOTDirectory
---------------------------

Although :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` resembles ROOT's TFile, TDirectory, and TFileDirectory to some degree, it does not have a direct relationship to any of them. (This is because we adopted a different model for representing the contents of a ROOT file: purely acyclic with continuation passing.) As a result, :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` is not a :py:class:`ROOTObject <uproot.rootio.ROOTObject>` and isn't named "TFile."

A :py:class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` may represent a whole ROOT file or a single TDirectory within that file--- after reading, there is no difference.

.. autoclass:: uproot.rootio.ROOTDirectory

.. automethod:: uproot.rootio.ROOTDirectory.get

.. automethod:: uproot.rootio.ROOTDirectory.iterkeys

.. automethod:: uproot.rootio.ROOTDirectory.itervalues

.. automethod:: uproot.rootio.ROOTDirectory.iteritems

.. automethod:: uproot.rootio.ROOTDirectory.iterclasses

.. automethod:: uproot.rootio.ROOTDirectory.keys

.. automethod:: uproot.rootio.ROOTDirectory.values

.. automethod:: uproot.rootio.ROOTDirectory.items

.. automethod:: uproot.rootio.ROOTDirectory.classes

.. automethod:: uproot.rootio.ROOTDirectory.allkeys

.. automethod:: uproot.rootio.ROOTDirectory.allvalues

.. automethod:: uproot.rootio.ROOTDirectory.allitems

.. automethod:: uproot.rootio.ROOTDirectory.allclasses

uproot.rootio.ROOTObject
------------------------

.. autoclass:: uproot.rootio.ROOTObject

uproot.rootio.ROOTStreamedObject
--------------------------------

.. autoclass:: uproot.rootio.ROOTStreamedObject
