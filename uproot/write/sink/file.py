#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

class Sink(object):
    pass

class FileSink(Sink):
    def __init__(self, path):
        self._path = path
        self._sink = open(path, "wb+")
        # self._pos = 0

    def write(self, data, pos):
        self._sink.seek(pos)
        self._sink.write(data)

    # def write(self, data, pos):
    #     if self._sink.tell() != pos:
    #         self._sink.seek(pos)
    #     self._sink.write(data)

    # def write(self, data, pos):
    #     if self._pos != pos:
    #         self._sink.seek(pos)
    #     self._sink.write(data)
    #     self._pos += len(data)    # needs self._pos

    @property
    def closed(self):
        return self._sink.closed

    def close(self):
        if not self._sink.closed:
            self._sink.close()

    def flush(self):
        if not self._sink.closed:
            self._sink.flush()
