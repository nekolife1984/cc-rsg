"""M6 — Kotlin extractor (tree-sitter based, Spring/Ktor/Android-aware).

Extracts Kotlin-specific constructs that the Java extractor cannot handle:
  - data class → schema role (Pydantic-like DTO positioning)
  - object declaration → class role
  - suspend functions → callable role
  - Extension functions → callable role
  - Spring annotations (same as Java: @RestController, @GetMapping, @Entity, etc.)
  - Ktor routing (routing { get("/path") { } })
  - top-level properties → schema (config-like vals)
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
    ("kotlin_property", "schema", "micro"),
]:
    taxonomy.register_kind(_kind, _role, _tier)

# Spring annotation method mapping (shared with Java)
_MAPPING_METHOD = {
    "GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT",
    "PatchMapping": "PATCH", "DeleteMapping": "DELETE", "RequestMapping": "ANY",
}

# Ktor HTTP method verbs
_KTOR_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _modifier_annotation_names(node, src) -> set[str]:
    """Collect annotation names from a node's modifiers (the Kotlin way).

    In tree-sitter-kotlin, annotations sit inside the ``modifiers`` child as
    ``annotation`` nodes. Each annotation's ``@``-prefixed identifier is the
    name (stripped of the ``@`` prefix).
    """
    mods = H.field(node, "modifiers")
    if not mods:
        return set()
    names: set[str] = set()
    for c in mods.children:
        if c.type == "annotation":
            # annotation text is e.g. "@RestController" — strip the @
            raw = H.text(c, src).strip()
            names.add(raw.lstrip("@"))
    return names


def _has_modifier(node, modifier: str) -> bool:
    """Check if a node has a specific modifier keyword (data, sealed, suspend, etc.)."""
    mods = H.field(node, "modifiers")
    if not mods:
        return False
    for c in mods.children:
        if c.type == modifier:
            return True
    return False


def _first_string_arg(node, src) -> str | None:
    """Return the first string literal argument of a call expression."""
    args = None
    for c in node.children:
        if c.type == "call_expression":
            args = c
            break
        if c.type == "lambda_literal":
            # Ktor: get("/path") { } — the path is in the call, not lambda
            continue
    if args is None and node.type == "call_expression":
        args = node
    if args is None:
        return None
    for c in args.children:
        if c.type == "string_literal":
            raw = H.text(c, src)
            return raw.strip("\"")
        if c.type == "navigation_expression":
            # member expression like foo.bar
            for cc in c.children:
                if cc.type == "string_literal":
                    return H.text(cc, src).strip("\"")
    return None


def _ktor_path(call_node, src) -> str | None:
    """Extract the path string from a Ktor route call.

    Handles:
      get("/users") { }
      post("/api/users") { }
    """
    for c in call_node.children:
        if c.type == "call_suffix":
            for cc in c.children:
                if cc.type == "string_literal":
                    return H.text(cc, src).strip("\"")
                # handle value_argument -> string_literal
                for ccc in cc.children:
                    if ccc.type == "string_literal":
                        return H.text(ccc, src).strip("\"")
    return None


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
            anns = _modifier_annotation_names(c, src)
            name = H.name_of(c, src)

            # Spring stereotypes
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

            # data class → schema (DTO / Pydantic-like)
            if _has_modifier(c, "data"):
                emit("schema", "kotlin_data_class", name, c)
                return

            # regular class
            emit("class", "kotlin_class", name, c)

        def handle_object(obj):
            name = H.name_of(obj, src) or "?"
            emit("class", "kotlin_object", name, obj)

        def handle_function(fn):
            name = H.name_of(fn, src) or "?"
            is_suspend = _has_modifier(fn, "suspend")
            is_extension = False

            # Detect extension function: if the function has a receiver type
            # (non-null type_identifier before the name)
            for c in fn.children:
                if c.type in ("type_identifier", "user_type"):
                    # The first type_identifier before ( is the receiver
                    for sibling in fn.children:
                        if sibling.type == "parameter":
                            break
                        if sibling.type in ("type_identifier", "user_type"):
                            is_extension = True
                            break
                    break

            if is_suspend:
                emit("callable", "kotlin_suspend_function", name, fn)
            elif is_extension:
                emit("callable", "kotlin_extension_function", name, fn)
            else:
                emit("callable", "kotlin_function", name, fn)

        def _emit_spring_endpoints(class_node, ctrl):
            """Extract @*Mapping endpoints from a Spring controller class."""
            body = H.field(class_node, "class_body")
            if not body:
                return
            for m in body.children:
                if m.type != "function_declaration":
                    continue
                anns = _modifier_annotation_names(m, src)
                for ann in anns:
                    if ann in _MAPPING_METHOD:
                        method = _MAPPING_METHOD[ann]
                        # Try to extract path from annotation arg
                        path_arg = _annotation_string_arg(m, src, ann)
                        emit("endpoint", "spring_endpoint",
                             f"{ctrl}#{H.name_of(m, src)}", m,
                             endpoint={"method": method, "path": path_arg or ""})
                        break

        def _annotation_string_arg(node, src, ann_name: str) -> str | None:
            """Extract the first string argument of a named annotation.

            e.g. @GetMapping("/users") → "/users"
            """
            mods = H.field(node, "modifiers")
            if not mods:
                return None
            for c in mods.children:
                if c.type != "annotation":
                    continue
                raw = H.text(c, src).strip()
                if not raw.startswith("@" + ann_name):
                    continue
                # Find the string inside parentheses
                for cc in c.children:
                    if cc.type in ("string_literal", "string"):
                        return H.text(cc, src).strip("\"")
                return None
            return None

        def _emit_ktor_endpoints(fn_body_node):
            """Walk a Ktor ``routing { }`` block for route definitions.

            Matches ``get("/path") { }``, ``post("/path") { }`` etc.
            """
            for c in fn_body_node.children:
                if c.type == "call_expression":
                    call_text = H.text(c, src).strip()
                    # Check if this is a Ktor method call
                    for ktor_method in _KTOR_METHODS:
                        if call_text.startswith(ktor_method + "(") or \
                           call_text.startswith(ktor_method + " ") or \
                           call_text.startswith(ktor_method + "{"):
                            p = _ktor_path(c, src)
                            emit("endpoint", "ktor_endpoint",
                                 f"{ktor_method.upper()} {p or '/'}", c,
                                 endpoint={"method": ktor_method.upper(), "path": p or "/"})
                            break
                    # Check for nested routing { }
                    if call_text.startswith("routing"):
                        for cc in c.children:
                            _emit_ktor_endpoints(cc)

        def walk(node):
            for c in node.children:
                if c.type == "class_declaration":
                    handle_class(c)
                elif c.type == "object_declaration":
                    handle_object(c)
                elif c.type == "function_declaration":
                    # If function is top-level or inside a file (not inside a class body)
                    handle_function(c)
                # Recurse into class bodies for nested classes
                if c.type in ("class_body", "source_file", "script_file"):
                    walk(c)

        walk(tree.root_node)
        return out


if H.have("kotlin"):
    register(KotlinExtractor())
