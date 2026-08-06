"""M6 acceptance: Swift extractor (tree-sitter based, v0.0.1 grammar)."""
from __future__ import annotations

import pytest

from source_map_v2 import extractors
from source_map_v2.model import IdFactory


def _ext(lang, src, path):
    e = extractors.get_extractor(lang)
    return e.extract(path, src, IdFactory()) if e else None


# ---------------------------------------------------------------------------
# Swift: class, struct, enum, protocol, function, method
# ---------------------------------------------------------------------------
SWIFT_SAMPLE = """\
class MyClass {
    func doSomething() {}
}

struct Point {
    var x: Int
}

enum Color { case red, blue }

protocol Drawable {
    func render()
}

actor MyActor {
    func work() {}
}

extension String {
    var len: Int { count }
}

func topLevel() {}
"""


@pytest.mark.skipif(extractors.get_extractor("swift") is None, reason="no swift grammar")
def test_swift_types_funcs():
    units = _ext("swift", SWIFT_SAMPLE, "src/lib.swift")
    by = {(u.kind, u.name) for u in units}

    assert ("swift_class", "MyClass") in by
    assert ("swift_struct", "Point") in by
    assert ("swift_enum", "Color") in by
    assert ("swift_protocol", "Drawable") in by
    assert ("swift_function", "topLevel") in by
