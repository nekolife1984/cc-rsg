"""Tests for adws/adw_specback_verify.py — Phase 4 Verify ADW."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADW_VERIFY = ROOT / "adws" / "adw_specback_verify.py"
SCRIPT_DIR = ROOT / "scripts"


def test_imports() -> None:
    """Verify the ADW script can be imported without errors (syntax + imports)."""
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{ROOT}')
from adws.adw_specback_verify import run_verify, build_parser, main
print('  ✅ ADW verify imports OK')
"""],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"Import failed:\n{result.stderr}"


def test_help() -> None:
    """Verify --help works."""
    result = subprocess.run(
        [sys.executable, str(ADW_VERIFY), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "specback ADW" in result.stdout
    assert "--target" in result.stdout


def test_run_verify_no_specback_dir(tmp_path: Path) -> None:
    """Verify exits with error when .specback dir doesn't exist."""
    result = subprocess.run(
        [sys.executable, str(ADW_VERIFY), "--target", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "specback directory not found" in result.stderr


def test_run_verify_with_mock_env(tmp_path: Path) -> None:
    """Verify runs and produces correct output with a minimal .specback dir."""
    # Create minimal .specback and output dir
    sb_dir = tmp_path / ".specback"
    sb_dir.mkdir()
    (sb_dir / "goal.json").write_text('{"title": "test", "language": "en"}', encoding="utf-8")
    (sb_dir / "state.json").write_text(
        '{"current_phase": "verify", "output_dir": "."}', encoding="utf-8"
    )
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable, str(ADW_VERIFY),
            "--target", str(tmp_path),
            "--output-dir", str(out_dir),
            "--gates", "schema_valid",
            "--envelope-out", str(tmp_path / "verify-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )
    # This should work - schema_valid will check if schema files exist
    # and report the results
    envelope_path = tmp_path / "verify-envelope.json"
    assert envelope_path.exists(), f"Envelope not written:\n{result.stdout}\n{result.stderr}"
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert "all_gates_passed" in envelope
    assert "failures" in envelope
