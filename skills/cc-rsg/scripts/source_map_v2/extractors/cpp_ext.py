"""M6 — C++ extractor (tree-sitter based).

Extracts C++ constructs:
  - class_specifier → cpp_class
  - struct_specifier → cpp_struct
  - enum_specifier → cpp_enum / cpp_enum_class
  - alias_declaration (using X = ...) → cpp_typedef
  - Top-level function_definition → cpp_function
  - function_definition inside field_declaration_list → cpp_method / cpp_virtual_method
  - namespace_definition → cpp_namespace
  - template_declaration containing class_specifier → cpp_template_class
"""

from __future__ import annotations

from typing import Callable

from .. import taxonomy
from ..model import SourceUnit, fingerprint
from . import register, Extractor
from . import tshelpers as H

# Register the kinds this extractor emits (binds each to a common role).
for _kind, _role, _tier in [
    ("cpp_class", "class", "middle"),
    ("cpp_struct", "model", "middle"),
    ("cpp_enum", "model", "middle"),
    ("cpp_enum_class", "model", "middle"),
    ("cpp_typedef", "dependency", "middle"),
    ("cpp_function", "callable", "middle"),
    ("cpp_method", "callable", "middle"),
    ("cpp_virtual_method", "callable", "middle"),
    ("cpp_namespace", "dependency", "middle"),
    ("cpp_template_class", "class", "middle"),
]:
    taxonomy.register_kind(_kind, _role, _tier)


# ---------------------------------------------------------------------------
# The extractor
# ---------------------------------------------------------------------------


class CppExtractor(Extractor):
    language = "cpp"

    def extract(self, path, source, id_factory: Callable[[], str], framework=None, context=None):
        tree, src = H.parse("cpp", source)
        out: list[SourceUnit] = []

        def emit(role, kind, name, node, endpoint=None):
            s, e = H.line_range(node)
            out.append(SourceUnit(
                id=id_factory(), path=path, line_range=(s, e), language="cpp",
                role=role, kind=kind, name=name, framework=framework,
                signature=H.text(node, src).splitlines()[0].strip()[:200],
                endpoint=endpoint, fingerprint=fingerprint(H.text(node, src)),
            ))

        def type_name(node) -> str:
            """Get the declared name from a specifier node (class/struct/enum).

            Tries the `name` field first, then falls back to a
            ``type_identifier`` child.
            """
            nm = H.field(node, "name")
            if nm is not None:
                return H.text(nm, src)
            for c in node.children:
                if c.type == "type_identifier":
                    return H.text(c, src)
            return "?"

        def function_name(fn_node) -> str:
            """Extract the function/method name from a function_definition.

            tree-sitter-cpp nests the identifier inside the ``declarator``
            child (which is a ``function_declarator`` or plain
            ``identifier``).  ``H.name_of`` on that child works.
            """
            decl = H.field(fn_node, "declarator")
            if decl is not None:
                return H.name_of(decl, src) or "?"
            return H.name_of(fn_node, src) or "?"

        # ---- handlers ----------------------------------------------------

        def handle_class(node):
            name = type_name(node)
            emit("class", "cpp_class", name, node)

        def handle_struct(node):
            name = type_name(node)
            emit("model", "cpp_struct", name, node)

        def handle_enum(node):
            name = type_name(node)
            is_scoped = any(c.type == "class" for c in node.children)
            if is_scoped:
                emit("model", "cpp_enum_class", name, node)
            else:
                emit("model", "cpp_enum", name, node)

        def handle_typedef(node):
            # alias_declaration: "using X = ..."
            name = type_name(node)
            emit("dependency", "cpp_typedef", name, node)

        def handle_function(node):
            name = function_name(node)
            emit("callable", "cpp_function", name, node)

        def handle_method(node):
            name = function_name(node)
            has_virtual = any(c.type == "virtual" for c in node.children)
            if has_virtual:
                emit("callable", "cpp_virtual_method", name, node)
            else:
                emit("callable", "cpp_method", name, node)

        def handle_namespace(node):
            # namespace_definition → name from namespace_identifier (name field)
            nm = H.field(node, "name")
            if nm is not None:
                name = H.text(nm, src)
            else:
                name = "?"  # anonymous namespace
            emit("dependency", "cpp_namespace", name, node)

        def handle_template_class(node):
            # template_declaration containing a class_specifier →
            # use the class_specifier's name but emit from the
            # template_declaration node (so line range covers the
            # whole template declaration)
            for c in node.children:
                if c.type == "class_specifier":
                    name = type_name(c)
                    emit("class", "cpp_template_class", name, node)
                    return
            name = "?"
            emit("class", "cpp_template_class", name, node)

        # ---- tree walker -------------------------------------------------

        def walk(node, inside_class=False):
            """Recurse through the AST, emitting SourceUnits as we go.

            ``inside_class`` is True when we are inside a
            ``field_declaration_list`` (i.e. inside a class or struct
            body), so that ``function_definition`` nodes are classified
            as methods rather than top-level functions.
            """
            for c in node.children:
                if c.type == "template_declaration":
                    # Check if this template contains a class_specifier
                    class_child = None
                    for cc in c.children:
                        if cc.type == "class_specifier":
                            class_child = cc
                            break
                    if class_child is not None:
                        handle_template_class(c)
                        # Walk the class body for methods, but don't emit
                        # the inner class_specifier again as cpp_class.
                        for cc in class_child.children:
                            if cc.type == "field_declaration_list":
                                walk(cc, inside_class=True)
                    else:
                        walk(c, inside_class=inside_class)

                elif c.type == "class_specifier":
                    handle_class(c)
                    for cc in c.children:
                        if cc.type == "field_declaration_list":
                            walk(cc, inside_class=True)

                elif c.type == "struct_specifier":
                    handle_struct(c)
                    for cc in c.children:
                        if cc.type == "field_declaration_list":
                            walk(cc, inside_class=True)

                elif c.type == "enum_specifier":
                    handle_enum(c)

                elif c.type == "alias_declaration":
                    handle_typedef(c)

                elif c.type == "function_definition":
                    if inside_class:
                        handle_method(c)
                    else:
                        handle_function(c)

                elif c.type == "namespace_definition":
                    handle_namespace(c)
                    # Recurse into namespace body (inside_class resets to
                    # False because a namespace is not a class body).
                    walk(c, inside_class=False)

                else:
                    walk(c, inside_class=inside_class)

        walk(tree.root_node)
        return out


if H.have("cpp"):
    register(CppExtractor())
