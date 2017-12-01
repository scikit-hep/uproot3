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
import math

import numpy

def execute(code):
    env = dict(math.__dict__)
    exec(code, env)
    return env["fcn"]

def string2fcn(string):
    insymbols = set()
    outsymbols = set()

    def recurse(node):
        if isinstance(node, ast.FunctionDef):
            raise TypeError("function definitions are not allowed in a function parsed from a string")

        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                if node.id not in outsymbols:
                    insymbols.add(node.id)
            elif isinstance(node.ctx, ast.Store):
                outsymbols.add(node.id)

        elif isinstance(node, ast.AST):
            for field in node._fields:
                recurse(getattr(node, field))

        elif isinstance(node, list):
            for x in node:
                recurse(x)
        
    body = ast.parse(string).body
    recurse(body)

    if len(body) == 0:
        raise TypeError("string contains no expressions")
    elif isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        body[-1].lineno = body[-1].value.lineno
        body[-1].col_offset = body[-1].value.col_offset

    module = ast.parse("def fcn({0}): pass".format(", ".join(sorted(insymbols))))
    module.body[0].body = body
    return execute(compile(module, string, "exec"))

class FunctionalChain(object):
    def __init__(self, names, arrays, outputtype, reportentries):
        self.names = names
        self.arrays = arrays
        self.outputtype = outputtype
        self.reportentries = reportentries
        self.functions = []

class TTreeMethods_numba(object):
    def __init__(self, tree):
        self._tree = tree

    def iterate(self, function, entrystepsize=100000, branches=None, outputtype=dict, reportentries=False, entrystart=None, entrystop=None, basketcache=None, keycache=None, executor=None):





        import numba

