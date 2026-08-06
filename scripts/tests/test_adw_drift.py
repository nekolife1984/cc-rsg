"""Tests for adws/adw_specback_drift.py — Phase 7 Drift ADW."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADW_DRIFT = ROOT / "adws" / "adw_specback_drift.py"


def test_imports() -> None:
    """Verify the ADW script can be imported without errors."""
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{ROOT}')
from adws.adw_specback_drift import run_drift, build_parser
print('  ✅ ADW drift imports OK')
"""],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"Import failed:\n{result.stderr}"


def test_help() -> None:
    """Verify --help works."""
    result = subprocess.run(
        [sys.executable, str(ADW_DRIFT), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "specback ADW" in result.stdout
    assert "--mode" in result.stdout


def test_no_specback_dir(tmp_path: Path) -> None:
    """Verify exits with error when .specback dir doesn't exist."""
    result = subprocess.run(
        [sys.executable, str(ADW_DRIFT), "--target", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "specback directory not found" in result.stderr


def test_run_drift_with_mock_env(tmp_path: Path) -> None:
    """Verify drift runs and produces correct output with a minimal .specback dir."""
    sb_dir = tmp_path / ".specback"
    sb_dir.mkdir()
    (sb_dir / "goal.json").write_text(
        json.dumps({"title": "test", "language": "en"}), encoding="utf-8",
    )
    (sb_dir / "state.json").write_text(
        json.dumps({"current_phase": "drift", "output_dir": "."}), encoding="utf-8",
    )

    out_dir = tmp_path / "output"
    out_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable, str(ADW_DRIFT),
            "--target", str(tmp_path),
            "--output-dir", str(out_dir),
            "--mode", "hash",
            "--skip-fix-refs",
            "--skip-config-refresh",
            "--envelope-out", str(tmp_path / "drift-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )

    envelope_path = tmp_path / "drift-envelope.json"
    assert envelope_path.exists(), f"Envelope not written:\n{result.stdout}\n{result.stderr}"
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))

    assert "affected_sections" in envelope
    assert "drift_report_path" in envelope
