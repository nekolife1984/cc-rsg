"""Tests for adws/adw_specback_changespec.py — Phase 7c ChangeSpec ADW."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADW_CSPEC = ROOT / "adws" / "adw_specback_changespec.py"


def test_imports() -> None:
    """Verify the ADW script can be imported without errors."""
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{ROOT}')
from adws.adw_specback_changespec import (
    run_changespec, build_parser, _generate_changespec_md, ChangeSpecOutput,
)
print('  ✅ ADW changespec imports OK')
"""],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"Import failed:\n{result.stderr}"


def test_help() -> None:
    """Verify --help works."""
    result = subprocess.run(
        [sys.executable, str(ADW_CSPEC), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "specback ADW" in result.stdout
    assert "--target" in result.stdout


def test_no_specback_dir(tmp_path: Path) -> None:
    """Verify exits with error when .specback dir doesn't exist."""
    result = subprocess.run(
        [sys.executable, str(ADW_CSPEC), "--target", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "specback directory not found" in result.stderr


def test_generate_changespec_md(tmp_path: Path) -> None:
    """Verify change-spec.md generation from structured data."""
    from adws.adw_specback_changespec import _generate_changespec_md

    test_data = [
        {"file": "src/main.py", "change_type": "modified", "impact": "minor",
         "summary": "Updated function signature"},
        {"file": "src/api.py", "change_type": "added", "impact": "breaking",
         "summary": "New endpoint added"},
    ]

    out_dir = tmp_path / "output"
    out_dir.mkdir()

    md_path = _generate_changespec_md(test_data, out_dir)

    assert Path(md_path).exists()
    content = Path(md_path).read_text(encoding="utf-8")
    assert "Change Specification" in content
    assert "src/main.py" in content
    assert "src/api.py" in content
    assert "breaking" in content


def test_non_interactive_mock(tmp_path: Path) -> None:
    """Verify non-interactive mode with minimal setup runs without error."""
    sb_dir = tmp_path / ".specback"
    sb_dir.mkdir()
    (sb_dir / "goal.json").write_text('{"title": "test"}', encoding="utf-8")
    (sb_dir / "state.json").write_text('{"current_phase": "changespec"}', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable, str(ADW_CSPEC),
            "--target", str(tmp_path),
            "--non-interactive",
            "--envelope-out", str(tmp_path / "cspec-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )

    envelope_path = tmp_path / "cspec-envelope.json"
    assert envelope_path.exists(), f"Envelope not written:\n{result.stdout}\n{result.stderr}"
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert "changespec_path" in envelope
    assert "files_changed" in envelope
    assert "breaking_changes" in envelope
