"""Smoke tests for snapshot-hashes.py (hash snapshot generator)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "snapshot-hashes.py"


def test_help_includes_specback_dir():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "--specback-dir" in result.stdout


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


def test_no_units_warns_writes_empty(tmp_path):
    """Empty source-map warns that an empty hash file will be written (not silent)."""
    sb = tmp_path / "proj" / ".specback"
    sb.mkdir(parents=True)
    (sb / "source-map.json").write_text(
        json.dumps({"units": [], "target_root": "."}), encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--specback-dir", str(sb)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Nothing to hash" in result.stderr
    assert "writing an empty source-hashes.json" in result.stderr
    # the empty artifact is still written (downstream consumers can read it)
    assert (sb / "source-hashes.json").exists()
