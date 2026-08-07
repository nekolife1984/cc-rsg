"""Tests for build-trace.py SRC-ID support (Issue #224).

Covers:
- SRC_REF_RE regex pattern matching
- scan_drafts_for_refs() with units_by_id resolution
- Unresolved SRC-ID (not in source-map) fallback
- Mixed SRC-ID + path:line refs on same line
- units_by_id=None graceful fallback
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# We import the script as a module for unit-testing internals
SCRIPT = Path(__file__).resolve().parent.parent / "build-trace.py"


def _import_build_trace():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_trace_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_source_map(units: list[dict]) -> Path:
    """Create a temporary source-map.json and return its path."""
    import tempfile
    path = Path(tempfile.mktemp(suffix=".json"))
    path.write_text(json.dumps({"units": units}), encoding="utf-8")
    return path


# ═══════════════════════════════════════════════════════════════════════════
# SRC_REF_RE: regex unit tests
# ═══════════════════════════════════════════════════════════════════════════


class TestSrcRefRe:
    def test_matches_src_id(self):
        mod = _import_build_trace()
        matches = mod.SRC_REF_RE.findall("<!-- REF: SRC-0142 -->")
        assert matches == ["SRC-0142"]

    def test_matches_src_id_with_spaces(self):
        mod = _import_build_trace()
        matches = mod.SRC_REF_RE.findall("<!-- REF:   SRC-0001   -->")
        assert matches == ["SRC-0001"]

    def test_does_not_match_path_line(self):
        mod = _import_build_trace()
        matches = mod.SRC_REF_RE.findall("<!-- REF: src/errors.py:1-50 -->")
        assert matches == []

    def test_does_not_match_invalid_id(self):
        mod = _import_build_trace()
        matches = mod.SRC_REF_RE.findall("<!-- REF: SRC-XXX -->")
        assert matches == []

    def test_matches_multiple_on_same_line(self):
        mod = _import_build_trace()
        matches = mod.SRC_REF_RE.findall(
            "<!-- REF: SRC-0001 --> and <!-- REF: SRC-0142 -->"
        )
        assert matches == ["SRC-0001", "SRC-0142"]


# ═══════════════════════════════════════════════════════════════════════════
# scan_drafts_for_refs: SRC-ID resolution
# ═══════════════════════════════════════════════════════════════════════════


class TestScanDraftsForRefsSrcId:
    def test_resolves_known_src_id(self, tmp_path):
        """SRC-ID that exists in units_by_id should resolve to path+line."""
        mod = _import_build_trace()
        units_by_id = {
            "SRC-0142": {
                "id": "SRC-0142",
                "path": "app/models/issue.rb",
                "line_range": [10, 42],
                "kind": "class",
                "name": "Issue",
            }
        }
        drafts_dir = tmp_path / "drafts"
        drafts_dir.mkdir()
        (drafts_dir / "01-overview.md").write_text(
            "# Chapter\n\n<!-- REF: SRC-0142 -->\n", encoding="utf-8"
        )
        refs = mod.scan_drafts_for_refs(drafts_dir, units_by_id)
        assert len(refs) == 1
        assert refs[0]["ref_path"] == "app/models/issue.rb"
        assert refs[0]["ref_start"] == 10
        assert refs[0]["ref_end"] == 42
        assert refs[0]["draft_file"] == "01-overview.md"

    def test_unresolved_src_id_gets_zero_range(self, tmp_path):
        """SRC-ID not in units_by_id should record with ref_start=ref_end=0."""
        mod = _import_build_trace()
        units_by_id: dict = {}  # empty — no source-map available
        drafts_dir = tmp_path / "drafts"
        drafts_dir.mkdir()
        (drafts_dir / "01-overview.md").write_text(
            "<!-- REF: SRC-9999 -->\n", encoding="utf-8"
        )
        refs = mod.scan_drafts_for_refs(drafts_dir, units_by_id)
        assert len(refs) == 1
        assert refs[0]["ref_path"] == "SRC-9999"
        assert refs[0]["ref_start"] == 0
        assert refs[0]["ref_end"] == 0

    def test_null_units_by_id_fallback(self, tmp_path):
        """units_by_id=None should treat SRC-ID refs as unresolved."""
        mod = _import_build_trace()
        drafts_dir = tmp_path / "drafts"
        drafts_dir.mkdir()
        (drafts_dir / "01-overview.md").write_text(
            "<!-- REF: SRC-0142 -->\n", encoding="utf-8"
        )
        refs = mod.scan_drafts_for_refs(drafts_dir, None)
        assert len(refs) == 1
        assert refs[0]["ref_path"] == "SRC-0142"
        assert refs[0]["ref_start"] == 0
        assert refs[0]["ref_end"] == 0

    def test_mixed_src_id_and_path_line_on_same_line(self, tmp_path):
        """Both SRC-ID and path:line refs on the same line should be captured."""
        mod = _import_build_trace()
        units_by_id = {
            "SRC-0142": {
                "id": "SRC-0142",
                "path": "app/models/issue.rb",
                "line_range": [10, 42],
                "kind": "class",
                "name": "Issue",
            }
        }
        drafts_dir = tmp_path / "drafts"
        drafts_dir.mkdir()
        (drafts_dir / "01-overview.md").write_text(
            "refs: <!-- REF: SRC-0142 --> and <!-- REF: app/errors.py:1-50 -->\n",
            encoding="utf-8",
        )
        refs = mod.scan_drafts_for_refs(drafts_dir, units_by_id)
        assert len(refs) == 2, f"Expected 2 refs, got {len(refs)}"
        # SRC-ID should be first (scanned before path:line)
        assert refs[0]["ref_path"] == "app/models/issue.rb"
        assert refs[1]["ref_path"] == "app/errors.py"

    def test_multiple_src_ids_on_same_line(self, tmp_path):
        """Multiple SRC-ID refs on the same line should all be captured."""
        mod = _import_build_trace()
        units_by_id = {
            "SRC-0001": {"id": "SRC-0001", "path": "src/a.py", "line_range": [1, 10], "kind": "class", "name": "A"},
            "SRC-0002": {"id": "SRC-0002", "path": "src/b.py", "line_range": [5, 20], "kind": "class", "name": "B"},
        }
        drafts_dir = tmp_path / "drafts"
        drafts_dir.mkdir()
        (drafts_dir / "01-overview.md").write_text(
            "refs: <!-- REF: SRC-0001 --> and <!-- REF: SRC-0002 -->\n",
            encoding="utf-8",
        )
        refs = mod.scan_drafts_for_refs(drafts_dir, units_by_id)
        assert len(refs) == 2, f"Expected 2 refs, got {len(refs)}"
        paths = [r["ref_path"] for r in refs]
        assert "src/a.py" in paths
        assert "src/b.py" in paths

    def test_skips_empty_drafts_dir(self, tmp_path):
        """Empty drafts directory should return empty list."""
        mod = _import_build_trace()
        drafts_dir = tmp_path / "empty_drafts"
        drafts_dir.mkdir()
        refs = mod.scan_drafts_for_refs(drafts_dir, {})
        assert refs == []
