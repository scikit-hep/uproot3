Parallel I/O
============

An essential aspect of Uproot's file-reader is that data :py:class:`Sources <uproot3.source.source.Source>` are completely distinct from :py:class:`Cursors <uproot3.source.cursor.Cursor>`, which track position in the source. This interface is similar to memory-mapped files, which do not track a position but respond as needed to requests for data by address, and it is unlike traditional file handles, which reference the source of data (integer linked to a file through syscalls) and a position within it (queried by ``seek`` and changed by ``tell``) as an indivisible unit. By default, Uproot reads data through memory-mapped files; all other sources are made to *look* like a memory-mapped file.

Throughout the ROOT I/O and TTree-handling modules, :py:class:`Sources <uproot3.source.source.Source>` and :py:class:`Cursors <uproot3.source.cursor.Cursor>` are passed as independent objects. A :py:class:`Cursor <uproot3.source.cursor.Cursor>` cannot read data without being given an explicit :py:class:`Source <uproot3.source.source.Source>`. When parts of a file are to be read in parallel, lightweight :py:class:`Cursors <uproot3.source.cursor.Cursor>` are duplicated, one per thread, while :py:class:`Sources <uproot3.source.source.Source>` are only duplicated (e.g. multiple file handles into the same file) if the source is not inherently thread-safe (as memory-mapped files are).

Even when not reading in parallel, copying a :py:class:`Cursor <uproot3.source.cursor.Cursor>` when passing it to a subroutine is a lightweight way to keep one's place without the spaghetti of ``seek`` and ``tell`` commands to backtrack, as is often necessary in the ROOT file structure.

uproot3.source.cursor.Cursor
---------------------------

.. autoclass:: uproot3.source.cursor.Cursor

.. automethod:: uproot3.source.cursor.Cursor.copied

.. automethod:: uproot3.source.cursor.Cursor.skipped

.. automethod:: uproot3.source.cursor.Cursor.skip

.. automethod:: uproot3.source.cursor.Cursor.fields

.. automethod:: uproot3.source.cursor.Cursor.field

.. automethod:: uproot3.source.cursor.Cursor.bytes

.. automethod:: uproot3.source.cursor.Cursor.array

.. automethod:: uproot3.source.cursor.Cursor.string

.. automethod:: uproot3.source.cursor.Cursor.cstring

.. automethod:: uproot3.source.cursor.Cursor.skipstring

.. automethod:: uproot3.source.cursor.Cursor.hexdump

uproot3.source.source.Source
---------------------------

.. autoclass:: uproot3.source.source.Source

uproot3.FileSource
-----------------

.. autoattribute:: uproot3.source.file.FileSource.defaults

.. autoclass:: uproot3.source.file.FileSource

uproot3.MemmapSource
-------------------

.. autoattribute:: uproot3.source.memmap.MemmapSource.defaults

.. autoclass:: uproot3.source.memmap.MemmapSource

uproot3.XRootDSource
-------------------

.. autoattribute:: uproot3.source.xrootd.XRootDSource.defaults

.. autoclass:: uproot3.source.xrootd.XRootDSource

uproot3.HTTPSource
-------------------

.. autoattribute:: uproot3.source.http.HTTPSource.defaults

.. autoclass:: uproot3.source.http.HTTPSource

uproot3.source.compressed.CompressedSource
-----------------------------------------

.. autoclass:: uproot3.source.compressed.Compression

.. autoclass:: uproot3.source.compressed.CompressedSource
