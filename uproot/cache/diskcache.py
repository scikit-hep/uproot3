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
import fcntl
import json
import math
import numbers
import os
import random
import re
import shutil
import struct
import sys

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

    header = ast.literal_eval(file[index:index + headersize].tostring())
    out = file[index + headersize:].view(header["descr"])

    if header["fortran_order"]:
        out = numpy.asfortranarray(out)

    if header["shape"] != out.shape:
        out = out.reshape(header["shape"])

    return out

memmapread.version1 = numpy.array([147, 78, 85, 77, 80, 89, 1, 0], dtype=numpy.uint8)
memmapread.version2 = numpy.array([147, 78, 85, 77, 80, 89, 2, 0], dtype=numpy.uint8)

def arrayread(filename, cleanup):
    try:
        file = open(filename, "rb"):
        magic_version = file.read(8)
        if magic_version == b"\x93NUMPY\x01\x00":
            # version 1.0
            headersize, = struct.unpack("<H", file.read(2))
        elif magic_version == b"\x93NUMPY\x02\x00":
            # version 2.0 (unlikely)
            headersize, = struct.unpack("<I", file.read(4))
        else:
            return None

        header = ast.literal_eval(file.read(headersize))
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
    numpy.save(open(filename, "wb"), obj)

class DiskCache(object):
    CONFIG_FILE = "config.json"
    STATE_FILE = "state.json"
    DATA_DIR = "data"
    TMP_DIR = "tmp"
    PID_DIR_PREFIX = "pid-"

    __slots__ = ("directory", "config", "read", "write")

    def __init__(self, *args, **kwds):
        raise TypeError("create a DiskCache with DiskCache.create or DiskCache.join")

    @staticmethod
    def create(limitbytes, directory, read=arrayread, write=arraywrite, maxperdir=100, delimiter="."):
        if os.path.exists(directory):
            shutil.rmtree(directory)

        if not os.path.exists(os.path.split(directory)[0]):
            raise OSError("cannot create {0} because {1} does not exist".format(repr(directory), repr(os.path.split(directory)[0])))

        config = {"limitbytes": limitbytes, "maxperdir": maxperdir, "delimiter": delimiter}
        state = {"numbytes": 0, "depth": 0, "next": 0, "lastevict": None}

        os.mkdir(directory)
        json.dump(open(os.path.join(directory, self.CONFIG_FILE), "w"), config)
        json.dump(open(os.path.join(directory, self.STATE_FILE), "w"), state)
        os.mkdir(os.path.join(directory, DiskCache.DATA_DIR))

        out = DiskCache.__new__(DiskCache)
        out.directory = directory
        out.config = config
        out.read = read
        out.write = write
        out._name2path = {}
        out._num2name = {}
        out._depth = 0
        out._next = 0
        out._lastevict = None
        out._formatter = "{0:0" + str(int(math.ceil(math.log(self.config["maxperdir"], 10)))) + "d}"
        return out
        
    @staticmethod
    def join(directory, read=arrayread, write=arraywrite):
        if not os.path.exists(directory):
            raise OSError("cannot join {0} because it does not exist".format(repr(directory)))
        if not os.path.isdir(directory):
            raise OSError("cannot join {0} because it is not a directory".format(repr(directory)))

        datadir = os.path.join(directory, self.DATA_DIR)
        if not os.path.exists(datadir):
            raise OSError("cannot join {0} because {1} does not exist".format(repr(directory), repr(datadir)))
        if not os.path.isdir(datadir):
            raise OSError("cannot join {0} because {1} is not a directory".format(repr(directory), repr(datadir)))
        
        config = json.load(open(os.path.join(directory, self.CONFIG_FILE)))
        numdigits = int(math.ceil(math.log(config["maxperdir"], 10)))
        digits = re.compile("^[0-9]{" + str(numdigits) + "}$")

        state = {"numbytes": 0, "depth": None, "next": None, "lastevict": None}
        name2path = {}
        num2name = {}

        def recurse(d, n, path):
            items = os.listdir(os.path.join(datadir, path))
            items.sort()

            # directories should all have numerical names (with the right number of digits)
            if all(os.path.isdir(os.path.join(datadir, path, fn)) and digits.match(fn) for fn in items):
                for fn in items:
                    recurse(d + 1, (n + int(fn)) * config["maxperdir"], os.path.join(path, fn))

            # a directory of files should all be files; no mixing of files and directories
            elif all(not os.path.isdir(os.path.join(datadir, path, fn)) for fn in items):
                for fn in items:
                    if config["delimiter"] not in fn or not digits.match(fn[:fn.index(config["delimiter"])]):
                        raise OSError("file name {0} in {1} is malformed; should be '{2}{3}NAME'".format(repr(fn), repr(os.path.join(datadir, path)), "#" * numdigits, config["delimiter"]))

                i = fn.index(config["delimiter"])
                name = fn[i + 1:]
                config["numbytes"] += os.path.getsize(os.path.join(datadir, path, fn))
                number = n + int(fn[:i])

                name2path[name] = os.path.join(path, fn)
                num2name[number] = name

                if state["depth"] is None:
                    state["depth"] = d
                elif state["depth"] != d:
                    raise OSError("some files are at depth {0}, others at depth {1}".format(state["depth"], d))

                if state["next"] is not None and number <= state["next"]:
                    raise OSError("cache numbers are not in increasing order")
                state["next"] = number
                
            else:
                raise OSError("directory contents must either be all directories (named /{0}/ because maxperdir is {1}) or all be files; failure at {2}".format(digits.pattern, config["maxperdir"], os.path.join(datadir, path)))

        statefile = open(os.path.join(directory, self.STATE_FILE), "rw")
        fcntl.lockf(statefile, fcntl.LOCK_EX)   # block until we get exclusive access to state.json
        try:
            recurse(0, 0, "")
            if state["depth"] is None:
                assert state["next"] is None
                state["depth"] = 0
                state["next"] = 0
            else:
                assert state["next"] is not None
                state["next"] += 1

            oldstate = json.load(statefile)
            for key, value in oldstate.items():
                if key not in state:
                    state[key] = value
                elif state[key] != value:
                    raise OSError("state.json differs from expected state in key {0}:\n\n    {1}\n\nvs\n\n    {2}".format(repr(key), oldstate, state))

            statefile.seek(0)
            statefile.truncate()
            json.dump(statefile, state)

        finally:
            fcntl.lockf(statefile, fcntl.LOCK_UN)  # release state.json
            statefile.close()

        out = DiskCache.__new__(DiskCache)
        out.directory = directory
        out.config = config
        out.read = read
        out.write = write
        out._name2path = name2path
        out._num2name = num2name
        out._depth = config["depth"]
        out._next = config["next"]
        out._lastevict = config["lastevict"]
        out._formatter = "{0:0" + str(int(math.ceil(math.log(config["maxperdir"], 10)))) + "d}"
        return out

    @staticmethod
    def _tmpfilename(directory):
        return os.path.join(piddir, "{0}-{1}".format(len(os.listdir(piddir)), "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for x in range(30))))

    def __getitem__(self, name):
        statefile = open(os.path.join(self.directory, self.STATE_FILE), "rw")
        fcntl.lockf(statefile, fcntl.LOCK_EX)   # block until we get exclusive access to state.json
        try:
            state = json.load(statefile)
            self._update(state)

            if name not in self._name2path:
                raise KeyError(repr(name))

            self._promote(state, name)

            oldpath = self._name2path[name]
            piddir = os.path.join(directory, DiskCache.PID_DIR_PREFIX + str(os.getpid()))
            if not os.path.exists(piddir):
                os.mkdir(piddir)
            newpath = self._tmpfilename(piddir)
            os.link(oldpath, newpath)

            statefile.seek(0)
            statefile.truncate()
            json.dump(statefile, state)

        finally:
            fcntl.lockf(statefile, fcntl.LOCK_UN)  # release state.json
            statefile.close()

        def cleanup():
            os.remove(newpath)
            try:
                os.rmdir(piddir)
            except OSError:
                pass

        return self.read(newpath, cleanup)
        
    def __setitem__(self, name, value):
        piddir = os.path.join(directory, DiskCache.PID_DIR_PREFIX + str(os.getpid()))
        try:
            os.mkdir(piddir)
        except:
            if not os.path.exists(piddir):
                raise

        newpath = self._tmpfilename(piddir)
        self.write(newpath, value)

        statefile = open(os.path.join(self.directory, self.STATE_FILE), "rw")
        fcntl.lockf(statefile, fcntl.LOCK_EX)   # block until we get exclusive access to state.json
        try:
            state = json.load(statefile)
            self._update(state)

            if name in self._name2path:
                self._promote(state, name)
                oldpath = self._name2path[name]
            







            statefile.seek(0)
            statefile.truncate()
            json.dump(statefile, state)

        finally:
            fcntl.lockf(statefile, fcntl.LOCK_UN)  # release state.json
            statefile.close()




        
    def __delitem__(self, name):
        raise NotImplementedError

    def _update(self, state):
        if self._depth < state["depth"]:
            prefix = ""
            while self._depth < state["depth"]:
                prefix = os.path.join(prefix, self._formatter.format(0))
                self._depth += 1
            self._addprefix(prefix)

        if self._lastevict != state["lastevict"]:
            if self.lastevict is None:
                self.lastevict = -1
            self._cleanlookup(self.lastevict, state["lastevict"])
            self.lastevict = state["lastevict"]

        if self._next != state["next"]:
            self._updatelookup(self._next, state["next"], "", 0, self._depth)

    def _addprefix(self, prefix):
        for n, path in self._name2path.items():
            self._name2path[n] = os.path.join(prefix, path)

    def _cleanlookup(self, oldlastevict, newlastevict):
        if oldlastevict is None:
            oldlastevict = -1
        if newlastevict is None:
            return
        for number in range(oldlastevict + 1, newlastevict + 1):
            if number in self._num2name:
                name = self._num2name[number]
                del self._num2name[number]
                del self._name2path[name]

    def _updatelookup(self, oldnext, newnext, path, origin, depth):
        items = os.listdir(os.path.join(self.directory, self.DATA_DIR, path))
        items.sort()

        for fn in items:
            subpath = os.path.join(path, fn)

            if os.path.isdir(os.path.join(self.directory, self.DATA_DIR, subpath)):
                # maybe descend to the next level
                low = origin + (int(fn) * self.config["maxperdir"]**depth)
                high = low + self.config["maxperdir"]**depth
                if low <= oldnext and newnext <= high:
                    self._updatelookup(oldnext, newnext, subpath, low, depth - 1)

            else:
                # maybe add files to lookup
                i = fn.index(self.config["delimiter"])
                number = origin + int(fn[:i])
                name = fn[i + 1:]
                if oldnext <= number < newnext:
                    self._num2name[number] = name
                    self._name2path[name] = subpath
        
    def _path2num(self, path):
        num = 0
        while path != "":
            path, fn = os.path.split(path)
            if self.config["delimiter"] in fn:
                n = int(fn[:fn.index(self.config["delimiter"])])
            else:
                n = int(fn)
            num = num * self.config["maxperdir"] + n
        return num

    def _promote(self, state, name):
        newnum, newpath = self._numpath(state, name)   # _numpath changes _name2path
        oldpath = self._name2path[name]                # and therefore must be called first
        oldnum = self._path2num(oldpath)

        os.rename(os.path.join(self.directory, self.DATA_DIR, oldpath), os.path.join(self.directory, self.DATA_DIR, newpath))

        self._name2path[name] = newpath
        del self._num2name[oldnum]
        self._num2name[newnum] = name

        # clean up empty directories
        path, fn = os.path.split(oldpath)
        while path != "":
            olddir = os.path.join(self.directory, self.DATA_DIR, path)
            if os.path.exists(olddir) and len(os.listdir(olddir)) == 0:
                os.rmdir(olddir)
            path, fn = os.path.split(path)

    def _evict(self, state, path, n):
        if state["numbytes"] <= self.config["limitbytes"]:
            return

        # eliminate in sort order
        items = os.listdir(path)
        items.sort()

        for fn in items:
            if state["numbytes"] <= self.config["limitbytes"]:
                return

            subpath = os.path.join(path, fn)

            if os.path.isdir(subpath):
                # descend to the next level
                self._evict(state, subpath, (n + int(fn)) * self.config["maxperdir"])

            else:
                # delete each file
                i = fn.index(self.config["delimiter"])
                number = n + int(fn[:i])

                state["lastevict"] = number
                del self._name2path[fn[i + 1:]]
                del self._num2name[number]

                numbytes = os.path.getsize(subpath)
                os.remove(subpath)
                state["numbytes"] -= numbytes

        # clean up empty directories
        if len(os.listdir(path)) == 0:
            os.rmdir(path)

    def _numpath(self, state, name):
        # maybe increase depth
        while state["next"] >= self.config["maxperdir"]**(state["depth"] + 1):
            state["depth"] += 1

            # move the subdirectories/files into a new directory
            tmp = os.path.join(self.directory, self.TMP_DIR)
            assert not os.path.exists(tmp)
            os.mkdir(tmp)
            for fn in os.listdir(os.path.join(self.directory, self.DATA_DIR)):
                os.rename(os.path.join(self.directory, self.DATA_DIR, fn), os.path.join(tmp, fn))

            prefix = self._formatter.format(0)
            os.rename(tmp, os.path.join(self.directory, self.DATA_DIR, prefix))

            # also update the lookup map
            self._addprefix(prefix)

        # create directories in path if necessary
        path = ""
        number = state["next"]
        for d in range(self.depth, 0, -1):
            factor = self.config["maxperdir"]**d

            fn = self._formatter.format(number // factor)
            number = number % factor

            path = os.path.join(path, fn)
            if not os.path.exists(os.path.join(self.directory, self.DATA_DIR, path)):
                os.mkdir(os.path.join(self.directory, self.DATA_DIR, path))

        # return new number and path
        return number, os.path.join(path, self._formatter.format(number) + self.config["delimiter"] + str(name))
