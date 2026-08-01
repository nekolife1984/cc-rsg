"""
Tests for coverage-check.py Issue #158 features.

Covers:
1. Reserved file body check (--require-min-body-lines-for-reserved)
2. Mermaid styling directive check (--no-mermaid-style-check)
3. Placeholder pattern check (--forbid-placeholder-pattern)
"""
from __future__ import annotations

import json
import subprocess
from typing import Any
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "coverage-check.py"

# Reserved files with enough content (≥ 5 body lines) to pass the default threshold
_RESERVED_00 = """# Metadata

- Created: 2026-01-01
- Template: default
- Author: specback
- Status: complete
"""

_RESERVED_99 = """# Unresolved

- No unresolved items remain.
- All questions have been answered.
- Feature gaps are documented.
- Known limitations listed.
- Review scheduled for next sprint.
- Owner assigned.
"""

_RESERVED_TRACE = """# Traceability

- All items are traced to source.
- Cross-references are complete.
- No orphan items found.
- Source-map is up to date.
- Coverage is verified.
- Drift detection passed.
"""


def _minimal_specback(
    tmp_path: Path,
    extra_files: dict[str, str] | None = None,
    reserved_override: dict[str, str] | None = None,
) -> Path:
    """Create a minimal .specback directory with inventory/trace/goal and required base files."""
    specback_dir = tmp_path / ".specback"
    specback_dir.mkdir()
    final_dir = specback_dir / "final"
    final_dir.mkdir()

    inventory: dict[str, Any] = {"units": []}
    (specback_dir / "inventory.json").write_text(json.dumps(inventory), encoding="utf-8")
    trace = {
        "source_units_total": 0, "source_units_covered": 0,
        "source_units_excluded": 0, "source_units_uncovered": 0,
    }
    (specback_dir / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
    (specback_dir / "goal.json").write_text(
        json.dumps({"template": "default"}), encoding="utf-8",
    )

    # Always create a minimal chapter file
    (final_dir / "01-overview.md").write_text("# Overview\n\nSome content.\n", encoding="utf-8")

    if reserved_override:
        # Use caller-specified content for reserved files
        for name in ("00-metadata.md", "99-unresolved.md", "traceability.md"):
            (final_dir / name).write_text(
                reserved_override.get(name, _RESERVED_00 if name == "00-metadata.md"
                                      else _RESERVED_99 if name == "99-unresolved.md"
                                      else _RESERVED_TRACE),
                encoding="utf-8",
            )
    else:
        # Default: all reserved files have sufficient content
        (final_dir / "00-metadata.md").write_text(_RESERVED_00, encoding="utf-8")
        (final_dir / "99-unresolved.md").write_text(_RESERVED_99, encoding="utf-8")
        (final_dir / "traceability.md").write_text(_RESERVED_TRACE, encoding="utf-8")

    if extra_files:
        for name, content in extra_files.items():
            (final_dir / name).write_text(content, encoding="utf-8")

    return specback_dir


def _run_check(specback_dir: Path, **overrides) -> dict:
    """Run coverage-check.py with JSON output and the given overrides.

    Returns the parsed JSON report regardless of exit code.
    ``overrides`` can include keys with value ``True`` for flags that take no
    argument (store_true), and string values for flags that take an argument.
    """
    defaults: dict[str, Any] = {
        "--min-inventory": "0",
        "--min-questions": "0",
        "--min-covered-by-fill": "0",
        "--min-mece-coverage": "0",
        "--min-refs-per-chapter": "0",
        "--min-lines-per-chapter": "0",
        "--min-code-blocks-per-chapter": "0",
        "--min-mermaid-per-chapter": "0",
        "--min-sources-read-per-chapter": "0",
        "--require-min-body-lines-for-reserved": "5",
    }
    defaults.update(overrides)

    cmd = [
        sys.executable, str(SCRIPT),
        "--specback-dir", str(specback_dir),
        "--output-format", "json",
    ]
    for key, val in defaults.items():
        cmd.append(key)
        if val is not True:  # store_true flags don't take a value
            cmd.append(str(val))

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise AssertionError(
            f"Failed to parse JSON output. exit={result.returncode}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )


# ---------------------------------------------------------------------------
# ① --require-min-body-lines-for-reserved
# ---------------------------------------------------------------------------


def test_help_shows_require_min_body_lines_for_reserved():
    """--help includes the --require-min-body-lines-for-reserved flag."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--require-min-body-lines-for-reserved" in result.stdout


def test_reserved_file_body_check_passes_with_sufficient_content(tmp_path):
    """Reserved files with enough body lines (default threshold=5) pass the check."""
    specback_dir = _minimal_specback(tmp_path)
    report = _run_check(specback_dir)
    assert report["reserved_file_body_failures"] == []


def test_reserved_file_body_check_fails_on_empty_file(tmp_path):
    """A reserved file with only the heading line should fail (body=1 < 5)."""
    specback_dir = _minimal_specback(
        tmp_path,
        reserved_override={
            "00-metadata.md": "# Metadata\n",
        },
    )
    report = _run_check(specback_dir)
    assert len(report["reserved_file_body_failures"]) == 1
    assert "00-metadata.md" in report["reserved_file_body_failures"][0]
    assert "body" in report["reserved_file_body_failures"][0].lower()


def test_reserved_file_body_check_threshold_via_cli(tmp_path):
    """Changing --require-min-body-lines-for-reserved adjusts the threshold."""
    # 00-metadata with only 5 body lines and all others with enough
    specback_dir = _minimal_specback(
        tmp_path,
        reserved_override={
            "00-metadata.md": _RESERVED_00,  # 5 body lines
        },
    )
    # Default 5 should pass (5 >= 5)
    report1 = _run_check(specback_dir)
    assert report1["reserved_file_body_failures"] == []

    # Override to 6 should fail (5 < 6)
    report2 = _run_check(specback_dir, **{"--require-min-body-lines-for-reserved": "6"})
    assert len(report2["reserved_file_body_failures"]) == 1
    assert "00-metadata.md" in report2["reserved_file_body_failures"][0]

    # Override to 2 should still pass
    report3 = _run_check(specback_dir, **{"--require-min-body-lines-for-reserved": "2"})
    assert report3["reserved_file_body_failures"] == []


def test_reserved_file_body_check_multiple_failures(tmp_path):
    """Multiple empty reserved files each report their own failure."""
    specback_dir = _minimal_specback(
        tmp_path,
        reserved_override={
            "00-metadata.md": "# Metadata\n",
            "99-unresolved.md": "# Unresolved\n",
            "traceability.md": "# Traceability\n",
        },
    )
    report = _run_check(specback_dir)
    assert len(report["reserved_file_body_failures"]) == 3


# ---------------------------------------------------------------------------
# ② --no-mermaid-style-check
# ---------------------------------------------------------------------------


def test_help_shows_no_mermaid_style_check():
    """--help includes the --no-mermaid-style-check flag."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--no-mermaid-style-check" in result.stdout


def test_mermaid_styling_check_passes_on_clean_mermaid(tmp_path):
    """A mermaid block without styling directives passes."""
    content = """# Chapter

```mermaid
graph TD;
    A-->B;
    B-->C;
```
"""
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert report["mermaid_style_violations"] == []


def test_mermaid_styling_check_detects_style_fill(tmp_path):
    """A mermaid block with style A fill:#f00 is detected."""
    content = """# Chapter

```mermaid
graph TD;
    A-->B;
    style A fill:#f00;
```
"""
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert len(report["mermaid_style_violations"]) == 1
    v = report["mermaid_style_violations"][0]
    assert "style A fill" in v["line_text"]
    assert v["file"] == "01-overview.md"


def test_mermaid_styling_check_detects_classDef_fill(tmp_path):
    """A mermaid block with classDef foo fill:#0f0 is detected."""
    content = """# Chapter

```mermaid
classDef foo fill:#0f0,stroke:#333;
```
"""
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert len(report["mermaid_style_violations"]) == 1


def test_mermaid_styling_check_detects_stroke_and_color(tmp_path):
    """Stroke and color directives are detected."""
    content = """# Chapter

```mermaid
graph LR;
    A-->B;
    linkStyle default stroke:#00f;
```
"""
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert len(report["mermaid_style_violations"]) == 1
    assert "stroke:" in report["mermaid_style_violations"][0]["line_text"]


def test_mermaid_styling_check_detects_multiple_violations(tmp_path):
    """Multiple styling directives are all detected."""
    content = """# Chapter

```mermaid
graph TD;
    style A fill:#f00;
    style B fill:#0f0;
    style C fill:#00f;
```
"""
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert len(report["mermaid_style_violations"]) == 3


def test_mermaid_styling_check_can_be_disabled(tmp_path):
    """With --no-mermaid-style-check, styling violations are ignored."""
    content = """# Chapter

```mermaid
style A fill:#bad;
```
"""
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir, **{"--no-mermaid-style-check": True})
    assert report["mermaid_style_violations"] == []


# ---------------------------------------------------------------------------
# ③ --forbid-placeholder-pattern
# ---------------------------------------------------------------------------


def test_help_shows_forbid_placeholder_pattern():
    """--help includes the --forbid-placeholder-pattern flag."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--forbid-placeholder-pattern" in result.stdout


def test_placeholder_check_passes_on_clean_content(tmp_path):
    """A chapter without placeholder text passes."""
    content = "# Overview\n\nAll sections are complete.\n"
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert report["placeholder_violations"] == []


def test_placeholder_check_detects_todo(tmp_path):
    """TODO is detected as a placeholder."""
    content = "# Overview\n\nTODO: add architecture diagram\n"
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert len(report["placeholder_violations"]) == 1
    v = report["placeholder_violations"][0]
    assert v["matched"] == "TODO"


def test_placeholder_check_detects_fixme(tmp_path):
    """FIXME is detected as a placeholder."""
    content = "# Overview\n\nFIXME: this section needs work\n"
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert len(report["placeholder_violations"]) == 1
    assert report["placeholder_violations"][0]["matched"] == "FIXME"


def test_placeholder_check_detects_phase_pattern(tmp_path):
    """'Phase 6 で記入予定' is detected."""
    content = "# Overview\n\nPhase 6 で記入予定\n"
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir)
    assert len(report["placeholder_violations"]) == 1
    assert "Phase 6" in report["placeholder_violations"][0]["matched"]


def test_placeholder_check_extra_pattern_via_cli(tmp_path):
    """Extra patterns via --forbid-placeholder-pattern are also detected."""
    content = "# Overview\n\nHACK: temporary workaround\n"
    specback_dir = _minimal_specback(tmp_path, extra_files={"01-overview.md": content})
    report = _run_check(specback_dir, **{"--forbid-placeholder-pattern": "HACK"})
    # Built-in 'TODO' and 'FIXME' are NOT in this content; 'HACK' should match
    assert len(report["placeholder_violations"]) == 1
    assert report["placeholder_violations"][0]["matched"] == "HACK"
