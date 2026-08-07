"""Smoke tests for fix-refs.py (Phase 7b — REF Auto-Fix).

Tests include SRC-ID support (Issue #224): verification that SRC-format
refs are correctly detected and skipped by the auto-fix logic.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "fix-refs.py"

# Import the regex patterns from the script for unit testing
# We re-import the module each time to get fresh constants
def _import_fix_refs():
    """Import fix-refs.py as a module to access its constants."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("fix_refs_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=30,
    )


# ═══════════════════════════════════════════════════════════════════════════
# CLI smoke tests
# ═══════════════════════════════════════════════════════════════════════════


def test_help_includes_specback_dir():
    result = _run("--help")
    assert result.returncode == 0
    assert "--specback-dir" in result.stdout


def test_help_includes_output_dir():
    result = _run("--help")
    assert result.returncode == 0
    assert "--output-dir" in result.stdout


def test_help_includes_apply():
    result = _run("--help")
    assert result.returncode == 0
    assert "--apply" in result.stdout


def test_help_includes_check():
    result = _run("--help")
    assert result.returncode == 0
    assert "--check" in result.stdout


def test_args_with_output_dir():
    """--output-dir combined with --help doesn't error."""
    result = _run("--output-dir", "/tmp/x", "--help")
    assert result.returncode == 0


# ═══════════════════════════════════════════════════════════════════════════
# SRC-ID regex tests (Issue #224)
# ═══════════════════════════════════════════════════════════════════════════


class TestSrcRefRe:
    """Verify SRC_REF_RE correctly matches <!-- REF: SRC-NNNN -->."""

    def test_matches_src_id(self):
        mod = _import_fix_refs()
        matches = mod.SRC_REF_RE.findall("<!-- REF: SRC-0142 -->")
        assert matches == ["SRC-0142"]

    def test_matches_src_id_with_spaces(self):
        mod = _import_fix_refs()
        matches = mod.SRC_REF_RE.findall("<!-- REF:   SRC-0001   -->")
        assert matches == ["SRC-0001"]

    def test_does_not_match_path_line(self):
        mod = _import_fix_refs()
        matches = mod.SRC_REF_RE.findall(
            "<!-- REF: src/errors.py:1-50 -->"
        )
        assert matches == []

    def test_does_not_match_invalid_format(self):
        mod = _import_fix_refs()
        matches = mod.SRC_REF_RE.findall("<!-- REF: SRC-XXX -->")
        assert matches == []

    def test_does_not_match_plain_path(self):
        mod = _import_fix_refs()
        matches = mod.SRC_REF_RE.findall("<!-- REF: app/models/user.rb -->")
        assert matches == []


class TestFindRefsInFileSrcId:
    """Verify SRC-ID refs are detected with is_src_id=True."""

    def test_src_id_ref_detected(self, tmp_path):
        mod = _import_fix_refs()
        spec_file = tmp_path / "01-overview.md"
        spec_file.write_text(
            "<!-- REF: SRC-0142 -->\n", encoding="utf-8"
        )
        refs = mod.find_refs_in_file(spec_file)
        assert len(refs) == 1
        assert refs[0]["is_src_id"] is True
        assert refs[0]["ref_path"] == "SRC-0142"

    def test_src_id_and_path_line_both_detected(self, tmp_path):
        mod = _import_fix_refs()
        spec_file = tmp_path / "02-data.md"
        spec_file.write_text(
            "<!-- REF: SRC-0142 -->\n"
            "<!-- REF: app/models/user.rb:42 -->\n",
            encoding="utf-8",
        )
        refs = mod.find_refs_in_file(spec_file)
        assert len(refs) == 2
        assert refs[0]["is_src_id"] is True
        assert refs[0]["ref_path"] == "SRC-0142"
        assert refs[1]["is_src_id"] is False
        assert refs[1]["ref_path"] == "app/models/user.rb"


class TestSrcRefReInRefRe:
    """Verify REF_RE does NOT match SRC-ID format (no false overlap)."""

    def test_ref_re_does_not_match_src_id(self):
        mod = _import_fix_refs()
        matches = mod.REF_RE.findall("<!-- REF: SRC-0142 -->")
        assert matches == []
