"""M6 acceptance: C++ extractor (tree-sitter based)."""
from __future__ import annotations

import pytest

from source_map_v2 import extractors
from source_map_v2.model import IdFactory


def _ext(lang, src, path):
    e = extractors.get_extractor(lang)
    return e.extract(path, src, IdFactory()) if e else None


# ---------------------------------------------------------------------------
# C++: class, struct, enum, typedef, function, method, virtual, namespace
# ---------------------------------------------------------------------------
CPP_SAMPLE = """\
class MyClass {
public:
    int getValue() const { return 42; }
    virtual void doSomething() = 0;
};

struct Config {
    int timeout;
};

enum class Color { RED, GREEN, BLUE };

using StringList = int;

void freeFunc() {}

namespace MyNS {
    class Internal {};
}

template<typename T>
class Container {
    T data;
};
"""


@pytest.mark.skipif(extractors.get_extractor("cpp") is None, reason="no cpp grammar")
def test_cpp_types_funcs():
    units = _ext("cpp", CPP_SAMPLE, "src/lib.cpp")
    by = {(u.kind, u.name) for u in units}

    # Classes
    assert ("cpp_class", "MyClass") in by
    assert ("cpp_struct", "Config") in by
    assert ("cpp_enum_class", "Color") in by
    assert ("cpp_typedef", "StringList") in by
    assert ("cpp_namespace", "MyNS") in by
    assert ("cpp_template_class", "Container") in by

    # Functions / methods
    assert ("cpp_function", "freeFunc") in by
    assert ("cpp_method", "getValue") in by or \
           ("cpp_virtual_method", "getValue") in by
    assert ("cpp_virtual_method", "doSomething") in by
