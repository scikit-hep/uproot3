Interpretation
==============

ROOT was designed for C++, so ROOT data have an unambiguous C++ interpretation. However, their Python interpretation is open to interpretation. For instance, you may want a branch to be read as a new Numpy array, or perhaps a user-provided array in shared memory, with or without byte-swapping, type conversion, or reshaping, or as an array of unequal-length arrays, or an array of classes defined by the ROOT streamers, or an array of custom classes, or as a Numpy record array, etc. The Uproot :py:class:`Interpretation <uproot3.interp.interp.Interpretation>` mechanism provides such flexibility without sacrificing the flexibility of the selective reading methods.

If no interpretation is specified, :py:func:`uproot3.interpret <uproot3.interp.auto.interpret>` is automatically called to provide a reasonable default. This function may also be called by the user with custom arguments and its output may be modified in the *branches* or *interpretation* arguments of :py:class:`TTreeMethods <uproot3.tree.TTreeMethods>` and :py:class:`TBranchMethods <uproot3.tree.TBranchMethods>` array-producing functions.

uproot3.interp.interp.Interpretation
-----------------------------------

.. autoclass:: uproot3.interp.interp.Interpretation

uproot3.interpret
----------------

.. autofunction:: uproot3.interp.auto.interpret

uproot3.interp.numerical.asdtype
-------------------------------

.. autoclass:: uproot3.interp.numerical.asdtype

.. automethod:: uproot3.interp.numerical.asdtype.to

.. automethod:: uproot3.interp.numerical.asdtype.toarray

uproot3.interp.numerical.asarray
-------------------------------

.. autoclass:: uproot3.interp.numerical.asarray

uproot3.interp.numerical.asdouble32
----------------------------------

.. autoclass:: uproot3.interp.numerical.asdouble32

uproot3.interp.numerical.asstlbitset
-----------------------------------

.. autoclass:: uproot3.interp.numerical.asstlbitset

uproot3.interp.jagged.asjagged
-----------------------------

.. autoclass:: uproot3.interp.jagged.asjagged

.. automethod:: uproot3.interp.jagged.asjagged.to

uproot3.interp.objects.astable
-----------------------------

.. autoclass:: uproot3.interp.objects.astable

uproot3.interp.objects.asobj
---------------------------

.. autoclass:: uproot3.interp.objects.asobj

uproot3.interp.objects.asgenobj
------------------------------

.. autoclass:: uproot3.interp.objects.asgenobj

uproot3.interp.objects.asstring
------------------------------

.. autoclass:: uproot3.interp.objects.asstring
