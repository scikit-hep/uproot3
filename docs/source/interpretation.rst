Interpretation
==============

ROOT was designed for C++, so ROOT data have an unambiguous C++ interpretation. However, their Python interpretation is open to interpretation. For instance, you may want a branch to be read as a new Numpy array, or perhaps a user-provided array in shared memory, with or without byte-swapping, type conversion, or reshaping, or as an array of unequal-length arrays, or an array of classes defined by the ROOT streamers, or an array of custom classes, or as a Numpy record array, etc. The uproot :py:class:`Interpretation <uproot.interp.interp.Interpretation>` mechanism provides such flexibility without sacrificing the flexibility of the selective reading methods.

If no interpretation is specified, :py:func:`uproot.interpret <uproot.interp.auto.interpret>` is automatically called to provide a reasonable default. This function may also be called by the user with custom arguments and its output may be modified in the *branches* or *interpretation* arguments of :py:class:`TTreeMethods <uproot.tree.TTreeMethods>` and :py:class:`TBranchMethods <uproot.tree.TBranchMethods>` array-producing functions.

uproot.interp.interp.Interpretation
-----------------------------------

.. autoclass:: uproot.interp.interp.Interpretation

uproot.interpret
----------------

.. autofunction:: uproot.interp.auto.interpret

uproot.interp.asdtype
---------------------

.. autoclass:: uproot.interp.numerical.asdtype

.. automethod:: uproot.interp.numerical.asdtype.to

.. automethod:: uproot.interp.numerical.asdtype.toarray

uproot.interp.asarray
---------------------

.. autoclass:: uproot.interp.numerical.asarray

uproot.interp.asjagged
----------------------

.. autoclass:: uproot.interp.jagged.asjagged

.. automethod:: uproot.interp.jagged.asjagged.to

uproot.interp.jagged.JaggedArray
--------------------------------

.. autoclass:: uproot.interp.jagged.JaggedArray

.. automethod:: uproot.interp.jagged.JaggedArray.fromlists

uproot.interp.asstrings
-----------------------

.. autoclass:: uproot.interp.strings.asstrings

uproot.interp.strings.Strings
-----------------------------

.. autoclass:: uproot.interp.strings.Strings

.. automethod:: uproot.interp.strings.Strings.fromstrs
