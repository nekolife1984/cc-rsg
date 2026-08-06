"""tree-sitter helpers shared by the language extractors.

tree-sitter is an OPTIONAL dependency (design risk #1): if it (or a grammar) is
not installed, ``have(language)`` returns False and the language extractor does
not register, so the pipeline falls back to file-level units + a loud warning.
"""

from __future__ import annotations

import importlib
from functools import lru_cache

try:
    import tree_sitter as _ts
    _HAVE_CORE = True
except ImportError:
    _HAVE_CORE = False


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "websocket", "route"}

# Languages whose extractor requires a tree-sitter grammar (guarded registration).
# When the grammar is missing, the extractor module imports cleanly but does not
# register, so the pipeline falls back to file-level units with a warning.
TREE_SITTER_BACKED: frozenset[str] = frozenset({
    "python", "typescript", "tsx", "javascript", "ruby", "php", "java",
    "csharp", "kotlin", "go", "c", "cpp", "dart", "swift", "rust",
})

# pip package providing the grammar for each tree-sitter backed language.
# (csharp differs: the package is ``tree-sitter-c-sharp``, not ``tree-sitter-csharp``.)
PIP_PACKAGE: dict[str, str] = {
    "python": "tree-sitter-python",
    "typescript": "tree-sitter-typescript",
    "tsx": "tree-sitter-typescript",
    "javascript": "tree-sitter-typescript",
    "ruby": "tree-sitter-ruby",
    "php": "tree-sitter-php",
    "java": "tree-sitter-java",
    "csharp": "tree-sitter-c-sharp",
    "kotlin": "tree-sitter-kotlin",
    "go": "tree-sitter-go",
    "c": "tree-sitter-c",
    "cpp": "tree-sitter-cpp",
    "dart": "tree-sitter-dart",
    "swift": "tree-sitter-swift",
    "rust": "tree-sitter-rust",
}

# language -> (python module name, function returning the grammar Language).
# Some grammars expose more than one language (typescript -> tsx, javascript);
# this mapping mirrors the old if/elif chain in ``_parser``.
_LANG_MODULE_FN: dict[str, tuple[str, str]] = {
    "python": ("tree_sitter_python", "language"),
    "ruby": ("tree_sitter_ruby", "language"),
    "typescript": ("tree_sitter_typescript", "language_typescript"),
    "tsx": ("tree_sitter_typescript", "language_tsx"),
    "javascript": ("tree_sitter_typescript", "language_typescript"),
    "php": ("tree_sitter_php", "language_php"),
    "java": ("tree_sitter_java", "language"),
    "csharp": ("tree_sitter_c_sharp", "language"),
    "kotlin": ("tree_sitter_kotlin", "language"),
    "go": ("tree_sitter_go", "language"),
    "c": ("tree_sitter_c", "language"),
    "cpp": ("tree_sitter_cpp", "language"),
    "dart": ("tree_sitter_dart", "language"),
    "swift": ("tree_sitter_swift", "language"),
    "rust": ("tree_sitter_rust", "language"),
}


def _load_language(language: str):
    """Import the grammar module and return a ``tree_sitter.Language``.

    Raises ImportError when the grammar (or core) is not installed, ValueError
    when the grammar's Language version is incompatible with the installed
    core, or any other exception raised by the grammar package at load time.
    """
    mod_name, fn_name = _LANG_MODULE_FN[language]
    mod = importlib.import_module(mod_name)
    return _ts.Language(getattr(mod, fn_name)())


@lru_cache(maxsize=None)
def _parser(language: str):
    if not _HAVE_CORE:
        return None
    try:
        return _ts.Parser(_load_language(language))
    except Exception:
        return None


# install_state() return values.
STATE_OK = "ok"  # parser loads successfully
STATE_MISSING = "missing"  # core or grammar not installed
STATE_INCOMPATIBLE = "incompatible"  # grammar Language version vs core mismatch
STATE_IMPORT_ERROR = "import-error"  # grammar installed but fails to load


