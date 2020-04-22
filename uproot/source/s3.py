from __future__ import absolute_import

import multiprocessing
import sys
from urllib.parse import urlparse

import numpy

import uproot.source.chunked


class S3Source(uproot.source.chunked.ChunkedSource):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.source.chunked.ChunkedSource.__metaclass__,), {})

    def __init__(self, path, *args, **kwds):
        super(S3Source, self).__init__(path, *args, **kwds)

        url_parsed = urlparse(self.path)
        if "s3" not in url_parsed.scheme:
            raise ValueError("%s not a valid s3 url" % self.path)
        scheme = url_parsed.scheme.replace("s3", "")
        self.endpoint_url = scheme + "://" + url_parsed.netloc
        self.local_path = url_parsed.path
        if not self.local_path:
            raise ValueError("%s not a valid s3 url" % self.path)

        self.fs = None  # the filesystem
        self._size = None

    defaults = {
        "chunkbytes": 1024 ** 2,
        "limitbytes": 100 * 1024 ** 2,
        "parallel": 8 * multiprocessing.cpu_count() if sys.version_info[0] > 2 else 1,
    }

    def size(self):
        if self._size is None:
            self._open()
        return self._size

    def _open(self):
        try:
            import s3fs
        except ImportError:
            raise ImportError("Install s3fs package with:\n    conda install -c conda-forge s3fs.")
        if self.fs is None:
            self.fs = s3fs.S3FileSystem(client_kwargs={"endpoint_url": self.endpoint_url})
        self._source = self.fs.open(self.local_path, "rb")
        self._size = self._source.info()["size"]

    def _read(self, chunkindex):
        self._source.seek(chunkindex * self._chunkbytes)
        data = self._source.read(self._chunkbytes)
        return numpy.frombuffer(data, dtype=numpy.uint8)

    def dismiss(self):
        if self._source is not None:
            self._source.close()  # local file connections are *not shared* among threads
