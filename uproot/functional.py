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
import sys
import math
import numbers
from collections import namedtuple

import numpy

import uproot.tree
import uproot.hist
import uproot.interp.auto

def ifinstalled(f):
    try:
        import numba
    except ImportError:
        return f
    else:
        return numba.jit(nogil=True)(f)

if sys.version_info[0] <= 2:
    parsable = (unicode, str)
else:
    parsable = (str,)

stringenv = dict(list(math.__dict__.items()) + list({
    "min": min,
    "max": max,
    "round": round,
    }.items()))

class ChainStep(object):
    NEW_ARRAY_DTYPE = numpy.dtype(numpy.float64)

    def __init__(self, previous):
        self.previous = previous

    def define(self, **exprs):
        return Define(self, exprs)

    def intermediate(self, cache=None, **exprs):
        return Intermediate._create(self, cache, exprs)

    def filter(self, expr):
        return Filter(self, expr)

    @property
    def source(self):
        return self.previous.source

    @property
    def tree(self):
        return self.previous.tree

    @staticmethod
    def _makefcn(code, env, name, source):
        env = dict(env)
        exec(code, env)
        env[name].source = source
        return env[name]

    @staticmethod
    def _generatenames(want, avoid=set()):
        disambigifier = 0
        out = {}
        for name in want:
            if ChainStep._isidentifier(name):
                newname = name
            else:
                newname = "tmp"
            while newname in avoid or newname in out or keyword.iskeyword(newname):
                newname = "{0}_{1}".format(name, disambigifier)
                disambigifier += 1
            out[name] = newname
        return out

    @staticmethod
    def _string2fcn(string):
        insymbols = []
        outsymbols = set()

        def recurse(node):
            if isinstance(node, ast.FunctionDef):
                raise TypeError("function definitions are not allowed in a function parsed from a string")

            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    if node.id not in outsymbols and node.id not in stringenv:
                        insymbols.append(node.id)
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

        names = ChainStep._generatenames(["fcn"], set(insymbols).union(outsymbols))

        module = ast.parse("def {fcn}({args}): pass".format(fcn=names["fcn"], args=", ".join(insymbols)))
        module.body[0].body = body
        return ChainStep._makefcn(compile(module, string, "exec"), stringenv, names["fcn"], string)

    @staticmethod
    def _isfcn(expr):
        return isinstance(expr, parsable) or (callable(expr) and hasattr(expr, "__code__"))

    @staticmethod
    def _tofcn(expr):
        identifier = None
        if isinstance(expr, parsable):
            if ChainStep._isidentifier(expr):
                identifier = expr
            expr = ChainStep._string2fcn(expr)

        return expr, ChainStep._params(expr), identifier

    @staticmethod
    def _params(fcn):
        return fcn.__code__.co_varnames[:fcn.__code__.co_argcount]

    @staticmethod
    def _tofcns(exprs):
        used = {}
        def getname(fcn):
            trial = getattr(fcn, "__name__", "<lambda>")
            if trial == "<lambda>":
                trial = "fcn"
                if "fcn" not in used:
                    used["fcn"] = 1
            out = trial
            while out in used:
                out = "{0}_{1}".format(trial, used[trial])
                used[trial] += 1
            if trial not in used:
                used[trial] = 2
            return out

        if isinstance(exprs, parsable):
            return [ChainStep._tofcn(exprs) + (exprs, exprs)]

        elif callable(exprs) and hasattr(exprs, "__code__"):
            return [ChainStep._tofcn(exprs) + (id(exprs), getname(exprs))]

        elif isinstance(exprs, dict) and all(ChainStep._isfcn(x) for x in exprs.values()):
            return [ChainStep._tofcn(x) + (x if isinstance(x, parsable) else id(x), n) for n, x in exprs.items()]

        else:
            try:
                assert all(ChainStep._isfcn(x) for x in exprs)
            except (TypeError, AssertionError):
                raise TypeError("exprs must be a dict of strings or functions, an iterable of strings or functions, a single string, or a single function")
            else:
                return [ChainStep._tofcn(x) + ((x, x) if isinstance(x, parsable) else (id(x), getname(x))) for i, x in enumerate(exprs)]

    @staticmethod
    def _isidentifier(dictname):
        try:
            assert not keyword.iskeyword(dictname)
            x = ast.parse(dictname)
            assert len(x.body) == 1 and isinstance(x.body[0], ast.Expr) and isinstance(x.body[0].value, ast.Name)
        except (SyntaxError, TypeError, AssertionError):
            return False
        else:
            return True

    @staticmethod
    def _compilefcn(numba):
        if callable(numba):
            return numba

        elif numba is None or numba is False:
            return lambda f: f

        elif numba is True:
            import numba as nb
            return lambda f: nb.njit(nogil=True)(f)

        else:
            import numba as nb
            return lambda f: nb.jit(**numba)(f)

    def _prepare(self, exprs, aliases, entryvar, numba):
        compilefcn = self._compilefcn(numba)

        dictnames = []
        nonidentifiers = []
        toresolve = []
        for fcn, requirements, identifier, cacheid, dictname in self._tofcns(exprs):
            dictnames.append(dictname)
            if identifier is None:
                nonidentifiers.append((fcn, requirements, identifier, cacheid, dictname))
                toresolve.append(dictname)
            else:
                toresolve.append(identifier)

        tmpnode = Intermediate(self, None, nonidentifiers)

        # find all the dependencies and put unique ones in lists
        sourcenames = []
        intermediates = []
        entryvars = set()
        for name in toresolve:
            tmpnode._satisfy(name, sourcenames, intermediates, entryvars, entryvar, aliases)

        # reorder the (Intermediate, name) pairs in order of increasing dependency (across all expressions)
        intermediates = Intermediate._dependencyorder(sourcenames, intermediates, entryvar, aliases)

        # now compile them, using the established "sourcenames" and "intermediates" order to get arguments by tuple index (hard-compiled into functions)
        fcncache = {}
        compiled = []
        for name in toresolve:
            compiled.append(tmpnode._argfcn(name, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache))

        # compile the intermediates in the same way
        compiledintermediates = [intermediate._compileintermediate(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache) for intermediate, requirement in intermediates]

        return tmpnode, dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, compilefcn

    def _wouldsatisfy(self, requirement, entryvar, aliases):
        return self.previous._wouldsatisfy(requirement, entryvar, aliases)

    def _satisfy(self, requirement, sourcenames, intermediates, entryvars, entryvar, aliases):
        self.previous._satisfy(requirement, sourcenames, intermediates, entryvars, entryvar, aliases)

    def _argfcn(self, requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache):
        return self.previous._argfcn(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)

    def _chain(self, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, numba):
        return self.previous._chain(sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, numba)

    def _endchain(self, compiled, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
        waits = self.source._chain(sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, numba)

        def calculate(wait):
            try:
                start, stop, numentries, arrays = wait()

                for compiledintermediate in compiledintermediates:
                    compiledintermediate(arrays)

                out = start, stop, numentries, [x(arrays) for x in compiled]

            except:
                return sys.exc_info(), None
            else:
                return None, out

        if calcexecutor is None:
            for wait in waits:
                excinfo, result = calculate(wait)
                uproot.tree._delayedraise(excinfo)
                yield result

        else:
            for excinfo, result in calcexecutor.map(calculate, waits):
                uproot.tree._delayedraise(excinfo)
                yield result
            
    def iterate_newarrays(self, exprs, entrysteps=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, reportentries=False, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        tmpnode, dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, compilefcn = self._prepare(exprs, aliases, entryvar, numba)

        if outputtype == namedtuple:
            for dictname in dictnames:
                if not self._isidentifier(dictname):
                    raise ValueError("illegal field name for namedtuple: {0}".format(repr(dictname)))
            outputtype = namedtuple("Arrays", dictnames)

        if issubclass(outputtype, dict):
            def finish(arrays):
                return outputtype(zip(dictnames, arrays))
        elif outputtype == tuple or outputtype == list:
            def finish(arrays):
                return outputtype(arrays)
        else:
            def finish(arrays):
                return outputtype(*arrays)

        for start, stop, numentries, arrays in tmpnode._endchain(compiled, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
            if reportentries:
                yield start, stop, numentries, finish(arrays)
            else:
                yield finish(arrays)

    def newarrays(self, exprs, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        tmpnode, dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, compilefcn = self._prepare(exprs, aliases, entryvar, numba)

        if outputtype == namedtuple:
            for dictname in dictnames:
                if not self._isidentifier(dictname):
                    raise ValueError("illegal field name for namedtuple: {0}".format(repr(dictname)))
            outputtype = namedtuple("Arrays", dictnames)

        partitions = []
        totalentries = 0
        for start, stop, numentries, arrays in tmpnode._endchain(compiled, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, None, entrystart, entrystop, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
            assert len(dictnames) == len(arrays)
            if len(arrays) > 0:
                for array in arrays:
                    assert numentries == len(array)

            partitions.append((totalentries, totalentries + numentries, arrays))
            totalentries += numentries

        if len(partitions) == 0:
            outarrays = [numpy.empty(0, dtype=self.NEW_ARRAY_DTYPE) for i in range(len(dictnames))]
        else:
            outarrays = [numpy.empty(totalentries, dtype=array.dtype) for array in partitions[0][2]]

        for start, stop, arrays in partitions:
            for outarray, array in zip(outarrays, arrays):
                outarray[start:stop] = array
            
        if issubclass(outputtype, dict):
            return outputtype(zip(dictnames, outarrays))
        elif outputtype == tuple or outputtype == list:
            return outputtype(outarrays)
        else:
            return outputtype(*outarrays)

    def newarray(self, expr, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        if not ChainStep._isfcn(expr):
            raise TypeError("expr must be a single string or function")

        return self.newarrays(expr, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=tuple, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)[0]

    def _normalize_reduceargs(self, identity, increment, combine):
        if isinstance(identity, parsable):
            identity = self._string2fcn(identity)
        if isinstance(increment, parsable):
            increment = self._string2fcn(increment)
        if isinstance(combine, parsable):
            combine = self._string2fcn(combine)

        if self._isfcn(identity) and self._isfcn(increment) and (combine is None or self._isfcn(combine)):
            if len(self._params(increment)) == 0:
                raise TypeError("increment function must have at least one parameter")

            if combine is None:
                combine = lambda x, y: x + y

            monoidvar = self._params(increment)[0]
            identity  = {monoidvar: identity}
            increment = {monoidvar: increment}
            combine   = {monoidvar: combine}
            order     = [monoidvar]

        if isinstance(increment, dict):
            if not isinstance(identity, dict):
                raise TypeError("if increment is a dict of functions, identity must be as well (to match up argument lists)")
            if not combine is None and not isinstance(combine, dict):
                raise TypeError("if increment is a dict of functions, combine must be as well (to match up argument lists)")

            if len(increment) == 0 or not all(self._isfcn(x) for n, x in increment.items()):
                raise TypeError("increment must be a (non-empty) dict of strings or functions, a (non-empty) iterable of strings or functions, a single string, or a single function")
            increment = dict((n, string2fcn(x) if isinstance(x, parsable) else x) for n, x in increment.items())
            if increment == dict:
                order = sorted(increment)
            else:
                order = list(increment)   # may be an OrderedDict; preserve whatever order it has
        else:
            try:
                assert len(increment) > 0 and all(self._isfcn(x) for x in increment)
            except (TypeError, AssertionError):
                raise TypeError("increment must be a (non-empty) dict of strings or functions, a (non-empty) iterable of strings or functions, a single string, or a single function")
            else:
                # define as a list first so that we get the order
                increment = [string2fcn(x) if isinstance(x, parsable) else x for x in increment]
                order = []
                for x in increment:
                    params = self._params(x)
                    if len(params) == 0:
                        raise TypeError("increment functions must have at least one argument (the aggregator)")
                    order.append(params[0])
                if len(order) != len(set(order)):
                    raise TypeError("if providing a list of increment functions, the aggregator (first argument) of each must be distinct")
                # redefine as a dict
                increment = dict(zip(order, increment))

        if isinstance(identity, dict):
            if not all(self._isfcn(x) for n, x in identity.items()):
                raise TypeError("identity must be a (non-empty) dict of strings or functions, a (non-empty) iterable of strings or functions, a single string, or a single function")
            identity = dict((n, string2fcn(x) if isinstance(x, parsable) else x) for n, x in identity.items())
        else:
            try:
                assert all(self._isfcn(x) for x in identity)
            except (TypeError, AssertionError):
                raise TypeError("identity must be a (non-empty) dict of strings or functions, a (non-empty) iterable of strings or functions, a single string, or a single function")
            else:
                identity = dict(zip(order, [string2fcn(x) if isinstance(x, parsable) else x for x in identity]))

        if not all(len(self._params(x)) == 0 for x in identity.values()):
            raise TypeError("identity functions must have zero arguments")

        if combine is None:
            combine = dict((n, lambda x, y: x + y) for n in order)
        elif isinstance(combine, dict):
            if not all(self._isfcn(x) for n, x in combine.items()):
                raise TypeError("combine must be None, a (non-empty) dict of strings or functions, a (non-empty) iterable of strings or functions, a single string, or a single function")
            combine = dict((n, string2fcn(x) if isinstance(x, parsable) else x) for n, x in combine.items())
        else:
            try:
                assert all(self._isfcn(x) for x in combine)
            except (TypeError, AssertionError):
                raise TypeError("combine must be None, a (non-empty) dict of strings or functions, a (non-empty) iterable of strings or functions, a single string, or a single function")
            else:
                combine = dict(zip(order, [string2fcn(x) if isinstance(x, parsable) else x for x in combine]))
        if not all(len(self._params(x)) == 2 for x in combine.values()):
            raise TypeError("combine functions must have two arguments")

        monoidvars = dict((n, self._params(x)[0]) for n, x in increment.items())

        if not set(identity.keys()) == set(increment.keys()) == set(combine.keys()):
            raise TypeError("if identity, increment, and combine are provided as dicts, they must have the same set of keys (to match up argument lists)")

        return identity, increment, combine, order, monoidvars

    def _finishreduce(self, rfcn, identity, combine, order, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrystart, entrystop, outputtype, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
        if outputtype == namedtuple:
            for name in order:
                if not self._isidentifier(name):
                    raise ValueError("illegal field name for namedtuple: {0}".format(repr(name)))
            outputtype = namedtuple("Reduced", order)

        waits = self._chain(sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, None, entrystart, entrystop, cache, basketcache, keycache, readexecutor, numba)

        results = [[None for j in range(len(order))] for i in range(len(waits))]

        def calculate(i):
            try:
                start, stop, numentries, arrays = waits[i]()

                for compiledintermediate in compiledintermediates:
                    compiledintermediate(arrays)

                inmonoids  = [identity[n]() for n in order]

                outmonoids = rfcn(arrays, numentries, *inmonoids)

                for j, monoid in enumerate(outmonoids):
                    results[i][j] = monoid

            except:
                return sys.exc_info()
            else:
                return None

        if calcexecutor is None:
            for i in range(len(waits)):
                uproot.tree._delayedraise(calculate(i))
        else:
            excinfos = calcexecutor.map(calculate, range(len(waits)))
            for excinfo in excinfos:
                uproot.tree._delayedraise(excinfo)

        # MAYBEFIXME: could combine in O(log_2(N)) steps rather than O(N) if combining is ever resource-heavy
        for i in range(1, len(waits)):
            for j in range(len(order)):
                results[0][j] = combine[order[j]](results[0][j], results[i][j])

        if issubclass(outputtype, dict):
            return outputtype(zip(order, results[0]))
        elif outputtype == tuple or outputtype == list:
            return outputtype(results[0])
        else:
            return outputtype(*results[0])

    def reduceall(self, identity, increment, combine=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        identity, increment, combine, order, monoidvars = self._normalize_reduceargs(identity, increment, combine)

        compilefcn = self._compilefcn(numba)

        dependencies = []
        for n in order:
            dependencies.extend(self._params(increment[n])[1:])

        # normal preparations for calculating dependencies
        sourcenames = []
        intermediates = []
        entryvars = set()
        fcncache = {}
        for name in dependencies:
            self._satisfy(name, sourcenames, intermediates, entryvars, entryvar, aliases)

        intermediates = Intermediate._dependencyorder(sourcenames, intermediates, entryvar, aliases)
        compiledintermediates = [intermediate._compileintermediate(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache) for intermediate, requirement in intermediates]

        # dependencies are unique strings
        avoid = set(dependencies)

        # unique names for dependency getters
        getternames = self._generatenames(dependencies, avoid)
        avoid = avoid.union(getternames.values())

        # unique names for dependency items
        itemnames = self._generatenames(dependencies, avoid)
        avoid = avoid.union(itemnames.values())

        # unique names for monoids
        monoidnames = self._generatenames(monoidvars.values(), avoid)
        avoid = avoid.union(monoidnames.values())

        # unique names for increment functions
        incnames = self._generatenames(increment, avoid)
        avoid = avoid.union(incnames.values())

        # unique names for builtins and dummy variables
        builtins = self._generatenames(["rfcn", "arrays", "numentries", "i", "range"], avoid)
        avoid = avoid.union(builtins.values())

        env = dict([("range", range)] + [(incnames[n], compilefcn(x)) for n, x in increment.items()])

        # getter -> item for each dependency
        itemdefs = []
        for n in dependencies:
            argfcn = self._argfcn(n, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)
            env[getternames[n]] = argfcn
            itemdefs.append("{0} = {1}({2})[{3}]".format(itemnames[n], getternames[n], builtins["arrays"], builtins["i"]))

        # call each increment function on its parameters (per item), in declaration or sorted order (not that it matters)
        incfcns = ["{0} = {1}({0}{2})".format(monoidnames[monoidvars[n]], incnames[n], "".join(", " + itemnames[x] for x in self._params(increment[n])[1:])) for n in order]

        # input parameters and output tuple
        monoidargs = [monoidnames[monoidvars[n]] for n in order]

        source = """
def {rfcn}({arrays}, {numentries}, {monoidargs}):
    for {i} in {range}({numentries}):
        {itemdefs}
        {incfcns}
    return ({monoidargs},)
""".format(rfcn=builtins["rfcn"], arrays=builtins["arrays"], numentries=builtins["numentries"], monoidargs=", ".join(monoidargs), i=builtins["i"], range=builtins["range"], itemdefs="\n        ".join(itemdefs), incfcns="\n        ".join(incfcns))

        rfcn = compilefcn(self._makefcn(compile(ast.parse(source), "<reduce>", "exec"), env, builtins["rfcn"], source))

        return self._finishreduce(rfcn, identity, combine, order, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrystart, entrystop, outputtype, cache, basketcache, keycache, readexecutor, calcexecutor, numba)

    def reduce(self, identity, increment, combine=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        if not self._isfcn(identity):
            raise TypeError("identity must be a string or a function")
        if not self._isfcn(increment):
            raise TypeError("increment must be a string or a function")
        if not (combine is None or self._isfcn(combine)):
            raise TypeError("combine must be None, a string, or a function")
        return self.reduceall(identity, increment, combine=combine, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=tuple, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)[0]

    def hists(self, specs, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        identity = {}
        datarule = {}
        weightrule = {}
        combine = {}
        monoidvars = {}
        order = []

        def handle(spec, defaultname):
            if not 4 <= len(spec) <= 7:
                raise ValueError("histogram specifications must have 4-7 arguments (inclusive):\n\n    (numbins, low, high, dataexpr[, weightexpr[, name[, title]]])")
            numbins, low, high, dataexpr = spec[:4]
            weightexpr = spec[4] if len(spec) > 4 else None
            name       = spec[5] if len(spec) > 5 else defaultname
            title      = spec[6] if len(spec) > 6 else None

            if not isinstance(numbins, numbers.Integral) or numbins <= 0:
                raise TypeError("numbins must be a positive integer, not {0}".format(repr(numbins)))
            if not isinstance(low, numbers.Real):
                raise TypeError("low must be a number, not {0}".format(repr(low)))
            if not isinstance(high, numbers.Real):
                raise TypeError("high must be a number, not {0}".format(repr(high)))
            if low >= high:
                raise TypeError("low must be less than high, but low={0} and high={1}".format(low, high))
            if not self._isfcn(dataexpr):
                raise TypeError("dataexpr must be a function, not {0}".format(repr(dataexpr)))
            elif isinstance(dataexpr, parsable):
                dataexpr = self._string2fcn(dataexpr)
            if weightexpr is not None and not self._isfcn(weightexpr):
                raise TypeError("weightexpr must be a function, not {0}".format(repr(weightexpr)))
            elif isinstance(weightexpr, parsable):
                weightexpr = self._string2fcn(weightexpr)

            identity[defaultname]   = lambda: uproot.hist(numbins, low, high, name=name, title=title)
            datarule[defaultname]   = dataexpr
            weightrule[defaultname] = weightexpr
            combine[defaultname]    = lambda x, y: x + y
            monoidvars[defaultname] = self._generatenames([defaultname], avoid=monoidvars.values())[defaultname]
            order.append(defaultname)

        if isinstance(specs, dict):
            for defaultname, spec in specs.items():
                handle(spec, defaultname)
        else:
            try:
                iter(specs)
            except TypeError:
                raise TypeError("specs must be a list of\n\n    (numbins, low, high, dataexpr[, weightexpr[, name[, title]]])\n\nor a dict from names to such specifications")
            else:
                for i, spec in enumerate(specs):
                    handle(spec, "h{0}".format(i + 1))

        if outputtype == namedtuple:
            for name in order:
                if not self._isidentifier(name):
                    raise ValueError("illegal field name for namedtuple: {0}".format(repr(name)))
            outputtype = namedtuple("Reduced", order)

        compilefcn = self._compilefcn(numba)

        dependencies = []
        for n in order:
            dependencies.extend(self._params(datarule[n]))
            if weightrule[n] is not None:
                dependencies.extend(self._params(weightrule[n]))

        # normal preparations for calculating dependencies
        sourcenames = []
        intermediates = []
        entryvars = set()
        fcncache = {}
        for name in dependencies:
            self._satisfy(name, sourcenames, intermediates, entryvars, entryvar, aliases)

        intermediates = Intermediate._dependencyorder(sourcenames, intermediates, entryvar, aliases)
        compiledintermediates = [intermediate._compileintermediate(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache) for intermediate, requirement in intermediates]

        # dependencies are unique strings
        avoid = set(dependencies)

        # unique names for dependency getters
        getternames = self._generatenames(dependencies, avoid)
        avoid = avoid.union(getternames.values())

        # unique names for dependency items
        itemnames = self._generatenames(dependencies, avoid)
        avoid = avoid.union(itemnames.values())

        # unique names for monoids
        monoidnames = self._generatenames(monoidvars.values(), avoid)
        avoid = avoid.union(monoidnames.values())

        # unique names for datarules
        datanames = self._generatenames(datarule, avoid)
        avoid = avoid.union(datanames.values())

        # unique names for weightrules
        weightnames = self._generatenames([n for n, x in weightrule.items() if x is not None], avoid)
        avoid = avoid.union(weightnames.values())

        # unique names for builtins and dummy variables
        builtins = self._generatenames(["rfcn", "arrays", "numentries", "i", "range"], avoid)
        avoid = avoid.union(builtins.values())

        env = dict([("range", range)])

        # getter -> item for each dependency
        itemdefs = []
        for n in dependencies:
            argfcn = self._argfcn(n, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)
            env[getternames[n]] = argfcn
            itemdefs.append("{0} = {1}({2})[{3}]".format(itemnames[n], getternames[n], builtins["arrays"], builtins["i"]))

        # call each increment function on its parameters (per item), in declaration or sorted order (not that it matters)
        incfcns = []
        for n in order:
            dataasarg = "{0}({1})".format(datanames[n], ", ".join(itemnames[x] for x in self._params(datarule[n])))
            env[datanames[n]] = compilefcn(datarule[n])
            if weightrule[n] is None:
                incfcns.append("{0}.fill({1})".format(monoidnames[monoidvars[n]], dataasarg))
            else:
                weightasarg = "{0}({1})".format(weightnames[n], ", ".join(itemnames[x] for x in self._params(weightrule[n])))
                env[weightnames[n]] = compilefcn(weightrule[n])
                incfcns.append("{0}.fillw({1}, {2})".format(monoidnames[monoidvars[n]], dataasarg, weightasarg))

        # input parameters and output tuple
        monoidargs = [monoidnames[monoidvars[n]] for n in order]

        source = """
def {rfcn}({arrays}, {numentries}, {monoidargs}):
    for {i} in {range}({numentries}):
        {itemdefs}
        {incfcns}
    return ({monoidargs},)
""".format(rfcn=builtins["rfcn"], arrays=builtins["arrays"], numentries=builtins["numentries"], monoidargs=", ".join(monoidargs), i=builtins["i"], range=builtins["range"], itemdefs="\n        ".join(itemdefs), incfcns="\n        ".join(incfcns))

        rfcn = compilefcn(self._makefcn(compile(ast.parse(source), "<reduce>", "exec"), env, builtins["rfcn"], source))

        return self._finishreduce(rfcn, identity, combine, order, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrystart, entrystop, outputtype, cache, basketcache, keycache, readexecutor, calcexecutor, numba)

    def hist(self, numbins, low, high, dataexpr, weightexpr=None, name=None, title=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return self.hists([(numbins, low, high, dataexpr, weightexpr, name, title)], entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=tuple, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)[0]

class Define(ChainStep):
    def __init__(self, previous, exprs):
        self.previous = previous

        self.fcn = {}
        self.requirements = {}
        self.order = []
        for fcn, requirements, identifier, cacheid, dictname in self._tofcns(exprs):
            self.fcn[dictname] = fcn
            self.requirements[dictname] = requirements
            self.order.append(dictname)

    def _wouldsatisfy(self, requirement, entryvar, aliases):
        if requirement in self.fcn:
            return self
        else:
            return self.previous._wouldsatisfy(requirement, entryvar, aliases)

    def _satisfy(self, requirement, sourcenames, intermediates, entryvars, entryvar, aliases):
        if requirement in self.fcn:
            if (self, requirement) not in intermediates:
                intermediates.append((self, requirement))

            for req in self.requirements[requirement]:
                self.previous._satisfy(req, sourcenames, intermediates, entryvars, entryvar, aliases)

        else:
            self.previous._satisfy(requirement, sourcenames, intermediates, entryvars, entryvar, aliases)

    def _argfcn(self, requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache):
        if requirement in self.fcn:
            env = {"fcn": compilefcn(self.fcn[requirement])}
            args = []
            for i, req in enumerate(self.requirements[requirement]):
                argfcn = self.previous._argfcn(req, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)
                env["arg{0}".format(i)] = argfcn
                args.append("arg{0}(arrays)".format(i))

            source = """
def afcn(arrays):
    return fcn({args})
""".format(args=", ".join(args))

            key = (id(self),)
            if key not in fcncache:
                fcncache[key] = compilefcn(self._makefcn(compile(ast.parse(source), requirement, "exec"), env, "afcn", source))
            return fcncache[key]

        else:
            return self.previous._argfcn(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)

class Intermediate(ChainStep):
    @staticmethod
    def _create(previous, cache, exprs):
        out = Intermediate(previous, cache, Intermediate._tofcns(exprs))

        if any(not isinstance(x, parsable) or not out._isidentifier(x) for x in exprs):
            raise TypeError("all names in exprs must be identifiers")

        return out

    def __init__(self, previous, cache, fcns):
        self.previous = previous
        self.cache = cache

        if self.cache is not None:
            raise NotImplementedError("intermediates will have a cache someday")

        self.fcn = {}
        self.requirements = {}
        self.order = []
        for fcn, requirements, identifier, cacheid, dictname in fcns:
            self.fcn[dictname] = fcn
            self.requirements[dictname] = requirements
            self.order.append(dictname)

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    def _wouldsatisfy(self, requirement, entryvar, aliases):
        if requirement in self.fcn:
            return self
        else:
            return self.previous._wouldsatisfy(requirement, entryvar, aliases)

    def _satisfy(self, requirement, sourcenames, intermediates, entryvars, entryvar, aliases):
        if requirement in self.fcn:
            if (self, requirement) not in intermediates:
                intermediates.append((self, requirement))
                
            for req in self.requirements[requirement]:
                self.previous._satisfy(req, sourcenames, intermediates, entryvars, entryvar, aliases)

        else:
            self.previous._satisfy(requirement, sourcenames, intermediates, entryvars, entryvar, aliases)

    @staticmethod
    def _dependencyorder(sourcenames, intermediates, entryvar, aliases):
        # https://stackoverflow.com/a/11564769/1623645
        def topological_sort(items):
            provided = set()
            while len(items) > 0:
                remaining_items = []
                emitted = False

                for item, dependencies in items:
                    if dependencies.issubset(provided):
                        yield item
                        provided.add(item)
                        emitted = True
                    else:
                        remaining_items.append((item, dependencies))

                if not emitted:
                    raise ValueError("could not sort intermediates in dependency order")

                items = remaining_items

        def dependencies(intermediate, names):
            out = set()
            for name in intermediate.requirements[names]:
                if name == entryvar or aliases.get(name, name) in sourcenames:
                    pass   # provided by source
                else:
                    node = intermediate.previous
                    while not isinstance(node, (Intermediate, Define)) or name not in node.fcn:
                        node = node.previous
                    out.add((node, name))
            return out
        
        preprocessed = [((intermediate, name), dependencies(intermediate, name)) for intermediate, name in intermediates]
        sorted = topological_sort(preprocessed)
        return [(intermediate, name) for intermediate, name in sorted if isinstance(intermediate, Intermediate)]

    def _argfcn(self, requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache):
        if requirement in self.fcn:
            index = len(sourcenames) + intermediates.index((self, requirement))
            if index not in fcncache:
                fcncache[index] = compilefcn(lambda arrays: arrays[index])
            return fcncache[index]

        else:
            return self.previous._argfcn(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)

    def _compileintermediate(self, requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache):
        env = {"fcn": compilefcn(self.fcn[requirement]), "getout": self._argfcn(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)}

        itemdefs = []
        itemis = []
        for i, req in enumerate(self.requirements[requirement]):
            argfcn = self.previous._argfcn(req, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)
            env["arg{0}".format(i)] = argfcn
            itemdefs.append("item{0} = arg{0}(arrays)".format(i))
            itemis.append("item{0}[i]".format(i))

        source = """
def afcn(arrays):
    {itemdefs}
    out = getout(arrays)
    for i in range(len(out)):
        out[i] = fcn({itemis})
    return out
""".format(itemdefs="\n    ".join(itemdefs), itemis=", ".join(itemis))

        if self.cache is not None:
            raise NotImplementedError("intermediates will have a cache someday")

        return compilefcn(self._makefcn(compile(ast.parse(source), requirement, "exec"), env, "afcn", source))

class Filter(ChainStep):
    def __init__(self, previous, expr):
        if not ChainStep._isfcn(expr):
            raise TypeError("expr must be a single string or function")

        self.previous = previous
        self.fcn, self.requirements, identifier = self._tofcn(expr)

    @property
    def source(self):
        return self

    def _wouldsatisfy(self, requirement, entryvar, aliases):
        if self.previous._wouldsatisfy(requirement, entryvar, aliases) is None:
            return None
        else:
            return self

    def _satisfy(self, requirement, sourcenames, intermediates, entryvars, entryvar, aliases):
        what = self.previous._wouldsatisfy(requirement, entryvar, aliases)
        if isinstance(what, Define):
            return what._satisfy(requirement, sourcenames, intermediates, entryvars, entryvar, aliases)
        else:
            sourcenames.append(requirement)

    def _argfcn(self, requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache):
        what = self.previous._wouldsatisfy(requirement, entryvar, aliases)
        if isinstance(what, Define):
            return what._argfcn(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)

        else:
            index = sourcenames.index(requirement)
            if index not in fcncache:
                fcncache[index] = compilefcn(lambda arrays: arrays[index])
            return fcncache[index]

    def _chain(self, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, numba):
        requests = sourcenames + [x for x in self.requirements if x not in sourcenames and not isinstance(self.previous._wouldsatisfy(x, entryvar, aliases), Define)]

        tmpnode, prevdictnames, prevcompiled, prevsourcenames, previntermediates, prevcompiledintermediates, preventryvars, compilefcn = self.previous._prepare(requests, aliases, entryvar, numba)
        maskindex = len(prevsourcenames) + len(prevcompiledintermediates) + len(preventryvars)

        env = {"fcn": compilefcn(self.fcn), "getmask": compilefcn(lambda arrays: arrays[maskindex])}

        itemdefs = []
        itemis = []
        prevfcncache = {}
        for i, req in enumerate(self.requirements):
            argfcn = tmpnode._argfcn(req, prevsourcenames, previntermediates, entryvar, aliases, compilefcn, prevfcncache)
            env["arg{0}".format(i)] = argfcn
            itemdefs.append("item{0} = arg{0}(arrays)".format(i))
            itemis.append("item{0}[i]".format(i))

        source = """
def afcn(arrays):
    {itemdefs}
    mask = getmask(arrays)
    for i in range(len(mask)):
        mask[i] = fcn({itemis})
""".format(itemdefs="\n    ".join(itemdefs), itemis=", ".join(itemis))

        afcn = compilefcn(self._makefcn(compile(ast.parse(source), "<filter>", "exec"), env, "afcn", source))

        waits = tmpnode._chain(prevsourcenames, prevcompiledintermediates, preventryvars, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, numba)

        prevsources = prevsourcenames + [req for node, req in previntermediates]

        def calculate(wait):
            start, stop, numentries, arrays = wait()

            # calculate upstream intermediates
            for prevcompiledintermediate in prevcompiledintermediates:
                prevcompiledintermediate(arrays)

            # add the mask array
            mask = numpy.empty(numentries, dtype=numpy.bool)

            # evaluate the expression and fill the mask
            afcn(arrays + (mask,))

            # apply the mask only to the sourcename arrays
            # cutarrays = [array[mask] for array in arrays[:len(sourcenames)]]
            cutarrays = [arrays[prevsources.index(name)][mask] for name in sourcenames]
            cutnumentries = mask.sum()

            for i in range(len(compiledintermediates)):
                # for Intermediates that will be made *after* the filter
                cutarrays.append(numpy.empty(cutnumentries, dtype=self.NEW_ARRAY_DTYPE))

            if len(entryvars) > 0:
                # same array, but putting it in the canonical position
                cutarrays.append(cutarrays[sourcenames.index(entryvar)])

            return start, stop, cutnumentries, tuple(cutarrays)

        def wrap_for_python_scope(wait):
            return lambda: calculate(wait)

        return [wrap_for_python_scope(wait) for wait in waits]

class ChainOrigin(ChainStep):
    def __init__(self, tree):
        self._tree = tree

    @property
    def source(self):
        return self

    @property
    def tree(self):
        return self._tree

    def _wouldsatisfy(self, requirement, entryvar, aliases):
        if requirement == entryvar:
            return self

        else:
            branchname = aliases.get(requirement, requirement)
            if branchname in self.tree:
                return self
            else:
                return None

    def _satisfy(self, requirement, sourcenames, intermediates, entryvars, entryvar, aliases):
        if requirement == entryvar:
            entryvars.add(None)

        else:
            branchname = aliases.get(requirement, requirement)
            self.tree[branchname]  # raise KeyError if not available
            if branchname not in sourcenames:
                sourcenames.append(branchname)
                
    def _argfcn(self, requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache):
        if requirement == entryvar:
            index = len(sourcenames) + len(intermediates)
        else:
            branchname = aliases.get(requirement, requirement)
            index = sourcenames.index(branchname)

        if index not in fcncache:
            fcncache[index] = compilefcn(lambda arrays: arrays[index])
        return fcncache[index]

    def _chain(self, sourcenames, compiledintermediates, entryvars, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, numba):
        branches = uproot.tree.OrderedDict()
        for branchname in sourcenames:
            if branchname in interpretations:
                branches[branchname] = interpretations[branchname]
            else:
                branches[branchname] = uproot.interp.auto.interpret(self.tree[branchname])

        waits = list(self.tree.iterate(branches=branches, entrysteps=entrysteps, outputtype=list, reportentries=True, entrystart=entrystart, entrystop=entrystop, cache=cache, basketcache=basketcache, keycache=keycache, executor=readexecutor, blocking=False))

        def calculate(start, stop, wait):
            numentries = stop - start
            arrays = wait()

            for i in range(len(compiledintermediates)):
                arrays.append(numpy.empty(numentries, dtype=self.NEW_ARRAY_DTYPE))

            if len(entryvars) > 0:
                arrays.append(numpy.arange(start, stop))

            return start, stop, numentries, tuple(arrays)

        def wrap_for_python_scope(start, stop, wait):
            return lambda: calculate(start, stop, wait)

        return [wrap_for_python_scope(start, stop, wait) for start, stop, wait in waits]

class TTreeFunctionalMethods(uproot.tree.TTreeMethods):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.tree.TTreeMethods.__metaclass__,), {})

    def define(self, **exprs):
        return ChainOrigin(self).define(**exprs)

    def intermediate(self, cache=None, **exprs):
        return ChainOrigin(self).intermediate(cache=cache, **exprs)

    def filter(self, expr):
        return ChainOrigin(self).filter(expr)

    def iterate_newarrays(self, exprs, entrysteps=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, reportentries=False, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).iterate_newarrays(exprs, entrysteps=entrysteps, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=outputtype, reportentries=reportentries, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def newarrays(self, exprs, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).newarrays(exprs, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=outputtype, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def newarray(self, expr, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).newarray(expr, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def reduceall(self, identity, increment, combine=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).reduceall(identity, increment, combine=combine, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=outputtype, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def reduce(self, identity, increment, combine=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).reduce(identity, increment, combine=combine, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def hists(self, specs, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).hists(specs, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=outputtype, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def hist(self, numbins, low, high, dataexpr, weightexpr=None, name=None, title=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).hist(numbins, low, high, dataexpr, weightexpr=weightexpr, name=name, title=title, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

uproot.rootio.methods["TTree"] = TTreeFunctionalMethods
