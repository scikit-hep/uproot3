#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

import unittest

try:
    import lzma
except ImportError:
    from backports import lzma
import lz4

import uproot

class Test(unittest.TestCase):
    def test_compression_identity(self):
        assert uproot.open("tests/samples/Zmumu-zlib.root").compression.algoname == "zlib"
        assert uproot.open("tests/samples/Zmumu-zlib.root").compression.level == 4

        assert uproot.open("tests/samples/Zmumu-lzma.root").compression.algoname == "lzma"
        assert uproot.open("tests/samples/Zmumu-lzma.root").compression.level == 4

        assert uproot.open("tests/samples/Zmumu-lz4.root").compression.algoname == "lz4"
        assert uproot.open("tests/samples/Zmumu-lz4.root").compression.level == 4

        assert uproot.open("tests/samples/Zmumu-uncompressed.root").compression.level == 0

        assert uproot.open("tests/samples/HZZ-zlib.root").compression.algoname == "zlib"
        assert uproot.open("tests/samples/HZZ-zlib.root").compression.level == 4

        assert uproot.open("tests/samples/HZZ-lzma.root").compression.algoname == "lzma"
        assert uproot.open("tests/samples/HZZ-lzma.root").compression.level == 4

        assert uproot.open("tests/samples/HZZ-lz4.root").compression.algoname == "lz4"
        assert uproot.open("tests/samples/HZZ-lz4.root").compression.level == 4

        assert uproot.open("tests/samples/HZZ-uncompressed.root").compression.level == 0

    def test_compression_keys(self):
        keys = [(n, cls._classname) for n, cls in uproot.open("tests/samples/Zmumu-uncompressed.root").allclasses()]
        assert [(n, cls._classname) for n, cls in uproot.open("tests/samples/Zmumu-zlib.root").allclasses()] == keys
        assert [(n, cls._classname) for n, cls in uproot.open("tests/samples/Zmumu-lzma.root").allclasses()] == keys
        assert [(n, cls._classname) for n, cls in uproot.open("tests/samples/Zmumu-lz4.root").allclasses()] == keys

        keys = [(n, cls._classname) for n, cls in uproot.open("tests/samples/HZZ-uncompressed.root").allclasses()]
        assert [(n, cls._classname) for n, cls in uproot.open("tests/samples/HZZ-zlib.root").allclasses()] == keys
        assert [(n, cls._classname) for n, cls in uproot.open("tests/samples/HZZ-lzma.root").allclasses()] == keys
        assert [(n, cls._classname) for n, cls in uproot.open("tests/samples/HZZ-lz4.root").allclasses()] == keys

    def test_compression_branches(self):
        branches = list(uproot.open("tests/samples/Zmumu-uncompressed.root")["events"].keys())
        assert list(uproot.open("tests/samples/Zmumu-zlib.root")["events"].keys()) == branches
        assert list(uproot.open("tests/samples/Zmumu-lzma.root")["events"].keys()) == branches
        assert list(uproot.open("tests/samples/Zmumu-lz4.root")["events"].keys()) == branches

        branches = list(uproot.open("tests/samples/HZZ-uncompressed.root")["events"].keys())
        assert list(uproot.open("tests/samples/HZZ-zlib.root")["events"].keys()) == branches
        assert list(uproot.open("tests/samples/HZZ-lzma.root")["events"].keys()) == branches
        assert list(uproot.open("tests/samples/HZZ-lz4.root")["events"].keys()) == branches

    def test_compression_content1(self):
        for name, array in uproot.open("tests/samples/Zmumu-uncompressed.root")["events"].arrays(["Type", "Event", "E1", "px1", "Q1", "M"]).items():
            array = array.tolist()
            assert uproot.open("tests/samples/Zmumu-zlib.root")["events"].array(name).tolist() == array
            assert uproot.open("tests/samples/Zmumu-lzma.root")["events"].array(name).tolist() == array
            assert uproot.open("tests/samples/Zmumu-lz4.root")["events"].array(name).tolist() == array

    def test_compression_content2(self):
        array = uproot.open("tests/samples/HZZ-uncompressed.root")["events"].array("Electron_Px").tolist()
        assert uproot.open("tests/samples/HZZ-zlib.root")["events"].array("Electron_Px").tolist() == array
        assert uproot.open("tests/samples/HZZ-lzma.root")["events"].array("Electron_Px").tolist() == array
        assert uproot.open("tests/samples/HZZ-lz4.root")["events"].array("Electron_Px").tolist() == array
