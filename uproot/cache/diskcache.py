#!/usr/bin/env python

# Copyright (c) 2017, DIANA-HEP
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import ast
import glob
import hashlib
import json
import math
import os
import random
import re
import shutil
import struct
try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    from urllib import quote as urlquote
    from urllib import unquote as urlunquote
except ImportError:
    from urllib.parse import quote as urlquote
    from urllib.parse import unquote as urlunquote
try:
    import fcntl
except ImportError:
    fcntl = None

import numpy

class MemmapWithDel(numpy.core.memmap):
    def __del__(self):
        try:
            self._cleanup()
        except:
            pass

def memmapread(filename, cleanup):
    file = MemmapWithDel(filename, dtype=numpy.uint8)
    file._cleanup = cleanup

    magic_version = file[:8]
    if numpy.array_equal(magic_version, memmapread.version1):
        # version 1.0
        headersize = file[8:10].view(numpy.uint16)[0]
        index = 10
    elif numpy.array_equal(magic_version, memmapread.version2):
        # version 2.0 (unlikely)
        headersize = file[8:12].view(numpy.uint32)[0]
        index = 12
    else:
        return None

    header = ast.literal_eval(file[index:index + headersize].tostring().decode("ascii"))
    out = file[index + headersize:].view(header["descr"])

    if header["fortran_order"]:
        out = numpy.asfortranarray(out)

    if header["shape"] != out.shape:
        out = out.reshape(header["shape"])

    return out

memmapread.version1 = numpy.array([147, 78, 85, 77, 80, 89, 1, 0], dtype=numpy.uint8)
memmapread.version2 = numpy.array([147, 78, 85, 77, 80, 89, 2, 0], dtype=numpy.uint8)

def arrayread(filename, cleanup):
    if hasattr(filename, "read") and hasattr(filename, "close"):
        file = filename
    else:
        file = open(filename, "rb")

    try:
        magic_version = file.read(8)
        if magic_version == b"\x93NUMPY\x01\x00":
            # version 1.0
            headersize, = struct.unpack("<H", file.read(2))
        elif magic_version == b"\x93NUMPY\x02\x00":
            # version 2.0 (unlikely)
            headersize, = struct.unpack("<I", file.read(4))
        else:
            return None

        header = ast.literal_eval(file.read(headersize).decode("ascii"))
        out = numpy.fromfile(file, dtype=header["descr"])

        if header["fortran_order"]:
            out = numpy.asfortranarray(out)

        if header["shape"] != out.shape:
            out = out.reshape(header["shape"])

        return out

    finally:
        file.close()
        cleanup()

def arraywrite(filename, obj):
    with open(filename, "wb") as file:
        numpy.save(file, obj)

def anyread(filename, cleanup):
    file = open(filename, "rb")
    if file.read(6) == b"\x93NUMPY":
        file.seek(0)
        return arrayread(file, cleanup)
    else:
        try:
            file.seek(0)
            return pickle.load(file)
        finally:
            file.close()
            cleanup()

def anywrite(filename, obj):
    if isinstance(obj, numpy.ndarray):
        return arraywrite(filename, obj)
    else:
        with open(filename, "wb") as file:
            pickle.dump(obj, file)

