#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot3/blob/master/LICENSE

from __future__ import absolute_import

import re

__version__ = "3.14.4"
version = __version__
version_info = tuple(re.split(r"[-\.]", __version__))

del re
