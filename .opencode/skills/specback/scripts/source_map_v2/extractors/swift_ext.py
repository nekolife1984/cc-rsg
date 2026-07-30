"""Swift language extractor for source_map_v2 (tree-sitter-swift v0.0.1).

Extracts Swift constructs — classes, structs, enums, protocols, actors,
extensions, top-level functions, and methods — mapping them to specback
source-map roles.

Tree-sitter-swift v0.0.1 quirks
-------------------------------
- ``class_declaration`` is the *universal* container for classes, structs,
  enums, extensions, and actors.  The first keyword child (``class``,
  ``struct``, ``enum``, ``extension``, ``actor``) discriminates the actual
  declaration type.
- ``protocol_declaration`` is its own, separate node type.
- Functions inside protocols use ``protocol_function_declaration`` rather
  than ``function_declaration``.
- ``function_declaration`` inside a ``class_body`` / ``enum_class_body`` is
  a method; at the top level it is a plain function.
"""

from __future__ import annotations

from typing import Callable

from .. import taxonomy
from ..model import SourceUnit, fingerprint
from . import register, Extractor
from . import tshelpers as H

# Register the kinds this extractor emits (binds each to a common role).
for _kind, _role, _tier in [
    ("swift_class", "class", "middle"),
    ("swift_struct", "model", "middle"),
    ("swift_enum", "model", "middle"),
    ("swift_protocol", "dependency", "middle"),
    ("swift_actor", "class", "middle"),
    ("swift_extension", "class", "middle"),
    ("swift_function", "callable", "middle"),
    ("swift_method", "callable", "middle"),
]:
    taxonomy.register_kind(_kind, _role, _tier)

# Body node types whose nested function_declaration nodes are methods.
_TYPE_BODIES = {"class_body", "enum_class_body", "protocol_body"}


# ---------------------------------------------------------------------------
# The extractor
# ---------------------------------------------------------------------------


class SwiftExtractor(Extractor):
    language = "swift"

    def extract(self, path, source, id_factory: Callable[[], str], framework=None, context=None):
        tree, src = H.parse("swift", source)
        out: list[SourceUnit] = []

        def emit(role, kind, name, node, endpoint=None):
            s, e = H.line_range(node)
            out.append(SourceUnit(
                id=id_factory(), path=path, line_range=(s, e), language="swift",
                role=role, kind=kind, name=name, framework=framework,
                signature=H.text(node, src).splitlines()[0].strip()[:200],
                endpoint=endpoint, fingerprint=fingerprint(H.text(node, src)),
            ))

        def _keyword(node):
            """Return the keyword child of a ``class_declaration``.

            In tree-sitter-swift v0.0.1, ``class_declaration`` is a universal
            container — the first (keyword) child is one of ``class``,
            ``struct``, ``enum``, ``extension``, or ``actor``.
            """
            for c in node.children:
                if c.type in ("class", "struct", "enum", "extension", "actor"):
                    return c.type
            return "?"

        def _is_in_type_body(node):
            """Return True if a function_declaration sits inside a type body."""
            p = node.parent
            return p is not None and p.type in _TYPE_BODIES

        def handle_class_decl(c):
            """Dispatch ``class_declaration`` by its keyword child."""
            kw = _keyword(c)
            name = H.name_of(c, src) or "?"
            if kw == "struct":
                emit("model", "swift_struct", name, c)
            elif kw == "enum":
                emit("model", "swift_enum", name, c)
            elif kw == "extension":
                emit("class", "swift_extension", name, c)
            elif kw == "actor":
                emit("class", "swift_actor", name, c)
            elif kw == "class":
                emit("class", "swift_class", name, c)

        def handle_function_decl(fn):
            name = H.name_of(fn, src) or "?"
            if _is_in_type_body(fn):
                emit("callable", "swift_method", name, fn)
            else:
                emit("callable", "swift_function", name, fn)

        def walk(node):
            for c in node.children:
                if c.type == "class_declaration":
                    handle_class_decl(c)
                elif c.type == "protocol_declaration":
                    name = H.name_of(c, src) or "?"
                    emit("dependency", "swift_protocol", name, c)
                elif c.type == "function_declaration":
                    handle_function_decl(c)
                elif c.type == "protocol_function_declaration":
                    name = H.name_of(c, src) or "?"
                    emit("callable", "swift_method", name, c)
                walk(c)

        walk(tree.root_node)
        return out


if H.have("swift"):
    register(SwiftExtractor())
