#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast

import meta
import yaml

def compose(pyast, **replacements):
    def recurse(x):
        if isinstance(x, ast.AST):
            if isinstance(x, ast.Name) and x.id in replacements:
                x = replacements[x.id]

            if isinstance(x, ast.Attribute) and x.attr in replacements:
                x.attr = replacements[x.attr]

            if isinstance(x, ast.FunctionDef) and x.name in replacements:
                x.name = replacements[x.name]

            for f in x._fields:
                setattr(x, f, recurse(getattr(x, f)))
            return x

        elif isinstance(x, list):
            return [recurse(xi) for xi in x]

        else:
            return x

    return recurse(pyast)

def toexpr(string, **replacements):
    return compose(ast.parse(string).body[0].value, **replacements)

def tostmt(string, **replacements):
    return compose(ast.parse(string).body[0], **replacements)

def tostmts(string, **replacements):
    return compose(ast.parse(string).body, **replacements)

def toname(string, ctx=ast.Load()):
    out = ast.Name(string, ctx)
    out.lineno = 1
    out.col_offset = 0
    return out

def toif(predicate, consequent, alternate):
    out = ast.If(predicate, consequent, alternate)
    out.lineno = 1
    out.col_offset = 0
    return out

def toliteral(obj):
    if isinstance(obj, str):
        out = ast.Str(obj)
    elif isinstance(obj, (int, float)):
        out = ast.Num(obj)
    else:
        raise AssertionError
    out.lineno = 1
    out.col_offset = 0
    return out

def formula(pyast):
    def recurse(x):
        if isinstance(x, ast.Name):
            return toexpr("self.X", X=x.id)
        elif isinstance(x, ast.AST):
            for field in x._fields:
                setattr(x, field, recurse(getattr(x, field)))
            return x
        elif isinstance(x, list):
            return [recurse(xi) for xi in x]
        else:
            return x
    return recurse(pyast)

def assignment(field, tpe):
    at = None
    if isinstance(tpe, dict) and "type" in tpe:
        if "at" in tpe:
            at = tpe["at"]
        tpe = tpe["type"]

    statements = []
    properties = []

    if isinstance(tpe, dict) and set(tpe.keys()) == set(["array", "size"]):
        assert at is None
        fieldi = toexpr("FIELD[i]", FIELD=field)
        fieldi.ctx = ast.Store()
        statements.extend(tostmts(
            """
size = EXPR
FIELD = [None] * size
for i in range(size):
    pass""",
            EXPR=formula(toexpr(tpe["size"])),
            FIELD=field))
        statements[-1].body, _ = assignment(fieldi, tpe["array"])

    elif isinstance(tpe, dict) and set(tpe.keys()) == set(["string"]):
        assert at is None
        size, = tpe.values()
        assert isinstance(size, int)
        statements.extend(tostmts(
            """
end = start + SIZE
FIELD = struct.unpack(FORMAT, file[start:end])[0]
start = end""",
            SIZE=toliteral(size),
            FIELD=field,
            FORMAT=toliteral("{0}s".format(size))))

    elif tpe == "string":
        assert at is None
        statements.extend(tostmts(
            """
size = struct.unpack("B", file[start:start+1])
start += 1
if size == 255:
    size = struct.unpack(">I", file[start:start+4])
    start += 4
end = start + size
FIELD = struct.unpack("{0}s".format(size), file[start:end])[0]
start = end""",
            FIELD=field))

    else:
        assert isinstance(tpe, string)
        primitives = {
            "bool": ("?", 1),
            "int8": ("b", 1),
            "uint8": ("B", 1),
            "int16": (">h", 2),
            "uint16": (">H", 2),
            "int32": (">i", 4),
            "uint32": (">I", 4),
            "int64": (">q", 8),
            "uint64": (">Q", 8),
            "float32": (">f", 4),
            "float64": (">d", 8)
            }

        if tpe in primitives:
            assert at is None
            format, size = [tpe]
            statements.extend(tostmts(
                """
end = start + SIZE
FIELD = struct.unpack(FORMAT, file[start:end])[0]
start = end""",
                SIZE=toliteral(size),
                FIELD=field))

        elif at is None:
            statements.extend(tostmts(
                """
end, FIELD = CLASS.read(file, start)
start = end""",
                FIELD=field,
                CLASS=toname(tpe)))

        else:
            assert isinstance(field, ast.Name)
            fieldmarker = toname("_" + field.id)
            if len(properties) == 0:
                statements.append(tostmt("self._file = file"))
            statements.append(tostmt("FIELDMARKER = AT", FIELDMARKER=fieldmarker, AT=formula(toexpr(at))))
            properties.extend(tostmts(
                """
@property
def FIELDNAME(self):
    return CLASS.read(self._file, FIELDMARKER)""",
                FIELDNAME=field.id,
                CLASS=toname(tpe),
                FIELDMARKER=fieldmarker))

    return statements, properties

def assignments(members):
    assert isinstance(members, list)

    names = []
    statements = []
    properties = []
    for member in members:
        assert isinstance(member, dict)
        if set(member.keys()) == set(["if"]):
            cases, = member.values()
            assert isinstance(cases, list)

            tmpns = []
            folded = []
            for case in reversed(cases):
                if set(case.keys()) == set(["case", "then"]):
                    predicate = formula(toexpr(case["case"]))
                    ns, stmts, props = assignments(case["then"])
                    folded = [toif(predicate, stmts, folded)]

                else:
                    assert set(case.keys()) == set(["else"])
                    ns, stmts, props = assignments(case["else"])
                    assert folded == []
                    folded = stmts

                tmpns.append(ns)
                properties.extend(props)

            for ns in reversed(tmpns):
                names.extend(ns)
            statements.extend(folded)

        else:
            assert len(member) == 1
            (fieldname, tpe), = member.items()

            field = toexpr("self.X", X=fieldname)
            field.ctx = ast.Store()

            stmts, props = assignment(field, tpe)

            names.append(fieldname)
            statements.extend(stmts)
            properties.extend(props)

    return names, statements, properties

def declare(classname, classspec):
    assert "members" in classspec
    names, statements, properties = assignments(classspec["members"])

    out = tostmt("""
class NAME(object):
    @staticmethod
    def read(file, start):
        self = NAME()
""")
    out.body.body.extend(statements)
    out.body.extend(properties)
    return out

if __name__ == "__main__":
    pass
