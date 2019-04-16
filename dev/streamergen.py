#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

# Run this script from the root directory of the project.

import sys
import os
sys.path.insert(0, os.path.abspath(""))

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
    couple_bytes = binary_file.read(streamerlen)
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
