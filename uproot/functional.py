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
    NEW_ARRAY_DTYPE = numpy.dtype(numpy.float64)

    def __init__(self, previous):
        self.previous = previous

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
    def _string2fcn(string):
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

        names = ChainStep._generatenames(["fcn"], insymbols.union(outsymbols))

        module = ast.parse("def {fcn}({args}): pass".format(fcn=names["fcn"], args=", ".join(sorted(insymbols))))
        module.body[0].body = body
        return ChainStep._makefcn(compile(module, string, "exec"), math.__dict__, names["fcn"], string)

    @staticmethod
    def _tofcn(expr):
        identifier = None
        if isinstance(expr, parsable):
            if ChainStep._isidentifier(expr):
                identifier = expr
            expr = ChainStep._string2fcn(expr)

        return expr, expr.__code__.co_varnames, identifier

    @staticmethod
    def _generatenames(want, avoid):
        disambigifier = 0
        out = {}
        for name in want:
            newname = name
            while newname in avoid or newname in out or keyword.iskeyword(newname):
                newname = "{0}_{1}".format(name, disambigifier)
                disambigifier += 1
            out[name] = newname
        return out

    @staticmethod
    def _tofcns(exprs):
        if isinstance(exprs, parsable):
            return [ChainStep._tofcn(exprs) + (exprs, exprs)]

        elif callable(exprs) and hasattr(exprs, "__code__"):
            return [ChainStep._tofcn(exprs) + (id(exprs), getattr(exprs, "__name__", None))]

        elif isinstance(exprs, dict) and all(isinstance(x, parsable) or (callable(x) and hasattr(x, "__code__")) for x in exprs.values()):
            return [ChainStep._tofcn(x) + (x if isinstance(x, parsable) else id(x), n) for n, x in exprs.items()]

        else:
            try:
                assert all(isinstance(x, parsable) or (callable(x) and hasattr(x, "__code__")) for x in exprs)
            except (TypeError, AssertionError):
                raise TypeError("exprs must be a dict of strings or functions, iterable of strings or functions, a single string, or a single function")
            else:
                return [ChainStep._tofcn(x) + ((x, x) if isinstance(x, parsable) else (id(x), getattr(x, "__name__", None))) for i, x in enumerate(exprs)]

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
            return lambda f: nb.njit()(f)

        else:
            import numba as nb
            return lambda f: nb.jit(**numba)(f)

    def _satisfy(self, requirement, sourcenames, intermediates, entryvars, entryvar, aliases):
        self.previous._satisfy(requirement, sourcenames, intermediates, entryvars, entryvar, aliases)

    def _argfcn(self, requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache):
        return self.previous._argfcn(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache)

    def _iterateapply(self, dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, entrysteps, entrystart, entrystop, aliases, interpretations, entryvar, outputtype, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
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

        interleave = readexecutor is not None and calcexecutor is not None and isinstance(self.source, ChainOrigin)

        await, oldstart, oldstop, oldnumentries = None, None, None, None
        for start, stop, numentries, arrays in self.source._iterate(sourcenames, intermediates, compiledintermediates, len(entryvars) > 0, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
            if interleave and await is not None:
                await()
                yield oldstart, oldstop, oldnumentries, finish(results)

            # do the intermediates synchronously because they have a dependency order
            for compiledintermediate in compiledintermediates:
                compiledintermediate(arrays)

            # do the subexpressions asynchronously and in parallel
            results = [None] * len(compiled)
            def calculate(i):
                try:
                    out = compiled[i](arrays)
                except:
                    return sys.exc_info()
                else:
                    results[i] = out
                    return None

            if calcexecutor is None:
                for i in range(len(compiled)):
                    uproot.tree._delayedraise(calculate(i))
                def await():
                    pass

            else:
                execinfos = calcexecutor.map(calculate, range(len(compiled)))
                def await():
                    for excinfo in excinfos:
                        uproot.tree._delayedraise(excinfo)

            oldstart, oldstop, oldnumentries = start, stop, numentries

            if not interleave:
                await()
                yield oldstart, oldstop, oldnumentries, finish(results)
                
        if interleave and await is not None:
            await()
            yield oldstart, oldstop, oldnumentries, finish(results)

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

        intermediate = Intermediate(self, None, nonidentifiers)

        # find all the dependencies and put unique ones in lists
        sourcenames = []
        intermediates = []
        entryvars = set()
        for name in toresolve:
            intermediate._satisfy(name, sourcenames, intermediates, entryvars, entryvar, aliases)

        # reorder the (Intermediate, name) pairs in order of increasing dependency (across all expressions)
        intermediates = Intermediate._dependencyorder(sourcenames, intermediates, entryvar, aliases)

        # now compile them, using the established "sourcenames" and "intermediates" order to get arguments by tuple index (hard-compiled into functions)
        fcncache = {}
        compiled = []
        for name in toresolve:
            compiled.append(intermediate._argfcn(name, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache))

        # compile the intermediates in the same way
        compiledintermediates = [intermediate._compileintermediate(requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache) for intermediate, requirement in intermediates]

        return dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, compilefcn

    def iterate_newarrays(self, exprs, entrysteps=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, reportentries=False, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, compilefcn = self._prepare(exprs, aliases, entryvar, numba)

        iterator = self._iterateapply(dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, entrysteps, entrystart, entrystop, aliases, interpretations, entryvar, outputtype, cache, basketcache, keycache, readexecutor, calcexecutor, numba)
        if reportentries:
            for start, stop, numentries, results in iterator:
                yield start, stop, numentries, results
        else:
            for start, stop, numentries, results in iterator:
                yield results

    def newarrays(self, exprs, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        entrystart, entrystop = self.tree._normalize_entrystartstop(entrystart, entrystop)
        outarrays = [(dictname, numpy.empty(entrystop - entrystart, dtype=self.NEW_ARRAY_DTYPE)) for fcn, requirements, identifier, cacheid, dictname in self._tofcns(exprs)]

        if outputtype == namedtuple:
            for dictname, outarray in outarrays:
                if not self._isidentifier(dictname):
                    raise ValueError("illegal field name for namedtuple: {0}".format(repr(dictname)))
            outputtype = namedtuple("Arrays", dictnames)

        dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, compilefcn = self._prepare(exprs, aliases, entryvar, numba)

        index = 0
        for start, stop, numentries, results in self._iterateapply(dictnames, compiled, sourcenames, intermediates, compiledintermediates, entryvars, None, entrystart, entrystop, aliases, interpretations, entryvar, tuple, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
            for (dictname, outarray), result in zip(outarrays, results):
                outarray[index : index + numentries] = result
                index += numentries

        outarrays = [(dictname, outarray[:index].copy()) for dictname, outarray in outarrays]
            
        if issubclass(outputtype, dict):
            return outputtype(outarrays)
        elif outputtype == tuple or outputtype == list:
            return outputtype([outarray for name, outarray in outarrays])
        else:
            return outputtype(*[outarray for name, outarray in outarrays])

    def newarray(self, expr, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        if isinstance(expr, parsable):
            pass
        elif callable(expr) and hasattr(expr, "__code__"):
            pass
        else:
            raise TypeError("expr must be a single string or function")
        return self.newarrays(expr, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=tuple, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)[0]

    def define(self, **exprs):
        return Define(self, exprs)

    def intermediate(self, cache=None, **exprs):
        return Intermediate._create(self, cache, **exprs)

    def filter(self, expr):
        return Filter(self, expr)

class Define(ChainStep):
    def __init__(self, previous, exprs):
        raise NotImplementedError

    # FIXME!!!

class Intermediate(ChainStep):
    @staticmethod
    def _create(previous, cache, **exprs):
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
                    while not isinstance(node, Intermediate) or name not in node.fcn:
                        node = node.previous
                    out.add((node, name))
            return out
        
        return list(topological_sort([((intermediate, name), dependencies(intermediate, name)) for intermediate, name in intermediates]))

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
        self.previous = previous

        if isinstance(expr, parsable):
            pass
        elif callable(expr) and hasattr(expr, "__code__"):
            pass
        else:
            raise TypeError("expr must be a single string or function")

        self.fcn, self.requirements, identifier = self._tofcn(expr)

    @property
    def source(self):
        return self

    def _satisfy(self, requirement, sourcenames, intermediates, entryvars, entryvar, aliases):
        if requirement not in sourcenames:
            sourcenames.append(requirement)

    def _argfcn(self, requirement, sourcenames, intermediates, entryvar, aliases, compilefcn, fcncache):
        if requirement in sourcenames:
            index = sourcenames.index(requirement)
        else:
            index = len(sourcenames) + [x for x in self.requirements if x not in sourcenames].index(requirement)

        if index not in fcncache:
            fcncache[index] = compilefcn(lambda arrays: arrays[index])
        return fcncache[index]

    def _iterate(self, sourcenames, intermediates, compiledintermediates, hasentryvar, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
        requests = sourcenames + [x for x in self.requirements if x not in sourcenames]
        maskindex = len(requests)
        prevdictnames, prevcompiled, prevsourcenames, previntermediates, prevcompiledintermediates, preventryvars, compilefcn = self.previous._prepare(requests, aliases, entryvar, numba)

        env = {"fcn": compilefcn(self.fcn), "getmask": compilefcn(lambda arrays: arrays[maskindex])}

        itemdefs = []
        itemis = []
        prevfcncache = {}
        for i, req in enumerate(self.requirements):
            argfcn = self.previous._argfcn(req, prevsourcenames, previntermediates, entryvar, aliases, compilefcn, prevfcncache)
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

        previterator = self.previous._iterateapply(prevdictnames, prevcompiled, prevsourcenames, previntermediates, prevcompiledintermediates, preventryvars, entrysteps, entrystart, entrystop, aliases, interpretations, entryvar, list, cache, basketcache, keycache, readexecutor, calcexecutor, numba)
        for prevstart, prevstop, prevnumentries, arrays in previterator:
            # add the mask array
            mask = numpy.empty(prevnumentries, dtype=numpy.bool)
            arrays.append(mask)

            # evaluate the expression and fill the mask
            afcn(tuple(arrays))

            # apply the mask only to the sourcename arrays
            cutarrays = [array[mask] for array in arrays[:len(sourcenames)]]
            cutnumentries = mask.sum()

            for i in range(len(compiledintermediates)):
                # for Intermediates (post-filter)
                cutarrays.append(numpy.empty(cutnumentries, dtype=self.NEW_ARRAY_DTYPE))

            if hasentryvar:
                # same array, but putting it in the canonical position
                cutarrays.append(cutarrays[sourcenames.index(entryvar)])

            yield prevstart, prevstop, cutnumentries, tuple(cutarrays)

class ChainOrigin(ChainStep):
    def __init__(self, tree):
        self._tree = tree

    @property
    def source(self):
        return self

    @property
    def tree(self):
        return self._tree

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

    def _iterate(self, sourcenames, intermediates, compiledintermediates, hasentryvar, aliases, interpretations, entryvar, entrysteps, entrystart, entrystop, cache, basketcache, keycache, readexecutor, calcexecutor, numba):
        branches = {}
        for branchname in sourcenames:
            if branchname in interpretations:
                branches[branchname] = interpretations[branchname]
            else:
                branches[branchname] = uproot.interp.auto.interpret(self.tree[branchname])

        for entrystart, entrystop, arrays in self.tree.iterate(entrysteps = entrysteps,
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

            for i in range(len(compiledintermediates)):
                arrays.append(numpy.empty(entrystop - entrystart, dtype=self.NEW_ARRAY_DTYPE))

            if hasentryvar:
                arrays.append(numpy.arange(entrystart, entrystop))

            yield entrystart, entrystop, entrystop - entrystart, tuple(arrays)

class TTreeFunctionalMethods(uproot.tree.TTreeMethods):
    # makes __doc__ attribute mutable before Python 3.3
    __metaclass__ = type.__new__(type, "type", (uproot.tree.TTreeMethods.__metaclass__,), {})

    def iterate_newarrays(self, exprs, entrysteps=None, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, reportentries=False, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).iterate_newarrays(exprs, entrysteps=entrysteps, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=outputtype, reportentries=reportentries, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def newarrays(self, exprs, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, outputtype=dict, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).newarrays(exprs, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, outputtype=outputtype, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def newarray(self, expr, entrystart=None, entrystop=None, aliases={}, interpretations={}, entryvar=None, cache=None, basketcache=None, keycache=None, readexecutor=None, calcexecutor=None, numba=ifinstalled):
        return ChainOrigin(self).newarray(expr, entrystart=entrystart, entrystop=entrystop, aliases=aliases, interpretations=interpretations, entryvar=entryvar, cache=cache, basketcache=basketcache, keycache=keycache, readexecutor=readexecutor, calcexecutor=calcexecutor, numba=numba)

    def define(self, **exprs):
        return ChainOrigin(self).define(**exprs)

    def intermediate(self, cache=None, **exprs):
        return ChainOrigin(self).intermediate(cache=cache, **exprs)

    def filter(self, expr):
        return ChainOrigin(self).filter(expr)

    def aggregate(self):
        raise NotImplementedError

    def hist(self, numbins, low, high, expr):
        raise NotImplementedError

    def fork(self):
        raise NotImplementedError

uproot.rootio.methods["TTree"] = TTreeFunctionalMethods
