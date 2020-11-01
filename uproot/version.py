#!/usr/bin/env python

# BSD 3-Clause License; see https://github.com/scikit-hep/uproot/blob/master/LICENSE

from __future__ import absolute_import

import re

__version__ = "3.13.0"
version = __version__
version_info = tuple(re.split(r"[-\.]", __version__))

del re
