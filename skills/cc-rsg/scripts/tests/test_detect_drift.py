"""Smoke tests for detect-drift.py (Phase 7 — Drift Detection)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "detect-drift.py"


def test_help_includes_cc_rsg_dir():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--cc-rsg-dir" in result.stdout


def test_help_includes_output_dir():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--output-dir" in result.stdout


def test_help_includes_mode():
    """--mode auto/git/hash appears in help."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--mode" in result.stdout
    assert "auto" in result.stdout
    assert "git" in result.stdout
    assert "hash" in result.stdout


def test_help_includes_json():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--json" in result.stdout


def test_args_with_output_dir():
    """--output-dir combined with --help doesn't error."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output-dir", "/tmp/x", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_args_with_mode_hash():
    """--mode hash combined with --help doesn't error."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", "hash", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
