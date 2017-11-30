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

import threading
import socket

import numpy

class TH1Methods_bokeh(object):
    def __init__(self, hist):
        self._hist = hist

    def fig(self, patch_options={}, fig_options={}, **options):
        import bokeh.plotting
        patch_options = dict(patch_options)
        patch_options.update(dict((n, v) for n, v in options.items() if n.startswith("line") or n.startswith("fill")))

        if "fill_color" not in patch_options and "fill_alpha" not in patch_options:
            patch_options["fill_alpha"] = 0.25

        fig_options = dict(fig_options)
        fig_options.update(dict((n, v) for n, v in options.items() if not n.startswith("line") and not n.startswith("fill")))

        freq, edges = self._hist.numpy
        xs = edges[numpy.repeat(numpy.arange(len(freq) + 1), 2)]
        ys = numpy.empty_like(xs)
        ys[1:-1] = freq[numpy.repeat(numpy.arange(len(freq)), 2)]
        ys[0]    = 0.0
        ys[-1]   = 0.0

        if "x_range" not in fig_options:
            fig_options["x_range"] = (edges[0], edges[-1])

        if "y_range" not in fig_options:
            minimum = min(freq)
            maximum = max(freq)
            diff = maximum - minimum
            if diff == 0:
                minimum -= 0.5
                maximum += 0.5
            else:
                if minimum < 0:
                    minimum -= 0.1*diff
                else:
                    minimum = 0
                maximum += 0.1*diff

            fig_options["y_range"] = (minimum, maximum)

        fig = bokeh.plotting.figure(**fig_options)
        fig.patch(xs, ys, **patch_options)
        return fig

    def plot(self, port=None, hosts=None, patch_options={}, fig_options={}, **options):
        fig = self.fig(patch_options=patch_options, fig_options=fig_options, **options)
        canvas = BokehCanvas(port, hosts)
        canvas(fig)
        return canvas

class BokehCanvas(object):
    _ioloop = None
    _instance = None

    def __new__(cls, port=None, hosts=None):
        if cls._ioloop is None:
            from tornado.ioloop import IOLoop
            cls._ioloop = IOLoop.current()
            def go():
                if not cls._ioloop._running:
                    cls._ioloop.start()
            thread = threading.Thread(target=go)
            thread.daemon = True
            thread.start()

        if cls._instance is None:
            cls._instance = cls._new(port, hosts)

        elif port is not None and port != cls._instance._port:
            if not cls._instance._server._stopped:
                cls._instance._server.stop()
            cls._instance = cls._new(port, hosts)

        elif hosts is not None and hosts != cls._instance._hosts:
            if not cls._instance._server._stopped:
                cls._instance._server.stop()
            cls._instance = cls._new(port, hosts)

        return cls._instance

    @classmethod
    def _new(cls, port, hosts):
        import bokeh
        import bokeh.application
        import bokeh.application.handlers
        import bokeh.server.server
        import bokeh.plotting

        self = object.__new__(cls)

        serveropts = {"io_loop": cls._ioloop}
        if port is None:
            serveropts["port"] = 0
        else:
            serveropts["port"] = port
        if hosts is not None:
            if isinstance(hosts, str):
                hosts = [hosts]
            serveropts["allow_websocket_origin"] = hosts

        self._plot = None
        self._layout = None
        self._doc = None

        def newwindow(doc):
            if self._plot is None:
                self._plot = bokeh.plotting.figure()
                self._plot.patch([], [], line_width=0)
            self._layout = bokeh.layouts.row(self._plot)
            self._plot = None
            doc.add_root(self._layout)
            self._doc = doc

        app = bokeh.application.Application(bokeh.application.handlers.function.FunctionHandler(newwindow))
        self._server = bokeh.server.server.Server({"/": app}, **serveropts)
        self._server.start()
        self._port = port
        self._hosts = hosts
        return self

    def __call__(self, plot):
        if self._doc is None:
            self._plot = plot
        else:
            def update():
                self._layout.children[0] = plot
            self._doc.add_next_tick_callback(update)

    @property
    def address(self):
        if self._hosts is None:
            return "localhost"

        hostname = socket.gethostname()
        if hostname != "localhost":
            return hostname

        ip = socket.gethostbyname(hostname)
        if ip != "127.0.0.1":
            return ip

        try:
            test = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test.connect(("8.8.8.8", 80))   # Google
            return test.getsockname()[0]
        finally:
            test.close()

    @property
    def url(self):
        return "http://{0}:{1}".format(self.address, self.port)

    @property
    def port(self):
        return self._server.port

    def show(self):
        self._server.show("/")
