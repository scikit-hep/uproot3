ROOT I/O
========

The :py:mod:`uproot3.rootio` module contains everything needed to navigate through a ROOT file and extract inert, data-only objects. Methods for those objects are defined in other modules. The :py:func:`uproot3.open <uproot3.rootio.open>` function returns a :py:class:`ROOTDirectory <uproot3.rootio.ROOTDirectory>` object, which is a handle into the file, from which all other data can be accessed.

This module has many more classes than those documented here, but all but a few are considered internal details. The classes documented below represent the public API. In fact, only :py:class:`ROOTDirectory <uproot3.rootio.ROOTDirectory>` has useful attributes and methods for a typical user. The other two, :py:class:`ROOTObject <uproot3.rootio.ROOTObject>` and :py:class:`ROOTStreamedObject <uproot3.rootio.ROOTStreamedObject>`, are documented because they are superclasses of all objects that could be extracted from a ROOT file, and may be useful in ``isinstance`` checks.

uproot3.rootio.ROOTDirectory
---------------------------

Although :py:class:`ROOTDirectory <uproot3.rootio.ROOTDirectory>` resembles ROOT's TFile, TDirectory, and TFileDirectory to some degree, it does not have a direct relationship to any of them. (This is because we adopted a different model for representing the contents of a ROOT file: purely acyclic with continuation passing.) As a result, :py:class:`ROOTDirectory <uproot3.rootio.ROOTDirectory>` is not a :py:class:`ROOTObject <uproot3.rootio.ROOTObject>` and isn't named "TFile."

A :py:class:`ROOTDirectory <uproot3.rootio.ROOTDirectory>` may represent a whole ROOT file or a single TDirectory within that file--- after reading, there is no difference.

.. autoclass:: uproot3.rootio.ROOTDirectory

.. automethod:: uproot3.rootio.ROOTDirectory.get

.. automethod:: uproot3.rootio.ROOTDirectory.iterkeys

.. automethod:: uproot3.rootio.ROOTDirectory.itervalues

.. automethod:: uproot3.rootio.ROOTDirectory.iteritems

.. automethod:: uproot3.rootio.ROOTDirectory.iterclasses

.. automethod:: uproot3.rootio.ROOTDirectory.keys

.. automethod:: uproot3.rootio.ROOTDirectory.values

.. automethod:: uproot3.rootio.ROOTDirectory.items

.. automethod:: uproot3.rootio.ROOTDirectory.classes

.. automethod:: uproot3.rootio.ROOTDirectory.allkeys

.. automethod:: uproot3.rootio.ROOTDirectory.allvalues

.. automethod:: uproot3.rootio.ROOTDirectory.allitems

.. automethod:: uproot3.rootio.ROOTDirectory.allclasses

uproot3.rootio.ROOTObject
------------------------

.. autoclass:: uproot3.rootio.ROOTObject

uproot3.rootio.ROOTStreamedObject
--------------------------------

.. autoclass:: uproot3.rootio.ROOTStreamedObject
