"""M6 acceptance: C extractor (tree-sitter based)."""
from __future__ import annotations

import pytest

from source_map_v2 import extractors
from source_map_v2.model import IdFactory


def _ext(lang, src, path):
    e = extractors.get_extractor(lang)
    return e.extract(path, src, IdFactory()) if e else None


# ---------------------------------------------------------------------------
# C: function, struct, enum, union, typedef
# ---------------------------------------------------------------------------
C_SAMPLE = """\
struct Point {
    int x;
    int y;
};

enum Status { OK, ERROR };

union Data {
    int i;
    float f;
};

typedef struct {
    char name[64];
} Person;

int add(int a, int b) {
    return a + b;
}

static void helper() {}
"""


@pytest.mark.skipif(extractors.get_extractor("c") is None, reason="no c grammar")
def test_c_types_funcs():
    units = _ext("c", C_SAMPLE, "src/lib.c")
    by = {(u.kind, u.name) for u in units}

    assert ("c_struct", "Point") in by
    assert ("c_enum", "Status") in by
    assert ("c_union", "Data") in by
    assert ("c_typedef", "Person") in by
    assert ("c_function", "add") in by
    assert ("c_function", "helper") in by
