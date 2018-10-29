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

import sys
import os
sys.path.insert(0, os.path.abspath('../..'))

import uproot

import subprocess
import json

# Make sure c file is named allstreamers.c
subprocess.run("root -l -q dev/allstreamers.c", shell=True)

f = uproot.open("dev/allstreamers.root")

# Check with json
data = json.load(open("dev/streamerversions.json"))
for x in f._context.streamerinfos:
    if data[x._fName.decode("ascii")] != x._fClassVersion:
        print("Old {0} version = {1}. New {0} version = {2}".format(x._fName, data[x._fName.decode("ascii")], x._fClassVersion))

tkey = uproot.rootio.TKey.read(f._context.source, uproot.source.cursor.Cursor(f._context.tfile["_fSeekInfo"]), None, None)
start = f._context.tfile["_fSeekInfo"] + tkey._fKeylen
streamerlen = tkey._fObjlen

with open("dev/allstreamers.root", "rb") as binary_file:
    binary_file.seek(start)
    couple_bytes = binary_file.read(streamerlen + 1)
streamers = "streamers = {0}".format(repr(couple_bytes))

lines = []
for line in open("uproot/write/streamers.py"):
    if line.startswith("streamers"):
        lines.append(streamers)
    else:
        lines.append(line)

with open("uproot/write/streamers.py", "w") as streamerfile:
    for line in lines:
        streamerfile.writelines(line)

os.remove("dev/allstreamers.root")