class DiskCache(object):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (type,), {})

    CONFIG_FILE = "config.json"
    STATE_FILE = "state.json"
    LOOKUP_FILE = "lookup.npy"
    ORDER_DIR = "order"
    COLLISIONS_DIR = "collisions"
    TMP_DIR = "tmp"
    PID_DIR_PREFIX = "pid-"

    def __init__(self, *args, **kwds):
        raise TypeError("create a DiskCache with DiskCache.create or DiskCache.join")

    class Config(object): pass
    class State(object): pass

    @staticmethod
    def create(limitbytes, directory, read=anyread, write=anywrite, lookupsize=10000, maxperdir=100, delimiter="-", numformat=numpy.uint64):
        if fcntl is None:
            raise NotImplementedError("DiskCache is currently supported only on systems with fcntl (such as Mac and Linux, not Windows)")

        if os.path.exists(directory):
            shutil.rmtree(directory)

        parent = os.path.split(directory)[0]
        if parent != "" and not os.path.exists(parent):
            raise ValueError("cannot create {0} because {1} does not exist".format(repr(directory), repr(parent)))

        numformat = str(numpy.dtype(numformat))

        os.mkdir(directory)
        statefile = open(os.path.join(directory, DiskCache.STATE_FILE), "w")
        fcntl.lockf(statefile, fcntl.LOCK_EX)
        try:
            os.mkdir(os.path.join(directory, DiskCache.ORDER_DIR))
            os.mkdir(os.path.join(directory, DiskCache.COLLISIONS_DIR))

            lookupfilename = os.path.join(directory, DiskCache.LOOKUP_FILE)
            lookupfile = open(lookupfilename, "wb")
            try:
                magic = b"\x93NUMPY"
                lookupfile.write(magic)

                header = repr({"descr": numformat, "fortran_order": False, "shape": (lookupsize,)}).encode("ascii")
                headersize = int(math.ceil((len(header) + 1 + len(magic) + 4) / 16.0)) * 16 - len(magic) - 4
                if headersize < 2**16:
                    # version 1.0
                    lookupfile.write(struct.pack("<BBH", 1, 0, headersize))
                else:
                    # version 2.0 (unlikely)
                    headersize = int(math.ceil((len(header) + 1 + len(magic) + 6) / 16.0)) * 16 - len(magic) - 6
                    lookupfile.write(struct.pack("<BBI", 2, 0, headersize))

                header = header + b" " * (headersize - len(header) - 1) + b"\n"
                lookupfile.write(header)
                lookupfile.flush()
                offset = lookupfile.tell()
            finally:
                lookupfile.close()

            out = DiskCache.__new__(DiskCache)

            out._lookup = numpy.memmap(lookupfilename, dtype=numformat, mode="r+", offset=offset, shape=(lookupsize,), order="C")
            out._EMPTY = numpy.iinfo(numpy.dtype(numformat).type).max
            out._COLLISION = numpy.iinfo(numpy.dtype(numformat).type).max - 1
            out._lookup[:] = out._EMPTY
            out._lookup.flush()

            config = {"limitbytes": limitbytes, "lookupsize": lookupsize, "maxperdir": maxperdir, "delimiter": delimiter, "numformat": numformat}
            state = {"numbytes": os.path.getsize(lookupfilename), "depth": 0, "next": 0}
            with open(os.path.join(directory, DiskCache.CONFIG_FILE), "w") as configfile:
                json.dump(config, configfile)
            statefile.write(json.dumps(state))
            statefile.flush()

            out.config = DiskCache.Config()
            out.config.__dict__.update(config)
            out.state = DiskCache.State()
            out.state.__dict__.update(state)
            out.directory = directory
            out.read = read
            out.write = write
            out._formatter = "{0:0" + str(int(math.ceil(math.log(config["maxperdir"], 10)))) + "d}"
            out._lock = None

        finally:
            fcntl.lockf(statefile, fcntl.LOCK_UN)
            statefile.close()

        return out

    @staticmethod
    def join(directory, read=anyread, write=anywrite, check=True):
        if fcntl is None:
            raise NotImplementedError("DiskCache is currently supported only on systems with fcntl (such as Mac and Linux, not Windows)")

        if not os.path.exists(directory):
            raise ValueError("cannot join {0} because it does not exist".format(repr(directory)))

        out = DiskCache.__new__(DiskCache)
        out.directory = directory
        out.read = read
        out.write = write
        out._lock = ()

        out.config = DiskCache.Config()
        with open(os.path.join(directory, DiskCache.CONFIG_FILE), "r") as configfile:
            out.config.__dict__.update(json.load(configfile))
        out._formatter = "{0:0" + str(int(math.ceil(math.log(out.config.maxperdir, 10)))) + "d}"

        digits = re.compile("^[0-9]{" + str(int(math.ceil(math.log(out.config.maxperdir, 10)))) + "}$")

        def recurse(depth, num, path):
            items = os.listdir(path)
            items.sort()

            if len(items) == 0:
                raise ValueError("cannot join {0} because {1} is an empty directory".format(repr(directory), repr(path)))

            elif len(items) > out.config.maxperdir:
                raise ValueError("cannot join {0} because {1} has more than maxperdir ({2}) items".format(repr(directory), repr(path), out.config.maxperdir))

            elif all(os.path.isdir(os.path.join(path, fn)) and digits.match(fn) for fn in items):
                for fn in items:
                    recurse(depth + 1, (num + int(fn)) * out.config.maxperdir, os.path.join(path, fn))

            elif all(not os.path.isdir(os.path.join(path, fn)) for fn in items):
                if depth != out.state.depth:
                    raise ValueError("cannot join {0} because depth in {1} ({2}) disagrees with depth in directory tree ({3})".format(repr(directory), repr(DiskCache.CONFIG_FILE), out.config.depth, depth))

                for fn in items:
                    if out.config.delimiter not in fn or not digits.match(fn[:fn.index(out.config.delimiter)]):
                        raise ValueError("cannot join {0} because {1} is not a proper file name with delimiter {2}".format(repr(directory), repr(fn), repr(out.config.delimiter)))

                    i = fn.index(out.config.delimiter)
                    number = num + int(fn[:i])
                    name = urlunquote(fn[i + 1:])

                    path = out._get(name)
                    if not os.path.exists(path):
                        raise ValueError("cannot join {0} because {1} (for key {2}) does not exist".format(repr(directory), repr(path), repr(name)))
                    out._unchecked[out._index(name)] = False

            else:
                raise ValueError("cannot join {0} because directory {1} is neither an all-directory nor an all-file directory".format(repr(directory), repr(path)))
                
        statefile = open(os.path.join(directory, DiskCache.STATE_FILE), "r+")
        fcntl.lockf(statefile, fcntl.LOCK_EX)
        try:
            out.state = DiskCache.State()
            out.state.__dict__.update(json.loads(statefile.read()))

            lookupfilename = os.path.join(directory, DiskCache.LOOKUP_FILE)
            with open(lookupfilename, "rb") as lookupfile:
                magic_version = lookupfile.read(8)
                if magic_version == b"\x93NUMPY\x01\x00":
                    # version 1.0
                    headersize, = struct.unpack("<H", lookupfile.read(2))
                    offset = 10 + headersize
                elif magic_version == b"\x93NUMPY\x02\x00":
                    # version 2.0 (unlikely)
                    headersize, = struct.unpack("<I", lookupfile.read(4))
                    offset = 12 + headersize
                else:
                    raise ValueError("cannot join {0} because {1} is incorrectly formatted".format(repr(directory), repr(lookupfilename)))

            out._lookup = numpy.memmap(lookupfilename, dtype=out.config.numformat, mode="r+", offset=offset, shape=(out.config.lookupsize,), order="C")
            out._EMPTY = numpy.iinfo(numpy.dtype(out.config.numformat).type).max
            out._COLLISION = numpy.iinfo(numpy.dtype(out.config.numformat).type).max - 1

            if check:
                out._unchecked = numpy.ones(out.config.lookupsize, dtype=numpy.bool)
                recurse(0, 0, os.path.join(directory, out.ORDER_DIR))

                if not (out._lookup[out._unchecked] == out._EMPTY).all():
                    raise ValueError("cannot join {0} because some hash bins in {1} that don't point to any files aren't empty".format(repr(directory), repr(DiskCache.LOOKUP_FILE)))
                del out._unchecked

        finally:
            fcntl.lockf(statefile, fcntl.LOCK_UN)
            statefile.close()
            out._lock = None

        return out

    def destroy(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)

    def refresh_config(self):
        self.config.__dict__.update(json.load(os.path.join(self.directory, self.CONFIG_FILE)))

    def __contains__(self, name, lock=True):
        if not isinstance(name, bytes) and hasattr(name, "encode"):
            name = name.encode("utf-8")
        if not isinstance(name, bytes):
            raise TypeError("keys must be strings, not {0}".format(type(name)))

        if lock:
            self._lockstate()
        try:
            for num, n in self._walkorder(os.path.join(self.directory, self.ORDER_DIR), reverse=True):
                if name == n:
                    return True
            return False

        finally:
            if lock:
                self._unlockstate()

    def promote(self, name, lock=True):
        if not isinstance(name, bytes) and hasattr(name, "encode"):
            name = name.encode("utf-8")
        if not isinstance(name, bytes):
            raise TypeError("keys must be strings, not {0}".format(type(name)))

        if lock:
            self._lockstate()
        try:
            oldpath = self._get(name)  # might raise KeyError

            # promote this item
            olddepth = self.state.depth
            newpath = self._newpath(name)
            newdepth = self.state.depth

            if olddepth != newdepth:
                oldpath = self._get(name)

            os.rename(oldpath, newpath)
            self._cleandirs(os.path.split(oldpath)[0])

            # update _lookup
            self._del(name)
            self._set(name, self._path2num(newpath))

        finally:
            if lock:
                self._unlockstate()

    def __getitem__(self, name, lock=True):
        if not isinstance(name, bytes) and hasattr(name, "encode"):
            name = name.encode("utf-8")
        if not isinstance(name, bytes):
            raise TypeError("keys must be strings, not {0}".format(type(name)))

        if lock:
            self._lockstate()
        try:
            oldpath = self._get(name)  # might raise KeyError

            # promote this item
            olddepth = self.state.depth
            newpath = self._newpath(name)
            newdepth = self.state.depth

            if olddepth != newdepth:
                oldpath = self._get(name)

            os.rename(oldpath, newpath)
            self._cleandirs(os.path.split(oldpath)[0])

            # update _lookup
            self._del(name)
            self._set(name, self._path2num(newpath))

            # link it so that we can release this lock
            piddir = self._piddir()
            linkpath = self._pidfile(piddir)
            os.link(newpath, linkpath)

        finally:
            if lock:
                self._unlockstate()

        def cleanup():
            os.remove(linkpath)
            try:
                os.rmdir(piddir)
            except OSError:
                pass

        return self.read(linkpath, cleanup)

    def __setitem__(self, name, value, lock=True):
        if not isinstance(name, bytes) and hasattr(name, "encode"):
            name = name.encode("utf-8")
        if not isinstance(name, bytes):
            raise TypeError("keys must be strings, not {0}".format(type(name)))

        # making piddir outside of lock; have to retry in case another thread rmdirs it
        piddir = self._piddir()
        pidpath = self._pidfile(piddir)
        while True:
            try:
                self.write(pidpath, value)   # try to write to this file
            except:
                if os.path.exists(piddir):   # if it fails for any reason other than losing the piddir,
                    raise                    # pass on that error!
                else:
                    piddir = self._piddir()  # otherwise, it's because another process removed the piddir;
            else:                            # simply reinstate it
                break   # success! get out of the while loop!

        if lock:
            self._lockstate()
        try:
            try:
                oldpath = self._get(name)
            except KeyError:
                # new key
                pass
            else:
                # old key
                self.state.numbytes -= os.path.getsize(oldpath)
                os.remove(oldpath)
                self._cleandirs(os.path.split(oldpath)[0])
                self._del(name)

            newpath = self._newpath(name)
            newnum = self._path2num(newpath)

            os.rename(pidpath, newpath)
            self.state.numbytes += os.path.getsize(newpath)
            self._set(name, newnum)

            self._evict(os.path.join(self.directory, self.ORDER_DIR), True)

        finally:
            if lock:
                self._unlockstate()

        try:
            os.rmdir(piddir)
        except:
            pass

    def __delitem__(self, name, lock=True):
        if not isinstance(name, bytes) and hasattr(name, "encode"):
            name = name.encode("utf-8")
        if not isinstance(name, bytes):
            raise TypeError("keys must be strings, not {0}".format(type(name)))

        if lock:
            self._lockstate()
        try:
            oldpath = self._get(name)
            self.state.numbytes -= os.path.getsize(oldpath)
            os.remove(oldpath)
            self._cleandirs(os.path.split(oldpath)[0])
            self._del(name)
        finally:
            if lock:
                self._unlockstate()

    def get(self, name, default=None, lock=True):
        try:
            return self.__getitem__(name, lock=lock)
        except KeyError:
            return default

    def setdefault(self, key, default=None, lock=True):
        if lock:
            self._lockstate()
        try:
            if not self.__contains__(key, lock=False):
                self.__setitem__(key, default, lock=False)
                return default
            else:
                return self.__getitem__(key, lock=False)
        finally:
            if lock:
                self._unlockstate()

    def do(self, key, function, lock=True):
        if not callable(function):
            raise TypeError("'function' must be a zero-argument function")
        if lock:
            self._lockstate()
        try:
            if not self.__contains__(key, lock=False):
                value = function()
                self.__setitem__(key, value, lock=False)
                return value
            else:
                return self.__getitem__(key, lock=False)
        finally:
            if lock:
                self._unlockstate()

    def keys(self, lock=True):
        if lock:
            self._lockstate()
        try:
            for num, name in self._walkorder(os.path.join(self.directory, self.ORDER_DIR)):
                yield name.decode("utf-8")
        finally:
            if lock:
                self._unlockstate()

    def items(self, lock=True):
        linkpaths = []

        if lock:
            self._lockstate()
        try:
            piddir = self._piddir()
            for num, name in self._walkorder(os.path.join(self.directory, self.ORDER_DIR)):
                oldpath = self._get(name)
                linkpath = self._pidfile(piddir)
                os.link(oldpath, linkpath)
                linkpaths.append((name, linkpath))

        finally:
            if lock:
                self._unlockstate()

        def make_cleanup(linkpath):   # Python's function-based variable scope
            def cleanup():
                os.remove(linkpath)
                try:
                    os.rmdir(piddir)
                except OSError:
                    pass
            return cleanup

        for name, linkpath in linkpaths:
            yield name.decode("utf-8"), self.read(linkpath, make_cleanup(linkpath))

    def values(self):
        for name, obj in self.items():
            yield obj

    @property
    def numbytes(self):
        self._lockstate()
        try:
            return self.state.numbytes
        finally:
            self._unlockstate()

    def _lockstate(self):
        assert self._lock is None
        self._lock = open(os.path.join(self.directory, self.STATE_FILE), "r+")
        fcntl.lockf(self._lock, fcntl.LOCK_EX)
        self.state.__dict__.update(json.load(self._lock))

    def _unlockstate(self):
        assert self._lock is not None
        self._lookup.flush()
        self._lock.seek(0)
        self._lock.truncate()
        json.dump(self.state.__dict__, self._lock)
        self._lock.flush()
        fcntl.lockf(self._lock, fcntl.LOCK_UN)
        self._lock.close()
        self._lock = None

    def _num2path(self, num):
        assert self._lock is not None
        assert num < self.config.maxperdir**(self.state.depth + 1)
        path = [self.directory, self.ORDER_DIR]
        for n in range(self.state.depth, 0, -1):
            factor = self.config.maxperdir**n
            path.append(self._formatter.format(int(num) // factor))
            num = num % factor
        path.append(self._formatter.format(int(num)))
        return os.path.join(*path)

    def _path2num(self, path):
        assert self._lock is not None
        prefix = os.path.join(self.directory, self.ORDER_DIR)
        num = 0
        for n in range(0, self.state.depth + 1):
            path, fn = os.path.split(path)
            if self.config.delimiter in fn:
                digit = int(fn[:fn.index(self.config.delimiter)])
            else:
                digit = int(fn)
            num += digit * self.config.maxperdir**n
        return num

    def _piddir(self):
        piddir = os.path.join(self.directory, DiskCache.PID_DIR_PREFIX + repr(os.getpid()))
        try:
            os.mkdir(piddir)
        except:
            if not os.path.exists(piddir) or not os.path.isdir(piddir):
                raise   # fail for any reason other than attempting to mkdir an existing dir
        return piddir

    def _pidfile(self, piddir):
        return os.path.join(piddir, "{0}-{1}".format(len(os.listdir(piddir)), "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for x in range(30))))

    def _index(self, name):
        if not isinstance(name, bytes) and hasattr(name, "encode"):
            name = name.encode("utf-8")
        if not isinstance(name, bytes):
            raise TypeError("keys must be strings, not {0}".format(type(name)))
        return abs(int(hashlib.md5(name).hexdigest(), 16)) % self.config.lookupsize

    def _get(self, name):
        assert self._lock is not None
        index = self._index(name)
        num = self._lookup[index]

        if num == self._EMPTY:
            raise KeyError(name)

        elif num == self._COLLISION:
            # lookupsize should be made large enough that collisions are unlikely
            collisionsfilename = os.path.join(self.directory, self.COLLISIONS_DIR, repr(index))
            with open(collisionsfilename, "r") as collisionsfile:
                num = json.load(collisionsfile)[urlquote(name, safe="")]

        dir, prefix = os.path.split(self._num2path(num))
        path = os.path.join(dir, prefix + self.config.delimiter + urlquote(name, safe=""))

        if not os.path.exists(path):
            raise KeyError(name)
        else:
            return path

    def _set(self, name, num):
        assert self._lock is not None
        index = self._index(name)
        oldvalue = self._lookup[index]

        if oldvalue == self._EMPTY:
            # should be the usual case
            self._lookup[index] = num

        elif oldvalue == self._COLLISION:
            # already has a collisions file; just update it
            collisionsfilename = os.path.join(self.directory, self.COLLISIONS_DIR, repr(index))
            with open(collisionsfilename, "r") as collisionsfile:
                collisions = json.load(collisionsfile)
            collisions[urlquote(name, safe="")] = int(num)
            with open(collisionsfilename, "w") as collisionsfile:
                json.dump(collisions, collisionsfile)
            # don't change self._lookup[index]

        else:
            # new collision; need to make the collisions file
            otherpath = glob.glob(self._num2path(oldvalue) + "*")[0]
            othername = otherpath[otherpath.index(self.config.delimiter) + 1:]

            collisionsfilename = os.path.join(self.directory, self.COLLISIONS_DIR, repr(index))
            with open(collisionsfilename, "w") as collisionsfile:
                json.dump({urlquote(name, safe=""): int(num), othername: int(oldvalue)}, collisionsfile)
            self._lookup[index] = self._COLLISION

    def _del(self, name):
        assert self._lock is not None
        index = self._index(name)
        oldvalue = self._lookup[index]

        if oldvalue == self._EMPTY:
            # nothing to delete
            raise KeyError(name)

        elif oldvalue == self._COLLISION:
            # have to update collisions file
            collisionsfilename = os.path.join(self.directory, self.COLLISIONS_DIR, repr(index))
            with open(collisionsfilename, "r") as collisionsfile:
                collisions = json.load(collisionsfile)

            del collisions[urlquote(name, safe="")]  # might result in a KeyError, and that's appropriate

            assert len(collisions) != 0
            if len(collisions) == 1:
                # now there's only one left; remove the collisions file and just set the _lookup directly
                othernum, = collisions.values()
                self._lookup[index] = othernum
                os.remove(collisionsfilename)
            else:
                # there's more than one left; we still need the collisions file
                with open(collisionsfilename, "w") as collisionsfile:
                    json.dump(collisions, collisionsfile)

        else:
            self._lookup[index] = self._EMPTY

    def _newpath(self, name):
        assert self._lock is not None

        # increase depth if necessary
        while self.state.next >= self.config.maxperdir**(self.state.depth + 1):
            self.state.depth += 1

            # move the subdirectories/files into a new directory
            tmp = os.path.join(self.directory, self.TMP_DIR)
            assert not os.path.exists(tmp)
            os.mkdir(tmp)
            count = 0
            for fn in os.listdir(os.path.join(self.directory, self.ORDER_DIR)):
                os.rename(os.path.join(self.directory, self.ORDER_DIR, fn), os.path.join(tmp, fn))
                count += 1

            # and rename the new directory as "000"
            if count > 0:
                os.rename(tmp, os.path.join(self.directory, self.ORDER_DIR, self._formatter.format(0)))
            else:
                os.rmdir(tmp)

        # create directories in path if necessary
        path = os.path.join(self.directory, self.ORDER_DIR)
        num = self.state.next
        for n in range(self.state.depth, 0, -1):
            factor = self.config.maxperdir**n
            path = os.path.join(path, self._formatter.format(num // factor))
            num = num % factor
            if n != 0 and not os.path.exists(path):
                os.mkdir(path)

        # update next
        self.state.next += 1

        # return new path
        return os.path.join(path, self._formatter.format(num) + self.config.delimiter + urlquote(name, safe=""))

    def _walkorder(self, path, sort=True, reverse=False):
        assert self._lock is not None
        items = os.listdir(path)
        if sort:
            items.sort(reverse=reverse)

        for fn in items:
            subpath = os.path.join(path, fn)
            if os.path.isdir(subpath):
                for x in self._walkorder(subpath, sort=sort, reverse=reverse):
                    yield x
            else:
                i = fn.index(self.config.delimiter)
                num = int(fn[:i])
                name = urlunquote(fn[i + 1:])
                yield num, name.encode("utf-8")

    def _evict(self, path, top):
        assert self._lock is not None
        if self.state.numbytes <= self.config.limitbytes:
            return

        # eliminate in sort order
        items = os.listdir(path)
        items.sort()

        for fn in items:
            if self.state.numbytes <= self.config.limitbytes:
                return

            subpath = os.path.join(path, fn)

            if os.path.isdir(subpath):
                # descend to the next level
                self._evict(subpath, False)

            else:
                # delete a file
                name = urlunquote(fn[fn.index(self.config.delimiter) + 1:])
                self._del(name)
                self.state.numbytes -= os.path.getsize(subpath)
                os.remove(subpath)

        # clean up empty directories
        if not top:
            try:
                os.rmdir(path)
            except:
                pass

    def _cleandirs(self, path):
        assert self._lock is not None
        prefix = os.path.join(self.directory, self.ORDER_DIR)
        while path != prefix:
            try:
                os.rmdir(path)
            except:
                return
            path, fn = os.path.split(path)
