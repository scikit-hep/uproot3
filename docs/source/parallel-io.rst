Parallel I/O
============

An essential aspect of uproot's file-reader is that data :py:class:`Sources <uproot.source.source.Source>` are completely distinct from :py:class:`Cursors <uproot.source.cursor.Cursor>`, which track position in the source. This interface is similar to memory-mapped files, which do not track a position but respond as needed to requests for data by address, and it is unlike traditional file handles, which reference the source of data (integer linked to a file through syscalls) and a position within it (queried by ``seek`` and changed by ``tell``) as an indivisible unit. By default, uproot reads data through memory-mapped files; all other sources are made to *look* like a memory-mapped file.

Throughout the ROOT I/O and TTree-handling modules, :py:class:`Sources <uproot.source.source.Source>` and :py:class:`Cursors <uproot.source.cursor.Cursor>` are passed as independent objects. A :py:class:`Cursor <uproot.source.cursor.Cursor>` cannot read data without being given an explicit :py:class:`Source <uproot.source.source.Source>`. When parts of a file are to be read in parallel, lightweight :py:class:`Cursors <uproot.source.cursor.Cursor>` are duplicated, one per thread, while :py:class:`Sources <uproot.source.source.Source>` are only duplicated (e.g. multiple file handles into the same file) if the source is not inherently thread-safe (as memory-mapped files are).

Even when not reading in parallel, copying a :py:class:`Cursor <uproot.source.cursor.Cursor>` when passing it to a subroutine is a lightweight way to keep one's place without the spaghetti of ``seek`` and ``tell`` commands to backtrack, as is often necessary in the ROOT file structure.

uproot.source.cursor.Cursor
---------------------------

.. autoclass:: uproot.source.cursor.Cursor

.. automethod:: uproot.source.cursor.Cursor.copied

.. automethod:: uproot.source.cursor.Cursor.skipped

.. automethod:: uproot.source.cursor.Cursor.skip

.. automethod:: uproot.source.cursor.Cursor.fields

.. automethod:: uproot.source.cursor.Cursor.field

.. automethod:: uproot.source.cursor.Cursor.bytes

.. automethod:: uproot.source.cursor.Cursor.array

.. automethod:: uproot.source.cursor.Cursor.string

.. automethod:: uproot.source.cursor.Cursor.cstring

.. automethod:: uproot.source.cursor.Cursor.skipstring

.. automethod:: uproot.source.cursor.Cursor.hexdump

uproot.source.source.Source
---------------------------

.. autoclass:: uproot.source.source.Source

uproot.FileSource
-----------------

.. autoattribute:: uproot.source.file.FileSource.defaults

.. autoclass:: uproot.source.file.FileSource

uproot.MemmapSource
-------------------

.. autoattribute:: uproot.source.memmap.MemmapSource.defaults

.. autoclass:: uproot.source.memmap.MemmapSource

uproot.XRootDSource
-------------------

.. autoattribute:: uproot.source.xrootd.XRootDSource.defaults

.. autoclass:: uproot.source.xrootd.XRootDSource

uproot.HTTPSource
-------------------

.. autoattribute:: uproot.source.http.HTTPSource.defaults

.. autoclass:: uproot.source.http.HTTPSource

uproot.source.compressed.CompressedSource
-----------------------------------------

.. autoclass:: uproot.source.compressed.Compression

.. autoclass:: uproot.source.compressed.CompressedSource
