"""M6 — Kotlin extractor (tree-sitter based, Spring/Ktor/Android-aware).

Extracts Kotlin-specific constructs that the Java extractor cannot handle:
  - data class → schema role (Pydantic-like DTO positioning)
  - object declaration → class role
  - suspend functions → callable role
  - Extension functions → callable role
  - Spring annotations (same as Java: @RestController, @GetMapping, @Entity, etc.)
  - Ktor routing (routing { get("/path") { } })
"""
from __future__ import annotations

from typing import Callable

from .. import taxonomy
from ..model import SourceUnit, fingerprint
from . import register, Extractor
from . import tshelpers as H

# Register the kinds this extractor emits (binds each to a common role).
for _kind, _role, _tier in [
    ("kotlin_class", "class", "middle"),
    ("kotlin_data_class", "schema", "middle"),
    ("kotlin_object", "class", "middle"),
    ("kotlin_function", "callable", "middle"),
    ("kotlin_suspend_function", "callable", "middle"),
    ("kotlin_extension_function", "callable", "middle"),
    ("spring_controller", "class", "middle"),
    ("spring_service", "dependency", "middle"),
    ("jpa_entity", "model", "middle"),
    ("spring_endpoint", "endpoint", "middle"),
    ("ktor_endpoint", "endpoint", "middle"),
]:
    taxonomy.register_kind(_kind, _role, _tier)

# Spring annotation method mapping (shared with Java)
_MAPPING_METHOD = {
    "GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT",
    "PatchMapping": "PATCH", "DeleteMapping": "DELETE", "RequestMapping": "ANY",
}

# Ktor HTTP method verbs
_KTOR_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


# ---------------------------------------------------------------------------
# Helpers for tree-sitter-kotlin AST navigation
#
# In tree-sitter-kotlin the ``modifiers`` node is a DIRECT child (not a named
# field), so H.field(node, "modifiers") returns None.  All modifier/annotation
# lookups iterate the children instead.
# ---------------------------------------------------------------------------


def _modifiers_child(node):
    """Return the first child with type ``modifiers``, or None."""
    for c in node.children:
        if c.type == "modifiers":
            return c
    return None


def _class_body_child(node):
    """Return the first child with type ``class_body``, or None."""
    for c in node.children:
        if c.type == "class_body":
            return c
    return None


def _annotation_name_of(ann_node, src) -> str:
    """Extract the bare name from an annotation node.

    ``@GetMapping("/{id}")`` → ``"GetMapping"``
    ``@RestController`` → ``"RestController"``
    ``@RequestMapping(value = ["/a"])`` → ``"RequestMapping"``
    """
    raw = H.text(ann_node, src).strip()
    stripped = raw.lstrip("@")
    paren = stripped.find("(")
    if paren != -1:
        stripped = stripped[:paren]
    return stripped


def _annotation_names(node, src) -> set[str]:
    """Collect annotation names from a node.

    tree-sitter-kotlin v1.1.0 places annotations in one of two places:

    1. Inside a ``modifiers`` child node (common for simple cases like
       ``@Service`` / ``@Entity``).

    2. As a preceding ``annotated_expression`` sibling node (common for
       multi-annotation patterns like ``@RestController @RequestMapping``,
       where the annotations wrap the declaration externally).

    We check both locations.
    """
    names: set[str] = set()

    # Source 1: modifiers child
    mods = _modifiers_child(node)
    if mods:
        for c in mods.children:
            if c.type == "annotation":
                names.add(_annotation_name_of(c, src))

    # Source 2: direct child annotation nodes (fallback)
    for c in node.children:
        if c.type == "annotation":
            names.add(_annotation_name_of(c, src))

    # Source 3: preceding annotated_expression sibling
    # (tree-sitter-kotlin v1.1.0 wraps multi-annotation sequences as
    # ``annotated_expression`` nodes before the actual declaration.)
    parent = node.parent
    if parent:
        for i, sibling in enumerate(parent.children):
            if sibling.id == node.id and i > 0:
                prev = parent.children[i - 1]
                if prev.type == "annotated_expression":
                    _collect_anns(prev, src, names)
                break

    return names


def _collect_anns(ann_node, src, names: set[str]) -> None:
    """Recursively collect annotation names from an ``annotated_expression``."""
    for c in ann_node.children:
        if c.type == "annotation":
            names.add(_annotation_name_of(c, src))
        _collect_anns(c, src, names)


def _is_data_class(node) -> bool:
    """Return True if the class_declaration has the ``data`` modifier."""
    mods = _modifiers_child(node)
    if not mods:
        return False
    for c in mods.children:
        if c.type == "class_modifier":
            for cc in c.children:
                if cc.type == "data":
                    return True
    return False


def _is_suspend_function(fn) -> bool:
    """Return True if the function_declaration has the ``suspend`` modifier."""
    mods = _modifiers_child(fn)
    if not mods:
        return False
    for c in mods.children:
        if c.type == "function_modifier":
            for cc in c.children:
                if cc.type == "suspend":
                    return True
    return False


def _is_extension_function(fn) -> bool:
    """Return True if the function_declaration is an extension function.

    Extension functions have a ``user_type`` child (the receiver) followed
    immediately by a ``.`` child, before the identifier (name).
    """
    found_user_type = False
    for c in fn.children:
        if c.type == "user_type":
            found_user_type = True
        elif c.type == "." and found_user_type:
            return True
        elif c.type in ("identifier", "name"):
            return False
    return False


