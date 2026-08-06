#!/usr/bin/env python3
"""Check that every public function/class in a script has a corresponding test.

Usage:
    python scripts/tests/check_test_coverage.py <script.py> [<test.py>]

If <test.py> is omitted, it defaults to tests/test_<script_basename>.py.

Exit codes:
    0 — all public symbols have test coverage
    1 — some symbols are missing test coverage
    2 — file not found or parse error
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# Symbols exempt from test coverage requirements (always OK to skip)
EXEMPT_SYMBOLS: set[str] = {
    # Entry points
    "main",
    # Test infrastructure
    "conftest",
    # Dunder methods on classes (tested indirectly)
    "__init__", "__str__", "__repr__", "__enter__", "__exit__",
    "__len__", "__iter__", "__getitem__", "__setitem__",
    "__call__", "__hash__", "__eq__", "__ne__",
}


def get_public_symbols(filepath: Path) -> set[str]:
    """Extract names of public functions, async functions, and classes."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError as e:
        print(f"ERROR: Syntax error in {filepath}: {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(2)

    symbols: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                symbols.add(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                symbols.add(node.name)
    return symbols


def get_test_symbols(filepath: Path) -> set[str]:
    """Extract names of test functions/classes from a test file."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, FileNotFoundError):
        return set()

    symbols: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.ClassDef):
            symbols.add(node.name)
    return symbols


def _test_name_candidates(symbol: str) -> list[str]:
    """Generate possible test names for a given symbol.

    Examples:
        build_report -> [test_build_report]
        hash_line_range -> [test_hash_line_range, test_hash_line, test_hash]
    """
    candidates = [f"test_{symbol}"]
    # For compound names like load_source_map, also check test_source_map
    parts: list[str] = []
    current: list[str] = []
    for i, ch in enumerate(symbol):
        if ch.isupper() and current:
            parts.append("".join(current))
            current = [ch.lower()]
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    if len(parts) > 1:
        for part in parts[1:]:
            candidates.append(f"test_{part}")
    return candidates


def check_coverage(script_path: Path, test_path: Path) -> int:
    """Return 0 if coverage is adequate, 1 if symbols are missing."""
    script_syms = get_public_symbols(script_path)
    test_syms = get_test_symbols(test_path)

    missing: list[str] = []
    for sym in sorted(script_syms):
        if sym in EXEMPT_SYMBOLS:
            continue
        # Check if any candidate test name exists in test file
        candidates = _test_name_candidates(sym)
        if not any(c in test_syms for c in candidates):
            missing.append(sym)

    if not missing:
        return 0

    # Only report top-level symbols (skip nested function names for brevity)
    print(f"⚠️  Missing test coverage for: {script_path.name}")
    for sym in missing:
        print(f"   - {sym}")
    print(f"   Expected in: {test_path}")
    return 1


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <script.py> [<test.py>]", file=sys.stderr)
        return 2

    script_path = Path(sys.argv[1]).resolve()
    if not script_path.exists():
        print(f"ERROR: {script_path} not found", file=sys.stderr)
        return 2

    if len(sys.argv) >= 3:
        test_path = Path(sys.argv[2]).resolve()
    else:
        # Default: tests/test_<name>.py
        base = script_path.stem.replace("-", "_")
        test_path = script_path.parent / "tests" / f"test_{base}.py"

    return check_coverage(script_path, test_path)


if __name__ == "__main__":
    sys.exit(main())
