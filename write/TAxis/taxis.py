import numpy


class TAxis(object):

    def __init__(self, fNbins, fXmin, fXmax):
        self.string = ""
        self.fNbins = fNbins
        self.fXmin = fXmin
        self.fXmax = fXmax

    def values1(self):
        bytestream = [ 64,   0,   0, 106,   0,  10,  64,   0,   0,  16,   0,   1,   0,
          1,   0,   0,   0,   0,   2,   0,   0,   0,   2]
        return numpy.frombuffer(bytes(bytestream), dtype=numpy.uint8)

    def values2(self):
        return self.string

    def values3(self):
        bytestream = [64, 0, 0, 36, 0, 4, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0, 61, 76, 204, 205, 0, 1, 0,
                      42, 0]
        return numpy.frombuffer(bytes(bytestream), dtype=numpy.uint8)

    def values4(self):
        return self.fNbins, self.fXmin, self.fXmax

    def values5(self):
        bytestream = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Check for bugs
        return numpy.frombuffer(bytes(bytestream), dtype=numpy.uint8)