def _annotation_string_arg(node, src, ann_name: str) -> str | None:
    """Extract the first string argument of a named annotation.

    e.g. @GetMapping("/users") → "/users"

    In tree-sitter-kotlin the path string is nested inside:
      annotation → constructor_invocation → value_arguments →
        value_argument → string_literal
    """
    mods = _modifiers_child(node)
    if not mods:
        return None
    for c in mods.children:
        if c.type != "annotation":
            continue
        raw = H.text(c, src).strip()
        if not raw.startswith("@" + ann_name):
            continue
        for ci in c.children:
            if ci.type == "constructor_invocation":
                for va in ci.children:
                    if va.type == "value_arguments":
                        for varg in va.children:
                            if varg.type == "value_argument":
                                for sl in varg.children:
                                    if sl.type == "string_literal":
                                        return H.text(sl, src).strip("\"")
        return None
    return None


def _ktor_path_from_call(call_node, src) -> str | None:
    """Extract path from a Ktor call expression node.

    tree-sitter-kotlin v1.1.0 represents ``get("/users") { }`` as an
    outer ``call_expression`` whose first child is an inner
    ``call_expression`` containing the identifier + value_arguments::

      call_expression (outer)
        call_expression (inner)
          identifier  "get"
          value_arguments
            value_argument
              string_literal  "/users"
        annotated_lambda  (the body)

    We walk the whole tree looking for ``string_literal`` inside any
    ``value_argument`` descendant.
    """
    path: str | None = None
    for c in call_node.children:
        if c.type == "call_suffix":
            for cc in c.children:
                if cc.type == "value_arguments":
                    for va in cc.children:
                        if va.type == "value_argument":
                            for sl in va.children:
                                if sl.type == "string_literal":
                                    path = H.text(sl, src).strip("\"")
        if c.type == "value_arguments":
            for va in c.children:
                if va.type == "value_argument":
                    for sl in va.children:
                        if sl.type == "string_literal":
                            path = H.text(sl, src).strip("\"")
        # Also recurse into nested call_expressions (Ktor pattern)
        if c.type == "call_expression":
            sub = _ktor_path_from_call(c, src)
            if sub is not None:
                path = sub
    return path


# ---------------------------------------------------------------------------
# The extractor
# ---------------------------------------------------------------------------


class KotlinExtractor(Extractor):
    language = "kotlin"

    def extract(self, path, source, id_factory: Callable[[], str], framework=None, context=None):
        tree, src = H.parse("kotlin", source)
        out: list[SourceUnit] = []

        def emit(role, kind, name, node, endpoint=None):
            s, e = H.line_range(node)
            out.append(SourceUnit(
                id=id_factory(), path=path, line_range=(s, e), language="kotlin",
                role=role, kind=kind, name=name, framework=framework,
                signature=H.text(node, src).splitlines()[0].strip()[:200],
                endpoint=endpoint, fingerprint=fingerprint(H.text(node, src)),
            ))

        def handle_class(c):
            anns = _annotation_names(c, src)
            name = H.name_of(c, src)

            if anns & {"RestController", "Controller"}:
                emit("class", "spring_controller", name, c)
                _emit_spring_endpoints(c, name)
                return

            if "Entity" in anns:
                emit("model", "jpa_entity", name, c)
                return

            if anns & {"Service", "Repository", "Component"}:
                emit("dependency", "spring_service", name, c)
                return

            if _is_data_class(c):
                emit("schema", "kotlin_data_class", name, c)
                return

            emit("class", "kotlin_class", name, c)

        def handle_object(obj):
            name = H.name_of(obj, src) or "?"
            emit("class", "kotlin_object", name, obj)

        def handle_function(fn):
            name = H.name_of(fn, src) or "?"
            if _is_suspend_function(fn):
                emit("callable", "kotlin_suspend_function", name, fn)
            elif _is_extension_function(fn):
                emit("callable", "kotlin_extension_function", name, fn)
            else:
                emit("callable", "kotlin_function", name, fn)

        def _emit_spring_endpoints(class_node, ctrl):
            """Extract @*Mapping endpoints from a Spring controller class."""
            body = _class_body_child(class_node)
            if not body:
                return
            for m in body.children:
                if m.type != "function_declaration":
                    continue
                anns = _annotation_names(m, src)
                for ann in anns:
                    if ann in _MAPPING_METHOD:
                        method = _MAPPING_METHOD[ann]
                        path_arg = _annotation_string_arg(m, src, ann)
                        emit("endpoint", "spring_endpoint",
                             f"{ctrl}#{H.name_of(m, src)}", m,
                             endpoint={"method": method, "path": path_arg or ""})
                        break

        def _walk_ktor(body_node):
            """Walk a Ktor ``routing { }`` block for route definitions."""
            for c in body_node.children:
                if c.type == "call_expression":
                    call_text = H.text(c, src).strip()
                    for ktor_method in _KTOR_METHODS:
                        if call_text.startswith(ktor_method + "(") or \
                           call_text.startswith(ktor_method + " {") or \
                           call_text.startswith(ktor_method + "{"):
                            p = _ktor_path_from_call(c, src)
                            emit("endpoint", "ktor_endpoint",
                                 f"{ktor_method.upper()} {p or '/'}", c,
                                 endpoint={"method": ktor_method.upper(), "path": p or "/"})
                            break
                    if call_text.startswith("routing") or call_text.startswith("route"):
                        _walk_ktor(c)
                else:
                    _walk_ktor(c)

        def walk(node):
            for c in node.children:
                if c.type == "class_declaration":
                    handle_class(c)
                elif c.type == "object_declaration":
                    handle_object(c)
                elif c.type == "function_declaration":
                    handle_function(c)
                walk(c)

        walk(tree.root_node)

        # Ktor routing detection (second pass on the whole tree).
        # Always scan — the ``framework`` hint is unreliable because
        # callers may not pass it, and Ktor patterns are unambiguous.
        _walk_ktor(tree.root_node)

        return out


if H.have("kotlin"):
    register(KotlinExtractor())
