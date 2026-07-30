"""Tests for build-traceability.py --output-dir and --stage arguments."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "build-traceability.py"


def test_help_includes_output_dir():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--output-dir" in result.stdout


def test_help_includes_stage():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--stage" in result.stdout


def test_output_dir_and_stage_with_help_allowed():
    """--output-dir and --stage combined with --help doesn't error."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--output-dir", "/tmp/x", "--stage", "drafts", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
