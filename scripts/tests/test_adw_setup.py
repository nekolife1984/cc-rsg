"""Tests for adws/adw_specback_setup.py — Phase 0 Setup ADW."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADW_SETUP = ROOT / "adws" / "adw_specback_setup.py"


def test_imports() -> None:
    """Verify the ADW script can be imported without errors."""
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{ROOT}')
from adws.adw_specback_setup import run_setup, build_parser, GoalOutput
print('  ✅ ADW setup imports OK')
"""],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"Import failed:\n{result.stderr}"


def test_help() -> None:
    """Verify --help works."""
    result = subprocess.run(
        [sys.executable, str(ADW_SETUP), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "specback ADW" in result.stdout
    assert "--target" in result.stdout


def test_no_target(tmp_path: Path) -> None:
    """Verify exits with error when target doesn't exist."""
    result = subprocess.run(
        [sys.executable, str(ADW_SETUP), "--target", str(tmp_path / "nonexistent")],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "target directory not found" in result.stderr


def test_non_interactive(tmp_path: Path) -> None:
    """Verify non-interactive mode produces correct goal.json."""
    out_dir = tmp_path / "specs"
    result = subprocess.run(
        [
            sys.executable, str(ADW_SETUP),
            "--target", str(tmp_path),
            "--output-dir", str(out_dir),
            "--non-interactive",
            "--language", "en",
            "--envelope-out", str(tmp_path / "setup-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, f"Setup failed:\n{result.stderr}"

    # Check envelope
    envelope_path = tmp_path / "setup-envelope.json"
    assert envelope_path.exists(), f"Envelope not written:\n{result.stdout}"
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert envelope["output_language"] == "en"
    assert envelope["output_dir"] == str(out_dir)
    assert envelope["primary_reader"] == "maintenance_developer"

    # Check goal.json
    goal_path = out_dir / ".specback" / "goal.json"
    assert goal_path.exists()
    goal = json.loads(goal_path.read_text(encoding="utf-8"))
    assert goal["output_language"] == "en"

    # Check state.json
    state_path = out_dir / ".specback" / "state.json"
    assert state_path.exists()

    # Check .skill-path
    skill_path = out_dir / ".specback" / ".skill-path"
    assert skill_path.exists()
    assert skill_path.read_text(encoding="utf-8").strip() == str(ROOT)


def test_resume(tmp_path: Path) -> None:
    """Verify resume mode loads existing goal.json."""
    out_dir = tmp_path / "specs"
    specback_dir = out_dir / ".specback"
    specback_dir.mkdir(parents=True, exist_ok=True)

    # Create existing goal.json
    initial_goal = {
        "output_language": "ja",
        "output_dir": "specs",
        "primary_reader": "regulator",
        "reader_action": "audit",
        "granularity": "detailed",
    }
    (specback_dir / "goal.json").write_text(
        json.dumps(initial_goal), encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable, str(ADW_SETUP),
            "--target", str(tmp_path),
            "--output-dir", str(out_dir),
            "--resume",
            "--non-interactive",
            "--envelope-out", str(tmp_path / "setup-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, f"Resume failed:\n{result.stderr}"

    envelope_path = tmp_path / "setup-envelope.json"
    assert envelope_path.exists()
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert envelope["output_language"] == "ja"
    assert envelope["primary_reader"] == "regulator"
    assert envelope["granularity"] == "detailed"
