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
import keyword
import math
import sys
from collections import namedtuple

import numpy

import uproot.tree
import uproot.interp.auto

def ifinstalled(f):
    try:
        import numba
    except ImportError:
        return f
    else:
        return numba.jit()(f)

if sys.version_info[0] <= 2:
    parsable = (unicode, str)
else:
    parsable = (str,)

class ChainStep(object):
    def __init__(self, previous):
        self.previous = previous

    @property
    def source(self):
        return self.previous.source

    def _makefcn(self, code, env, name, source):
        env = dict(env)
        exec(code, env)
        env[name].source = source
        return env[name]

    def _string2fcn(self, string):
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

        names = self._generatenames(["fcn"], insymbols.union(outsymbols))

        module = ast.parse("def {fcn}({args}): pass".format(fcn=names["fcn"], args=", ".join(sorted(insymbols))))
        module.body[0].body = body
        return self._makefcn(compile(module, string, "exec"), math.__dict__, names["fcn"], string)

    def _tofcn(self, expr):
        if isinstance(expr, parsable):
            expr = self._string2fcn(expr)
        return expr, expr.__code__.co_varnames

    def _generatenames(self, want, avoid):
        disambigifier = 0
        out = {}
        for name in want:
            newname = name
            while newname in avoid or newname in out or keyword.iskeyword(newname):
                newname = "{0}_{1}".format(name, disambigifier)
                disambigifier += 1
            out[name] = newname
        return out

    def _tofcns(self, exprs):
        if isinstance(exprs, parsable):
            return [self._tofcn(exprs) + (exprs, exprs)]

        elif callable(exprs) and hasattr(exprs, "__code__"):
            return [self._tofcn(exprs) + (id(exprs), getattr(exprs, "__name__", None))]

        elif isinstance(exprs, dict) and all(isinstance(x, parsable) or (callable(x) and hasattr(x, "__code__")) for x in exprs.values()):
            return [self._tofcn(x) + (x if isinstance(x, parsable) else id(x), n) for n, x in exprs.items()]

        else:
            try:
                assert all(isinstance(x, parsable) or (callable(x) and hasattr(x, "__code__")) for x in exprs)
            except (TypeError, AssertionError):
                raise TypeError("exprs must be a dict of strings or functions, iterable of strings or functions, a single string, or a single function")
            else:
                return [self._tofcn(x) + ((x, x) if isinstance(x, parsable) else (id(x), getattr(x, "__name__", None))) for i, x in enumerate(exprs)]

    def _satisfy(self, requirement, branchnames, entryvars, entryvar, aliases):
        self.previous._satisfy(requirement, branchnames, entryvars, entryvar, aliases)

    def _argfcn(self, requirement, branchnames, entryvar, aliases, compilefcn):
        return self.previous._argfcn(requirement, branchnames, entryvar, aliases, compilefcn)

    def _compilefcns(self, fcns, entryvar, aliases, compilefcn):
        branchnames = []
        entryvars = set()
        for fcn, requirements, cacheid, dictname in fcns:
            for requirement in requirements:
                self._satisfy(requirement, branchnames, entryvars, entryvar, aliases)

        compiled = []
        for fcn, requirements, cacheid, dictname in fcns:
            argstrs = []
            argfcns = []
            env = {"fcn": compilefcn(fcn)}
            for i, requirement in enumerate(requirements):
                argstrs.append("arg{0}(start, stop, arrays)".format(i))
                argfcn = self._argfcn(requirement, branchnames, entryvar, aliases, compilefcn)
                argfcns.append(argfcn)
                env["arg{0}".format(i)] = argfcn

            source = "def cfcn(start, stop, arrays): return fcn({0})".format(", ".join(argstrs))
            compiled.append(compilefcn(self._makefcn(compile(ast.parse(source), str(dictname), "exec"), env, "cfcn", source)))

        return compiled, branchnames, entryvars

    def _isidentifier(self, dictname):
        try:
            x = ast.parse(dictname)
            assert len(x.body) == 1 and isinstance(x.body[0], ast.Expr) and isinstance(x.body[0].value, ast.Name)
        except (SyntaxError, TypeError, AssertionError):
            return False
        else:
            return True

    def _compilefcn(self, numba):
        if callable(numba):
            return numba

        elif numba is None or numba is False:
            return lambda f: f

        elif numba is True:
            import numba as nb
            return lambda f: nb.njit()(f)

        else:
            import numba as nb
            return lambda f: nb.jit(**numba)(f)

    def _iterateapply(self, fcns, compiled, branchnames, entryvars, entrystepsize, entrystart, entrystop, aliases, interpretations, entryvar, outputtype, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
        dictnames = [dictname for fcn, requirements, cacheid, dictname in fcns]
        if outputtype == namedtuple:
            for dictname in dictnames:
                if not self._isidentifier(dictname):
                    raise ValueError("illegal field name for namedtuple: {0}".format(repr(dictname)))
            outputtype = namedtuple("Arrays", dictnames)

        if issubclass(outputtype, dict):
            def finish(results):
                return outputtype(zip(dictnames, results))
        elif outputtype == tuple or outputtype == list:
            def finish(results):
                return outputtype(results)
        else:
            def finish(results):
                return outputtype(*results)

        excinfos = None
        for start, stop, arrays in self.source._iterate(branchnames, len(entryvars) > 0, interpretations, entrystepsize, entrystart, entrystop, cache, basketcache, keycache, readexecutor):
            if excinfos is not None:
                for excinfo in excinfos:
                    _delayedraise(excinfo)
                yield finish(results)

            results = [None] * len(compiled)
            arrays = tuple(arrays)

            def calculate(i):
                try:
                    out = compiled[i](start, stop, arrays)
                except:
                    return sys.exc_info()
                else:
                    results[i] = out
                    return None

            if calcexecutor is None:
                for i in range(len(compiled)):
                    uproot.tree._delayedraise(calculate(i))
                excinfos = ()
            else:
                excinfos = calcexecutor.map(calculate, range(len(compiled)))

        if excinfos is not None:
            for excinfo in excinfos:
                _delayedraise(excinfo)
            yield finish(results)

    def iterate_newarrays(self, exprs, entrystepsize=100000, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        compilefcn = self._compilefcn(numba)

        fcns = []
        for fcn, requirements, cacheid, dictname in self._tofcns(exprs):
            if len(requirements) == 0:
                newfcn = compilefcn(fcn)
            else:
                names = self._generatenames(["afcn", "out", "empty", "dtype", "i", "fcn"] + [req + "_i" for req in requirements], requirements)
                source = """
def {afcn}({params}):
    {out} = {empty}(len({one}), {dtype})
    for {i} in range(len({one})):
        {itemdefs}
        {out}[{i}] = {fcn}({items})
    return {out}
""".format(afcn = names["afcn"],
           params = ", ".join(requirements),
           out = names["out"],
           empty = names["empty"],
           one = requirements[0],
           dtype = names["dtype"],
           i = names["i"],
           itemdefs = "\n        ".join("{0} = {1}[{2}]".format(names[req + "_i"], req, names["i"]) for req in requirements),
           fcn = names["fcn"],
           items = ", ".join(names[req + "_i"] for req in requirements))

                newfcn = self._makefcn(compile(ast.parse(source), dictname, "exec"), {"fcn": compilefcn(fcn), "empty": numpy.empty, "dtype": numpy.dtype(numpy.float64)}, names["afcn"], source)

            fcns.append((newfcn, requirements, cacheid, dictname))
            
        compiled, branchnames, entryvars = self._compilefcns(fcns, entryvar, aliases, compilefcn)
        return self._iterateapply(fcns, compiled, branchnames, entryvars, entrystepsize, entrystart, entrystop, aliases, interpretations, entryvar, outputtype, cache, basketcache, keycache, readexecutor, calcexecutor, numba)
    
    def define(self, exprs={}, **more_exprs):
        return Define(self, exprs, **more_exprs)

class Define(ChainStep):
    def __init__(self, previous, exprs={}, **more_exprs):
        self.previous = previous

        if not isinstance(exprs, dict):
            raise TypeError("exprs must be a dict")
        exprs = dict(exprs)
        exprs.update(more_exprs)

        if any(not isinstance(x, parsable) or not self._isidentifier(x) or keyword.iskeyword(x) for x in exprs):
            raise TypeError("all names in exprs must be identifiers (and strings!)")

        self.fcn = {}
        self.requirements = {}
        for fcn, requirements, cacheid, dictname in self._tofcns(exprs):
            self.fcn[dictname] = fcn
            self.requirements[dictname] = requirements

    def _satisfy(self, requirement, branchnames, entryvars, entryvar, aliases):
        if requirement in self.requirements:
            for req in self.requirements[requirement]:
                self.previous._satisfy(req, branchnames, entryvars, entryvar, aliases)
        else:
            self.previous._satisfy(requirement, branchnames, entryvars, entryvar, aliases)

    def _argfcn(self, requirement, branchnames, entryvar, aliases, compilefcn):
        if requirement in self.requirements:
            env = {"fcn": compilefcn(self.fcn[requirement]), "empty": numpy.empty, "dtype": numpy.dtype(numpy.float64)}
            itemdefs = []
            itemis = []
            for i, req in enumerate(self.requirements[requirement]):
                argfcn = self.previous._argfcn(req, branchnames, entryvar, aliases, compilefcn)
                env["arg{0}".format(i)] = argfcn
                itemdefs.append("item{0} = arg{0}(start, stop, arrays)".format(i))
                itemis.append("item{0}[i]".format(i))

            source = """
def afcn(start, stop, arrays):
    {itemdefs}
    out = empty(stop - start, dtype)
    for i in range(stop - start):
        out[i] = fcn({itemis})
    return out
""".format(itemdefs="\n    ".join(itemdefs), itemis=", ".join(itemis))

            return compilefcn(self._makefcn(compile(ast.parse(source), requirement, "exec"), env, "afcn", source))

        else:
            return self.previous._argfcn(requirement, branchnames, entryvar, aliases, compilefcn)

class ChainSource(ChainStep):
    def __init__(self, tree):
        self.tree = tree

    def _iterate(self, branchnames, hasentryvar, interpretations, entrystepsize, entrystart, entrystop, cache, basketcache, keycache, readexecutor):
        branches = {}
        for branchname in branchnames:
            if branchname in interpretations:
                branches[branchname] = interpretations[branchname]
            else:
                branches[branchname] = uproot.interp.auto.interpret(self.tree[branchname])

        for entrystart, entrystop, arrays in self.tree.iterate(entrystepsize = entrystepsize,
                                                               branches = branches,
                                                               outputtype = list,
                                                               reportentries = True,
                                                               entrystart = entrystart,
                                                               entrystop = entrystop,
                                                               cache = cache,
                                                               basketcache = basketcache,
                                                               keycache = keycache,
                                                               executor = readexecutor,
                                                               blocking = True):
            if hasentryvar:
                arrays.append(numpy.arange(entrystart, entrystop))
            yield entrystart, entrystop, arrays

    @property
    def source(self):
        return self

    def _satisfy(self, requirement, branchnames, entryvars, entryvar, aliases):
        if requirement == entryvar:
            entryvars.add(None)

        else:
            branchname = aliases.get(requirement, requirement)
            try:
                index = branchnames.index(branchname)
            except ValueError:
                index = len(branchnames)
                branchnames.append(branchname)

    def _argfcn(self, requirement, branchnames, entryvar, aliases, compilefcn):
        if requirement == entryvar:
            index = len(branchnames)
        else:
            branchname = aliases.get(requirement, requirement)
            index = branchnames.index(branchname)
        return compilefcn(lambda start, stop, arrays: arrays[index])

class TTreeFunctionalMethods(uproot.tree.TTreeMethods):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.tree.TTreeMethods.__metaclass__,), {})

    def iterate_newarrays(self, exprs, entrystepsize=100000, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainSource(self).iterate_newarrays(exprs, entrystepsize=entrystepsize, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=outputtype, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def newarrays(self):
        raise NotImplementedError

    def newarray(self):
        raise NotImplementedError

    def filter(self):
        raise NotImplementedError

    def aggregate(self):
        raise NotImplementedError

    def hist(self, numbins, low, high, expr):
        raise NotImplementedError

    def define(self, exprs={}, **more_exprs):
        return ChainSource(self).define(exprs, **more_exprs)

    def fork(self):
        raise NotImplementedError

uproot.rootio.methods["TTree"] = TTreeFunctionalMethods
