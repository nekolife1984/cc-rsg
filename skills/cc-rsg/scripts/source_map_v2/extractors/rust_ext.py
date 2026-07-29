"""M6 — Rust extractor (tree-sitter based).

Extracts Rust constructs:
  - function_item → rust_function / rust_method
  - struct_item → rust_struct
  - enum_item → rust_enum
  - trait_item → rust_trait
  - type_item → rust_type_alias
  - impl_item → rust_impl_block (with methods inside)
  - mod_item (with body) → rust_module
  - const_item / static_item → rust_const
"""

from __future__ import annotations

from typing import Callable

from .. import taxonomy
from ..model import SourceUnit, fingerprint
from . import register, Extractor
from . import tshelpers as H

# Register the kinds this extractor emits (binds each to a common role).
for _kind, _role, _tier in [
    ("rust_function", "callable", "middle"),
    ("rust_method", "callable", "middle"),
    ("rust_struct", "schema", "middle"),
    ("rust_enum", "schema", "middle"),
    ("rust_trait", "callable", "middle"),
    ("rust_type_alias", "schema", "middle"),
    ("rust_impl_block", "module", "middle"),
    ("rust_module", "module", "middle"),
    ("rust_const", "config", "middle"),
]:
    taxonomy.register_kind(_kind, _role, _tier)

# Visibility modifier text for pub detection
_VISIBILITY_MODIFIER = "visibility_modifier"


# ---------------------------------------------------------------------------
# Helpers for tree-sitter-rust AST navigation
# ---------------------------------------------------------------------------


def _is_pub(node) -> bool:
    """Return True if node has ``pub`` visibility modifier."""
    for c in node.children:
        if c.type == _VISIBILITY_MODIFIER:
            return True
    return False


def _decl_name(node, src: bytes) -> str:
    """Extract the declaration name from a Rust item node.

    Most Rust items have a ``name`` field.  Falls back to first identifier child.
    """
    nm = H.field(node, "name")
    if nm is not None:
        return H.text(nm, src)
    # Fallback: look for identifier children
    for c in node.children:
        if c.type == "identifier":
            return H.text(c, src)
    return "?"


def _impl_trait_name(node, src: bytes) -> str | None:
    """If node is an impl_item for a trait (``impl Trait for Type``), return trait name."""
    children = list(node.children)
    # tree-sitter-rust: impl_item has structure: "impl" [type] ["for" type]
    # The trait name is the type after "impl", before optional "for"
    found_impl = False
    for c in children:
        if c.type == "impl":
            found_impl = True
            continue
        if found_impl and c.type in ("type", "generic_type", "path_type", "scoped_type_identifier"):
            trait_name = H.text(c, src)
            # Check if this is a trait impl (has "for" keyword after the type)
            remaining_after = False
            for c2 in children:
                if c2.type == "for" and c.id != c2.id:
                    # This is "impl Trait for Type" — the first type after "impl" is the trait
                    remaining_after = True
            if remaining_after:
                return trait_name
    return None


# ---------------------------------------------------------------------------
# The extractor
# ---------------------------------------------------------------------------


class RustExtractor(Extractor):
    language = "rust"

    def extract(self, path, source, id_factory: Callable[[], str], framework=None, context=None):
        tree, src = H.parse("rust", source)
        out: list[SourceUnit] = []

        def emit(role, kind, name, node, endpoint=None):
            s, e = H.line_range(node)
            signature = H.text(node, src).splitlines()[0].strip()[:200]
            out.append(SourceUnit(
                id=id_factory(), path=path, line_range=(s, e), language="rust",
                role=role, kind=kind, name=name, framework=framework,
                signature=signature,
                endpoint=endpoint, fingerprint=fingerprint(H.text(node, src)),
            ))

        # ---- handlers ----------------------------------------------------

        def handle_function(node, is_method=False):
            name = _decl_name(node, src) or "?"
            pub = _is_pub(node)
            if pub:
                name = f"pub {name}"
            if is_method:
                emit("callable", "rust_method", name, node)
            else:
                emit("callable", "rust_function", name, node)

        def handle_struct(node):
            name = _decl_name(node, src) or "?"
            emit("schema", "rust_struct", name, node)

        def handle_enum(node):
            name = _decl_name(node, src) or "?"
            emit("schema", "rust_enum", name, node)

        def handle_trait(node):
            name = _decl_name(node, src) or "?"
            emit("callable", "rust_trait", name, node)
            # Recurse into trait body for method signatures
            body = None
            for c in node.children:
                if c.type == "declaration_list":
                    body = c
                    break
            if body:
                _walk_fns_in_block(body, is_method=True)

        def handle_type_alias(node):
            name = _decl_name(node, src) or "?"
            emit("schema", "rust_type_alias", name, node)

        def handle_impl(node):
            """Emit an impl block and its associated methods."""
            trait_of = _impl_trait_name(node, src)
            type_name = _impl_target_name(node, src)
            label = type_name or "?"
            if trait_of:
                label = f"{trait_of} for {type_name or '?'}"
            emit("module", "rust_impl_block", label, node)

            # Extract methods inside the impl body
            for c in node.children:
                if c.type == "declaration_list":
                    _walk_fns_in_block(c, is_method=True)

        def _impl_target_name(node, src) -> str | None:
            """Extract the type being implemented (the type after ``for`` or after ``impl``)."""
            children = list(node.children)
            found_for = False
            # Find the last meaningful type node (the impl target)
            candidate = None
            for c in children:
                if c.type == "for":
                    found_for = True
                    candidate = None
                    continue
                if c.type in ("type", "generic_type", "path_type",
                              "scoped_type_identifier", "scoped_identifier"):
                    candidate = H.text(c, src)
                elif c.type == "declaration_list":
                    break
            return candidate if found_for else candidate

        def handle_module(node):
            name = _decl_name(node, src) or "?"
            emit("module", "rust_module", name, node)
            # Recurse into module body if it has one (inline module)
            for c in node.children:
                if c.type == "declaration_list":
                    _walk_items(c)

        def handle_const(node):
            name = _decl_name(node, src) or "?"
            emit("config", "rust_const", name, node)

        # ---- tree walkers ------------------------------------------------

        def _walk_fns_in_block(parent, is_method=False):
            """Walk a declaration_list for function_items (methods)."""
            for c in parent.children:
                if c.type == "function_item":
                    handle_function(c, is_method=True)
                elif c.type == "macro_invocation":
                    # Skip macros inside impl blocks
                    pass

        def _walk_items(parent):
            """Walk items inside a module or source_file."""
            for c in parent.children:
                if c.type == "function_item":
                    handle_function(c, is_method=False)
                elif c.type == "struct_item":
                    handle_struct(c)
                elif c.type == "enum_item":
                    handle_enum(c)
                elif c.type == "trait_item":
                    handle_trait(c)
                elif c.type == "type_item":
                    handle_type_alias(c)
                elif c.type == "impl_item":
                    handle_impl(c)
                elif c.type == "mod_item":
                    handle_module(c)
                elif c.type == "const_item":
                    handle_const(c)
                elif c.type == "static_item":
                    handle_const(c)  # static items as config role too
                elif c.type in ("declaration_list", "ERROR", "tree_sitter_error"):
                    # Recurse into bodies that may contain items
                    _walk_items(c)
                # Skip: use, extern_crate, macro_invocation, attribute_item, etc.

        _walk_items(tree.root_node)
        return out


if H.have("rust"):
    register(RustExtractor())
