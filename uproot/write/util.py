#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from __future__ import absolute_import

import datetime

def datime(when=None):
    if when is None:
        when = datetime.datetime.now()
    return (when.year - 1995) << 26 | when.month << 22 | when.day << 17 | when.hour << 12 | when.minute << 6 | when.second
