import numpy
import struct
from write.utils import resize
from write.utils import get_eof_position


class Sink(object):

    def __init__(self, file):
        self.file = file

    def set_bytestream(self, pos, toadd):
        if (pos + len(toadd)) > get_eof_position(self.file):
            self.file = resize(self.file, pos + len(toadd) + 1)
        self.file.seek(pos)
        self.file.write(toadd)

    def set_numbers(self, pos, packer, *args):
        toadd = numpy.frombuffer(struct.pack(packer, *args), dtype=numpy.uint8)
        self.set_bytestream(pos, toadd)

    def set_strings(self, pos, toput):
        self.file = resize(self.file, get_eof_position(self.file) + 1)
        try:
            self.file.seek(pos)
        except:
            self.file = resize(self.file, get_eof_position(self.file) + 1)
            self.file.seek(pos)
        # toadd = bytes(str(len(toput)), "ascii")
        toadd = numpy.frombuffer(struct.pack(">B", len(toput)), dtype=numpy.uint8)
        self.file.write(toadd)
        pos = self.file.tell()
        toadd = numpy.frombuffer(toput, dtype=numpy.uint8)
        if (pos + len(toadd)) > get_eof_position(self.file):
            self.file = resize(self.file, pos + len(toadd) + 1)
        self.file.seek(pos)
        self.file.write(toadd)

    def set_cname(self, pos, toput):
        toadd = numpy.frombuffer(toput, dtype=numpy.uint8)
        if (pos + len(toadd)) > get_eof_position(self.file):
            self.file = resize(self.file, pos + len(toadd) + 1)
        self.file.seek(pos)
        self.file.write(toadd)

    def set_array(self, pos, packer, array):
        buffer = bytearray()
        packer = packer
        for x in array:
            buffer = buffer + struct.pack(packer, x)
        toadd = numpy.frombuffer(buffer, dtype=numpy.uint8)
        if (pos + len(toadd)) > get_eof_position(self.file):
            self.file = resize(self.file, pos + len(toadd) + 1)
        self.file.seek(pos)
        self.file.write(toadd)

    def set_empty_array(self, pos):
        data = bytearray()
        toadd = numpy.frombuffer(data, dtype=numpy.uint8)
        if (pos + len(toadd)) > get_eof_position(self.file):
            self.file = resize(self.file, pos + len(toadd) + 1)
        self.file.seek(pos)
        self.file.write(toadd)

    def set_header(self, header):
        pos = 0
        packer, magic, fVersion = header.get_values1()
        self.set_numbers(pos, packer, magic, fVersion)
        pos = self.file.tell()
        packer, fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress, fSeekInfo, fNbytesInfo, fUUID = header.get_values2()
        self.set_numbers(pos, packer, fBEGIN, fEND, fSeekFree, fNbytesFree, nfree, fNbytesName, fUnits, fCompress,
                         fSeekInfo, fNbytesInfo, fUUID)

    def set_key(self, pos, key):
        packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir, fClassName, fName, fTitle = key.get_values()
        self.set_numbers(pos, packer, fNbytes, fVersion, fObjlen, fDatime, fKeylen, fCycle, fSeekKey, fSeekPdir)
        pos = self.file.tell()
        self.set_strings(pos, fClassName)
        pos = self.file.tell()
        self.set_strings(pos, fName)
        pos = self.file.tell()
        self.set_strings(pos, fTitle)

    def set_directoryinfo(self, pos, directory):
        pos += 1
        packer, fVersion, fDatimeC, fDatimeM, fNbytesKeys, fNbytesName = directory.get_values1()
        self.set_numbers(pos, packer, fVersion, fDatimeC, fDatimeM, fNbytesKeys, fNbytesName)
        pos = self.file.tell()
        packer, fSeekDir, fSeekParent, fSeekKeys = directory.get_values2()
        self.set_numbers(pos, packer, fSeekDir, fSeekParent, fSeekKeys)

    def set_tobjstring(self, pos, Object):
        packer, cnt, vers = Object.values1()
        self.set_numbers(pos, packer, cnt, vers)
        pos = self.file.tell()
        toadd = Object.values2()
        self.set_bytestream(pos, toadd)

    def set_taxis(self, pos, Object, keyname):
        Object.string = keyname
        self.file.seek(pos)
        cnt, vers, packer = Object.valuestop1()
        self.set_numbers(pos, packer, cnt, vers)
        pos = self.file.tell()
        self.file.seek(pos)
        cnt, vers, packer = Object.valuestop2()
        self.set_numbers(pos, packer, cnt, vers)
        pos = self.file.tell()
        self.file.seek(pos)
        self.file.write(Object.values1())
        pos = self.file.tell()
        self.set_strings(pos, Object.values2().encode("utf-8"))
        pos = self.file.tell() + 1
        self.file.seek(pos)
        self.file.write(Object.values3())
        pos = self.file.tell() - 1
        fNbins, fXmin, fXmax = Object.values4()
        self.set_numbers(pos, ">i", fNbins)
        pos = self.file.tell()
        self.set_numbers(pos, ">dd", fXmin, fXmax)
        pos = self.file.tell()
        self.file.write(Object.values5())
        
    def set_th1f(self, pos, Object):
        self.file.seek(pos)
        self.file.write(Object.values1())
        pos = self.file.tell() - 1
        self.file.seek(pos)
        nbinsx, xlow, xup = Object.values2()
        self.set_numbers(pos, ">idd", nbinsx, xlow, xup)
        pos = self.file.tell()
        self.file.seek(pos)
        self.file.write(Object.values3())
        for x in range(0, 15504):
            pos = self.file.tell()
            self.file.seek(pos)
            self.file.write(numpy.frombuffer(bytes([0]), dtype=numpy.uint8))