@lru_cache(maxsize=None)
def install_state(language: str) -> str:
    """Diagnose why ``have(language)`` may be False.

    Unlike ``have()`` — which swallows every failure and returns False —
    this distinguishes *missing* grammars from *installed but broken* ones
    (Issue #123).  Returns one of the STATE_* constants:

    - STATE_OK:           parser loads
    - STATE_MISSING:      tree-sitter core or the grammar is not installed
    - STATE_INCOMPATIBLE: grammar installed, but its Language version is not
                          supported by the installed core.  This happens at
                          ``Parser()`` creation, not ``Language()``: newer
                          grammars ship Language version 15 while core 0.23.x
                          only supports v13-14 (e.g. tree-sitter-python 0.25.x,
                          tree-sitter-rust 0.24.x) — ``pip install`` alone
                          will NOT fix this; pin core >= 0.24 in
                          requirements.txt (verified: core 0.25.1 + latest
                          grammars works on Python 3.11/3.12)
    - STATE_IMPORT_ERROR: grammar installed but fails to load for another
                          reason (module-level bug in the grammar package)
    """
    if language not in _LANG_MODULE_FN:
        return STATE_MISSING
    if not _HAVE_CORE:
        return STATE_MISSING
    try:
        # Check at Parser() level, not Language() level: a Language object
        # can be constructed from an unsupported version, but Parser() then
        # raises "Incompatible Language version N".  have() is the source of
        # truth for extractor registration, so install_state must agree.
        _ts.Parser(_load_language(language))
        return STATE_OK
    except ImportError:
        return STATE_MISSING
    except ValueError as exc:
        if "version" in str(exc).lower():
            return STATE_INCOMPATIBLE
        return STATE_IMPORT_ERROR
    except Exception:
        return STATE_IMPORT_ERROR


def name_of(node, src: bytes) -> str:
    """Best-effort declaration name: the `name` field, else first identifier child."""
    nm = node.child_by_field_name("name")
    if nm is not None:
        return text(nm, src)
    for c in node.children:
        if c.type in ("identifier", "name", "type_identifier", "field_identifier", "simple_identifier"):
            return text(c, src)
    return "?"


def have(language: str) -> bool:
    return _parser(language) is not None


def parse(language: str, source: str):
    p = _parser(language)
    if p is None:
        raise RuntimeError(f"tree-sitter parser for {language!r} unavailable")
    return p.parse(source.encode("utf-8", "replace")), source.encode("utf-8", "replace")


def text(node, src_bytes: bytes) -> str:
    return src_bytes[node.start_byte:node.end_byte].decode("utf-8", "replace")


def field(node, name: str):
    return node.child_by_field_name(name)


def line_range(node) -> tuple[int, int]:
    return (node.start_point[0] + 1, node.end_point[0] + 1)


_STRING_TYPES = {
    "string", "string_literal", "encapsed_string",
    "interpreted_string_literal", "raw_string_literal",
}
_STRING_CONTENT_TYPES = {"string_content", "string_fragment"}


def _string_value(node, src_bytes: bytes) -> str:
    for c in node.children:
        if c.type in _STRING_CONTENT_TYPES:
            return text(c, src_bytes)
    return text(node, src_bytes).strip("\"'`@")


def _first_string_descendant(node):
    for c in node.children:
        if c.type in _STRING_TYPES:
            return c
        found = _first_string_descendant(c)
        if found is not None:
            return found
    return None


def first_string_arg(call_node, src_bytes: bytes) -> str | None:
    """First string argument of a call, descending through arg wrappers.

    Handles both direct-string args (Python/TS: ``f("/x")``) and wrapped args
    (PHP: ``argument -> string -> string_content``).
    """
    args = field(call_node, "arguments")
    if not args:
        return None
    for a in args.children:
        if a.type in ("(", ")", ","):
            continue
        if a.type in _STRING_TYPES:
            return _string_value(a, src_bytes)
        found = _first_string_descendant(a)
        if found is not None:
            return _string_value(found, src_bytes)
    return None
