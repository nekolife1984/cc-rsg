"""M6 — Dart extractor (tree-sitter based).

Extracts Dart-specific constructs:
  - class → dart_class
  - top-level function → dart_function
  - method (function inside a class body) → dart_method
  - enum → dart_enum
  - typedef → dart_typedef
  - mixin → dart_mixin
  - extension → dart_extension
"""

from __future__ import annotations

from typing import Callable

from .. import taxonomy
from ..model import SourceUnit, fingerprint
from . import register, Extractor
from . import tshelpers as H

# Register the kinds this extractor emits (binds each to a common role).
for _kind, _role, _tier in [
    ("dart_class", "class", "middle"),
    ("dart_function", "callable", "middle"),
    ("dart_method", "callable", "middle"),
    ("dart_enum", "model", "middle"),
    ("dart_typedef", "dependency", "middle"),
    ("dart_mixin", "class", "middle"),
    ("dart_extension", "class", "middle"),
]:
    taxonomy.register_kind(_kind, _role, _tier)


class DartExtractor(Extractor):
    language = "dart"

    def extract(self, path, source, id_factory: Callable[[], str], framework=None, context=None):
        tree, src = H.parse("dart", source)
        out: list[SourceUnit] = []

        def emit(role, kind, name, node, endpoint=None):
            s, e = H.line_range(node)
            out.append(SourceUnit(
                id=id_factory(), path=path, line_range=(s, e), language="dart",
                role=role, kind=kind, name=name, framework=framework,
                signature=H.text(node, src).splitlines()[0].strip()[:200],
                endpoint=endpoint, fingerprint=fingerprint(H.text(node, src)),
            ))

        def _is_inside_class_body(node) -> bool:
            """Return True if *node* is inside a class body (i.e. it is a method)."""
            p = node.parent
            while p is not None:
                if p.type == "class_body":
                    return True
                p = p.parent
            return False

        def walk(node):
            for c in node.children:
                if c.type == "class_definition":
                    name = H.name_of(c, src)
                    emit("class", "dart_class", name, c)

                elif c.type == "function_definition":
                    name = H.name_of(c, src) or "?"
                    if _is_inside_class_body(c):
                        emit("callable", "dart_method", name, c)
                    else:
                        emit("callable", "dart_function", name, c)

                elif c.type == "enum_definition":
                    name = H.name_of(c, src)
                    emit("model", "dart_enum", name, c)

                elif c.type == "typedef_definition":
                    name = H.name_of(c, src)
                    emit("dependency", "dart_typedef", name, c)

                elif c.type == "mixin_definition":
                    name = H.name_of(c, src)
                    emit("class", "dart_mixin", name, c)

                elif c.type == "extension_definition":
                    name = H.name_of(c, src)
                    emit("class", "dart_extension", name, c)

                walk(c)

        walk(tree.root_node)
        return out


if H.have("dart"):
    register(DartExtractor())
