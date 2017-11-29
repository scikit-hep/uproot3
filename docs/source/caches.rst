Caches
======

Many functions in uproot may be given a cache to avoid expensive re-reading or re-calculating previously read or calculated quantities. These functions assume nothing about the cache other than a ``dict``-like interface: square brackets get old values and set new ones and ``in`` checks for existence. Therefore, a ``dict`` may be used as a "save forever" cache, but of course you might not have enough memory to save all data in memory forever.

The classes described on this page are drop-in replacements for ``dict`` with additional properties: least-recently-used (LRU) eviction, which drops the oldest cache item upon reaching a memory budget, as well as thread safety and process safety.

This interface, in which the user instantiates and passes the cache object explicitly instead of turning on an internal cache option, is to avoid situations in which the user can't determine where large amounts of memory are accumulating. When uproot reads a ROOT file, it does not save anything for reuse except what it puts in user-provided caches, so the user can always inspect these objects to see what's being saved.

The array-reading functions (in :py:class:`TTreeMethods <uproot.tree.TTreeMethods>` and :py:class:`TBranchMethods <uproot.tree.TBranchMethods>`) each have three cache parameters:

- **cache** for fully interpreted data. Accessing the same arrays with a different interpretation or a different entry range results in a cache miss.
- **basketcache** for raw basket data. Accessing the same arrays with a different interpretation or a different entry range fully utilizes this cache, since the interpretation/construction from baskets is performed after retrieving data from this cache.
- **keycache** for basket TKeys. TKeys are small, but require file access, so caching them can speed up repeated access.

Passing explicit caches to **basketcache** and **keycache** will ensure that the file is read only once, while passing explicit caches to **cache** and **keycache** will ensure that the file is read *and interpreted* only once.

uproot.cache.MemoryCache
------------------------

.. autoclass:: uproot.cache.memorycache.MemoryCache

uproot.cache.ThreadSafeMemoryCache
----------------------------------

.. autoclass:: uproot.cache.memorycache.ThreadSafeMemoryCache

uproot.cache.ThreadSafeDict
---------------------------

.. autoclass:: uproot.cache.memorycache.ThreadSafeDict

uproot.cache.DiskCache
----------------------

.. autoclass:: uproot.cache.diskcache.DiskCache

.. automethod:: uproot.cache.diskcache.DiskCache.create

.. automethod:: uproot.cache.diskcache.DiskCache.join

uproot.cache.arrayread
----------------------

.. autofunction:: uproot.cache.diskcache.arrayread

uproot.cache.arraywrite
-----------------------

.. autofunction:: uproot.cache.diskcache.arraywrite

uproot.cache.memmapread
-----------------------

.. autofunction:: uproot.cache.diskcache.memmapread
