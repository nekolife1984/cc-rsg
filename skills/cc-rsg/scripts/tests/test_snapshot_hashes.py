"""Smoke tests for snapshot-hashes.py (hash snapshot generator)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "snapshot-hashes.py"


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


def test_help_includes_output():
    """--output flag for source-hashes.json path."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--output" in result.stdout


def test_args_with_output_dir():
    """--output-dir combined with --help doesn't error."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output-dir", "/tmp/x", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
