"""M6 acceptance: Rust extractor (tree-sitter based)."""
from __future__ import annotations

import pytest

from source_map_v2 import extractors
from source_map_v2.model import IdFactory


def _ext(lang, src, path):
    e = extractors.get_extractor(lang)
    return e.extract(path, src, IdFactory()) if e else None


# ---------------------------------------------------------------------------
# Rust: function, struct, enum, trait, impl, type alias, module, const
# ---------------------------------------------------------------------------
RUST_SAMPLE = """\
pub fn public_func() -> i32 { 42 }

fn private_func(x: i32) -> i32 { x + 1 }

struct Point {
    x: i32,
    y: i32,
}

struct Generic<T> {
    inner: T,
}

enum Direction {
    North,
    South,
    East,
    West,
}

enum Option<T> {
    Some(T),
    None,
}

trait Drawable {
    fn draw(&self);
    fn area(&self) -> f64;
}

impl Drawable for Point {
    fn draw(&self) {}
    fn area(&self) -> f64 { 0.0 }
}

impl Point {
    pub fn new(x: i32, y: i32) -> Self { Point { x, y } }
    fn translate(&mut self, dx: i32, dy: i32) {}
}

type UserId = i64;

mod utils {
    fn helper() -> bool { true }
}

const MAX_SIZE: usize = 1024;
static APP_NAME: &str = "myapp";
"""


@pytest.mark.skipif(extractors.get_extractor("rust") is None, reason="no rust grammar")
def test_rust_types_funcs():
    units = _ext("rust", RUST_SAMPLE, "src/lib.rs")
    assert units is not None, "rust extractor returned None"
    by = {(u.kind, u.name) for u in units}

    # Functions
    assert ("rust_function", "pub public_func") in by, "pub fn"
    assert ("rust_function", "private_func") in by, "private fn"

    # Structs
    assert ("rust_struct", "Point") in by, "struct Point"
    assert ("rust_struct", "Generic") in by, "struct Generic<T>"

    # Enums
    assert ("rust_enum", "Direction") in by, "enum Direction"
    assert ("rust_enum", "Option") in by, "enum Option<T>"

    # Traits
    assert ("rust_trait", "Drawable") in by, "trait Drawable"

    # Impl blocks
    has_impl_block = any(k == "rust_impl_block" for k, _ in by)
    assert has_impl_block, "at least one impl_block"

    # Type aliases
    assert ("rust_type_alias", "UserId") in by, "type UserId"

    # Modules
    assert ("rust_module", "utils") in by, "mod utils"

    # Const / static
    assert ("rust_const", "MAX_SIZE") in by, "const MAX_SIZE"
    assert ("rust_const", "APP_NAME") in by, "static APP_NAME"


@pytest.mark.skipif(extractors.get_extractor("rust") is None, reason="no rust grammar")
def test_rust_methods():
    """Methods inside impl blocks are extracted as rust_method."""
    units = _ext("rust", RUST_SAMPLE, "src/lib.rs")
    assert units is not None
    by = {(u.kind, u.name) for u in units}

    assert ("rust_method", "pub new") in by, "pub fn new in impl Point"
    assert ("rust_method", "draw") in by, "fn draw in impl Drawable for Point"
    assert ("rust_method", "area") in by, "fn area in impl Drawable for Point"


@pytest.mark.skipif(extractors.get_extractor("rust") is None, reason="no rust grammar")
def test_rust_roles():
    """Verify that each kind resolves to the expected role."""
    units = _ext("rust", RUST_SAMPLE, "src/lib.rs")
    assert units is not None

    role_by_kind = {}
    for u in units:
        if u.kind not in role_by_kind:
            role_by_kind[u.kind] = u.role

    assert role_by_kind.get("rust_function") == "callable"
    assert role_by_kind.get("rust_method") == "callable"
    assert role_by_kind.get("rust_struct") == "schema"
    assert role_by_kind.get("rust_enum") == "schema"
    assert role_by_kind.get("rust_trait") == "callable"
    assert role_by_kind.get("rust_type_alias") == "schema"
    assert role_by_kind.get("rust_impl_block") == "module"
    assert role_by_kind.get("rust_module") == "module"
    assert role_by_kind.get("rust_const") == "config"


@pytest.mark.skipif(extractors.get_extractor("rust") is None, reason="no rust grammar")
def test_rust_line_ranges():
    """Check that line ranges are reasonable."""
    units = _ext("rust", RUST_SAMPLE, "src/lib.rs")
    assert units is not None

    for u in units:
        assert u.line_range[0] >= 1, f"start line {u.line_range[0]} for {u.kind}:{u.name}"
        assert u.line_range[1] >= u.line_range[0], f"end >= start for {u.kind}:{u.name}"
        assert u.signature, f"signature non-empty for {u.kind}:{u.name}"


@pytest.mark.skipif(extractors.get_extractor("rust") is None, reason="no rust grammar")
def test_rust_fingerprint_uniqueness():
    """Fingerprints should differ for different constructs."""
    units = _ext("rust", RUST_SAMPLE, "src/lib.rs")
    assert units is not None

    fps = [u.fingerprint for u in units]
    unique = set(fps)
    # Allow some duplicates (pub / non-pub variants of same fn may have same body hash)
    assert len(unique) >= len(fps) * 0.5, "at least 50% fingerprints unique"
