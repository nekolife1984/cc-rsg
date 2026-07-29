"""M6 — C extractor (tree-sitter based).

Extracts C constructs:
  - struct_specifier → c_struct
  - enum_specifier → c_enum
  - union_specifier → c_union
  - type_definition → c_typedef
  - function_definition → c_function
"""

from __future__ import annotations

from typing import Callable

from .. import taxonomy
from ..model import SourceUnit, fingerprint
from . import register, Extractor
from . import tshelpers as H

# Register the kinds this extractor emits.
for _kind, _role, _tier in [
    ("c_function", "callable", "middle"),
    ("c_struct", "model", "middle"),
    ("c_enum", "model", "middle"),
    ("c_union", "model", "middle"),
    ("c_typedef", "dependency", "middle"),
]:
    taxonomy.register_kind(_kind, _role, _tier)


class CExtractor(Extractor):
    language = "c"

    def extract(self, path, source, id_factory: Callable[[], str], framework=None, context=None):
        tree, src = H.parse("c", source)
        out: list[SourceUnit] = []

        def emit(role, kind, name, node, endpoint=None):
            s, e = H.line_range(node)
            out.append(SourceUnit(
                id=id_factory(), path=path, line_range=(s, e), language="c",
                role=role, kind=kind, name=name, framework=framework,
                signature=H.text(node, src).splitlines()[0].strip()[:200],
                endpoint=endpoint, fingerprint=fingerprint(H.text(node, src)),
            ))

        def _type_identifier_name(node) -> str | None:
            """Extract name from the first type_identifier child, or None."""
            for c in node.children:
                if c.type == "type_identifier":
                    return H.text(c, src)
            return None

        def _function_name(fn) -> str | None:
            """Extract function name via function_declarator -> identifier."""
            for c in fn.children:
                if c.type == "function_declarator":
                    for cc in c.children:
                        if cc.type == "identifier":
                            return H.text(cc, src)
                    return None
            return None

        def walk(node):
            for c in node.children:
                if c.type == "struct_specifier":
                    name = _type_identifier_name(c)
                    if name is not None:
                        emit("model", "c_struct", name, c)
                elif c.type == "enum_specifier":
                    name = _type_identifier_name(c)
                    if name is not None:
                        emit("model", "c_enum", name, c)
                elif c.type == "union_specifier":
                    name = _type_identifier_name(c)
                    if name is not None:
                        emit("model", "c_union", name, c)
                elif c.type == "type_definition":
                    name = _type_identifier_name(c)
                    if name is not None:
                        emit("dependency", "c_typedef", name, c)
                elif c.type == "function_definition":
                    name = _function_name(c)
                    if name is not None:
                        emit("callable", "c_function", name, c)
                walk(c)

        walk(tree.root_node)
        return out


if H.have("c"):
    register(CExtractor())
