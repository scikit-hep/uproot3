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

import uproot

fragments = {
    # localsource
    "localsource": u"""localsource : function (path \u21d2 :class:`Source <uproot.source.source.Source>`)
        function that will be applied to the path to produce an uproot :class:`Source <uproot.source.source.Source>` object if the path is a local file. Default is :meth:`MemmapSource.defaults <uproot.source.memmap.MemmapSource.defaults>` for memory-mapped files.""",

    # xrootdsource
    "xrootdsource": u"""xrootdsource : function (path \u21d2 :class:`Source <uproot.source.source.Source>`)
        function that will be applied to the path to produce an uproot :class:`Source <uproot.source.source.Source>` object if the path is an XRootD URL. Default is :meth:`XRootDSource.defaults <uproot.source.xrootd.XRootDSource.defaults>` for XRootD with default chunk size/caching. (See :class:`XRootDSource <uproot.source.xrootd.XRootDSource>` constructor for details.)""",
    "options": u"""**options
        passed to :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>` constructor.""",

    # entrystepsize
    "entrystepsize": u"""entrystepsize : positive int
        number of entries to provide in each step of iteration except the last in each file (unless it exactly divides the number of entries in the file).""",

    }

uproot.rootio.open.__doc__ = \
u"""Opens a ROOT file (local or remote), specified by file path.

    Parameters
    ----------
    path : str
        local file path or URL specifying the location of a file (note: not a Python file object!). If the URL schema is "root://", :func:`xrootd <uproot.xrootd>` will be called.

    {localsource}

    {xrootdsource}

    {options}

    Returns
    -------
    :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`
        top-level directory of the ROOT file.

    Notes
    -----
    The ROOTDirectory returned by this function is not necessarily an open file. File handles are managed internally by :class:`Source <uproot.source.source.Source>` objects to permit parallel reading. Although this function can be used in a ``with`` construct (which protects against unclosed files), the ``with`` construct has no meaning when applied to this function. Files will be opened or closed as needed to read data on demand.

    Examples
    --------
    ::

        import uproot
        tfile = uproot.open("/my/root/file.root")
    """.format(**fragments)

# uproot.rootio.xrootd.__doc__ = \
u"""Opens a remote ROOT file with XRootD (if installed).

    Parameters
    ----------
    path : str
        URL specifying the location of a file.

    {xrootdsource}

    {options}

    Returns
    -------
    :class:`ROOTDirectory <uproot.rootio.ROOTDirectory>`
        top-level directory of the ROOT file.
    
    Examples
    --------
    ::

        import uproot
        tfile = uproot.open("root://eos-server.cern/store/file.root")
    """.format(**fragments)

uproot.tree.iterate.__doc__ = \
u"""

    """.format(**fragments)
