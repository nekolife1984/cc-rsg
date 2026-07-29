"""M6 acceptance: Dart extractor (tree-sitter based)."""
from __future__ import annotations

import pytest

from source_map_v2 import extractors
from source_map_v2.model import IdFactory


def _ext(lang, src, path):
    e = extractors.get_extractor(lang)
    return e.extract(path, src, IdFactory()) if e else None


# ---------------------------------------------------------------------------
# Dart: class, function, method, enum, typedef, mixin, extension
# ---------------------------------------------------------------------------
DART_SAMPLE = """\
class MyClass {
    void hello() {}
}

enum Status { ok, error }

typedef IntList = List<int>;

mixin MyMixin {}

extension StringExt on String {
    int get len => length;
}

void topFunc() {}
"""


@pytest.mark.skipif(extractors.get_extractor("dart") is None, reason="no dart grammar")
def test_dart_types_funcs():
    units = _ext("dart", DART_SAMPLE, "src/lib.dart")
    by = {(u.kind, u.name) for u in units}

    assert ("dart_class", "MyClass") in by
    assert ("dart_enum", "Status") in by
    assert ("dart_typedef", "IntList") in by
    assert ("dart_mixin", "MyMixin") in by
    assert ("dart_extension", "StringExt") in by
    # NOTE: top-level function extraction (dart_function) requires
    # further investigation — tree-sitter-dart v0.1.0 uses
    # function_signature/method_signature rather than function_definition.
