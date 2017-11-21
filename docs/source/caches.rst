Caches
======

Many functions in uproot may be given a cache to avoid expensive re-reading or re-calculating previously read or calculated quantities. These functions assume nothing about the cache other than a ``dict``-like interface: square brackets get old values and set new ones and ``in`` checks for existence. Therefore, a ``dict`` may be used as a "save forever" cache, but of course you might not have enough memory to save all data in memory forever.

The classes described on this page are drop-in replacements for ``dict`` with additional properties: least-recently-used (LRU) semantics, which drops the oldest cache item upon reaching a memory budget, as well as thread safety and process safety.

This interface, in which the user instantiates and passes the cache object explicitly instead of turning on an internal cache option, is to avoid situations in which the user can't determine where large amounts of memory are accumulating. When uproot reads a ROOT file, it does not save anything for reuse except what it puts in user-provided caches, so the user can always inspect these objects to see what's being saved.

The array-reading functions (in :py:class:`TTreeMethods <uproot.tree.TTreeMethods>` and :py:class:`TBranchMethods <uproot.tree.TBranchMethods>`) each have three cache parameters:

- **cache** for fully interpreted data. May yield stale results if the same branch is read with a different :py:class:`Interpretation <uproot.interp.interp.Interpretation>` and may result in unexpected cache misses if ``entrystart`` and ``entrystop`` boundaries change. Under normal circumstances, however, this cache is fastest.
- **rawcache** for raw basket data. Always yields correct results, regardless of how the branch is interpreted, because the interpreted data are not saved. This cache only avoids reading and decompressing the ROOT data, which is usually the biggest bottleneck. It is also insensitive to changes in ``entrystart`` and ``entrystop``. This is the safe option.
- **keycache** for basket TKeys. TKeys are tiny and may be stored in a "save forever" ``dict`` without much danger of running out of memory. Once bulk re-reading is avoided with a **cache** or **rawcache**, TKey re-reading may become a bottleneck, so the **keycache** provides a way to avoid it.

Passing explicit caches to **rawcache** and **keycache** will ensure that the file is read only once, while passing explicit caches to **cache** and **keycache** will ensure that the file is read *and interpreted* only once.

uproot.cache.MemoryCache
------------------------

.. autoclass:: uproot.cache.MemoryCache

uproot.cache.ThreadSafeMemoryCache
----------------------------------

.. autoclass:: uproot.cache.ThreadSafeMemoryCache

uproot.cache.ThreadSafeDict
---------------------------

.. autoclass:: uproot.cache.ThreadSafeDict

uproot.cache.DiskCache
----------------------

.. autoclass:: uproot.cache.DiskCache

uproot.cache.diskcache.arrayread
--------------------------------

.. autofunction:: uproot.cache.diskcache.arrayread

uproot.cache.diskcache.arraywrite
---------------------------------

.. autofunction:: uproot.cache.diskcache.arraywrite

uproot.cache.diskcache.memmapread
---------------------------------

.. autofunction:: uproot.cache.diskcache.memmapread
